"""
priority_engine.py
------------------
Converts raw risk scores into a cost-aware priority queue.

Key innovation: a high-risk asset that is expensive to fix may rank BELOW
a moderate-risk asset that is cheap to fix and serves more customers.

Corrected Formulas (ITEM 10)
-----------------------------
  P_failure            = risk_score / 100
  OutageCostPerCust    = 50  (illustrative USD per customer-hour)
  critical_load_multiplier : hospital=3.0 | water_treatment=2.5 | shelter=2.0 | none=1.0
  ExpectedOutageCost   = P_failure × downstream_customers × OutageCostPerCust
                         × critical_load_multiplier   ← criticality folded here ONCE
  redundancy adjustment: ExpectedOutageCost *= 0.60  (40% reduction if feeder has redundancy)
  ActionEffectiveness  = per dominant_cause, bounded [0,1]
  NetBenefit           = ExpectedOutageCost × ActionEffectiveness
                         − PreventiveCost − MobilizationCost − CarbonCost
  MinimumCost          = 500  (floor to avoid division by zero / trivial tasks)
  Priority             = NetBenefit / max(PreventiveCost, MinimumCost)

Changes vs previous version
----------------------------
  • Criticality multiplier applied ONLY in ExpectedOutageCost (never again in priority ratio)
  • ActionEffectiveness (0–1) now scales benefit
  • MobilizationCost and CarbonCost are explicit named constants (auditable)
  • Priority denominator is max(PreventiveCost, MinimumCost) — avoids zero-cost inflation

Output: data/priority_report.csv  (sorted by priority_score descending)
"""

import os
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SRC_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SRC_DIR, "data")

# ---------------------------------------------------------------------------
# Constants — auditable by non-engineers
# ---------------------------------------------------------------------------

CRITICAL_LOAD_MULTIPLIERS = {
    "hospital":        3.0,
    "water_treatment": 2.5,
    "shelter":         2.0,
    "none":            1.0,
}

OUTAGE_COST_PER_CUSTOMER = 50  # illustrative USD per customer affected

# Illustrative preventive intervention (labour + materials) costs in USD
INTERVENTION_COSTS = {
    "vegetation":             800,
    "flood_drainage":         1_200,
    "wind_foundation":        4_500,
    "corrosion_age":          6_000,
    "thermal_overload":       8_500,    # emergency transformer intervention
    "insulation_degradation": 10_000,   # insulation replacement / winding overhaul
}

# Mobilisation costs (travel, logistics, crew standby) per dominant_cause
MOBILIZATION_COSTS = {
    "vegetation":             150,
    "flood_drainage":         250,
    "wind_foundation":        400,
    "corrosion_age":          500,
    "thermal_overload":       600,
    "insulation_degradation": 700,
}

# Carbon cost (illustrative tonne CO2-equiv × $50/t carbon price)
CARBON_COSTS = {
    "vegetation":             20,
    "flood_drainage":         40,
    "wind_foundation":        80,
    "corrosion_age":          100,
    "thermal_overload":       120,
    "insulation_degradation": 140,
}

# ActionEffectiveness: fraction of expected outage cost avoided by the intervention
# Bounded [0, 1]. Must NOT be multiplied by criticality again.
ACTION_EFFECTIVENESS = {
    "vegetation":             0.60,
    "flood_drainage":         0.48,
    "wind_foundation":        0.55,
    "corrosion_age":          0.70,
    "thermal_overload":       0.65,
    "insulation_degradation": 0.72,
}

REDUNDANCY_DISCOUNT = 0.40   # 40% expected_outage_cost reduction if feeder has redundancy
MINIMUM_COST        = 500    # floor denominator to prevent trivial-cost inflation


# ---------------------------------------------------------------------------
# Per-row calculators
# ---------------------------------------------------------------------------

def _critical_multiplier(critical_loads_value: str) -> float:
    val = str(critical_loads_value).strip().lower()
    return CRITICAL_LOAD_MULTIPLIERS.get(val, 1.0)


def _compute_expected_loss(row) -> float:
    """
    ExpectedOutageCost = P_failure × customers × outage_cost_per_customer × criticality_mult
    Criticality is folded in HERE and nowhere else.
    """
    p_failure = float(row["risk_score"]) / 100.0
    customers = float(row["downstream_customers"])
    mult      = _critical_multiplier(row["critical_loads"])
    loss      = p_failure * customers * OUTAGE_COST_PER_CUSTOMER * mult
    # Reduce if the feeder has a redundant path
    redundancy = str(row.get("redundancy", "False")).strip().lower()
    if redundancy in ("true", "1", "yes"):
        loss *= (1.0 - REDUNDANCY_DISCOUNT)
    return round(loss, 2)


def _net_benefit(expected_outage_cost: float, dominant_cause: str) -> float:
    """
    NetBenefit = ExpectedOutageCost × ActionEffectiveness
                 − PreventiveCost − MobilizationCost − CarbonCost
    """
    cause       = str(dominant_cause).strip().lower()
    effectiveness = ACTION_EFFECTIVENESS.get(cause, 0.50)  # default 50%
    effectiveness = max(0.0, min(1.0, effectiveness))       # enforce [0, 1]

    preventive_cost   = INTERVENTION_COSTS.get(cause, 3_000)
    mobilization_cost = MOBILIZATION_COSTS.get(cause, 300)
    carbon_cost       = CARBON_COSTS.get(cause, 60)

    benefit = (
        expected_outage_cost * effectiveness
        - preventive_cost
        - mobilization_cost
        - carbon_cost
    )
    return round(benefit, 2)


def _intervention_cost(dominant_cause: str) -> int:
    return INTERVENTION_COSTS.get(str(dominant_cause).strip().lower(), 3_000)


def _priority_score(net_benefit: float, preventive_cost: int) -> float:
    """
    Priority = NetBenefit / max(PreventiveCost, MinimumCost)
    """
    denom = max(float(preventive_cost), float(MINIMUM_COST))
    return round(net_benefit / denom, 6)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run():
    print("priority_engine — Loading risk_report.csv …")
    risk_path = os.path.join(DATA_DIR, "risk_report.csv")
    df = pd.read_csv(risk_path)

    df["critical_load_multiplier"]    = df["critical_loads"].apply(_critical_multiplier)
    df["expected_loss"]               = df.apply(_compute_expected_loss, axis=1)
    df["estimated_intervention_cost"] = df["dominant_cause"].apply(_intervention_cost)
    df["net_benefit"]                 = df.apply(
        lambda r: _net_benefit(r["expected_loss"], r["dominant_cause"]), axis=1
    )
    df["priority_score"]              = df.apply(
        lambda r: _priority_score(r["net_benefit"], r["estimated_intervention_cost"]),
        axis=1,
    )

    df_sorted = df.sort_values("priority_score", ascending=False).reset_index(drop=True)

    out_path = os.path.join(DATA_DIR, "priority_report.csv")
    df_sorted.to_csv(out_path, index=False)
    print(f"  Written: {out_path}  ({len(df_sorted)} rows)")

    # -----------------------------------------------------------------------
    # Demonstrate re-ranking: show risk_score rank vs priority_score rank
    # -----------------------------------------------------------------------
    df_risk_rank     = df.sort_values("risk_score",    ascending=False).reset_index(drop=True)
    df_priority_rank = df_sorted.copy()

    risk_ranks     = {row["asset_id"]: i + 1 for i, row in df_risk_rank.iterrows()}
    priority_ranks = {row["asset_id"]: i + 1 for i, row in df_priority_rank.iterrows()}

    reranked = [
        (aid, risk_ranks[aid], priority_ranks[aid], priority_ranks[aid] - risk_ranks[aid])
        for aid in risk_ranks
        if abs(priority_ranks[aid] - risk_ranks[aid]) >= 3
    ]
    reranked.sort(key=lambda x: abs(x[3]), reverse=True)

    print("\n  Top priority_score ranking:")
    print(df_priority_rank[["asset_id", "risk_score", "priority_score",
                              "expected_loss", "net_benefit",
                              "estimated_intervention_cost",
                              "dominant_cause"]].head(10).to_string(index=False))

    if reranked:
        print(f"\n  Assets re-ranked >=3 positions vs pure risk_score:")
        for aid, rr, pr, delta in reranked[:5]:
            sign = "^" if delta < 0 else "v"
            print(f"    {aid}: risk_rank={rr}  priority_rank={pr}  ({sign}{abs(delta)})")
    else:
        print("\n  (No assets moved >=3 positions -- distribution may be narrow)")

    print("\npriority_engine complete.")
    return df_sorted


if __name__ == "__main__":
    run()
