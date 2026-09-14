"""
recommend.py
------------
Rule-based recommendation engine.

Maps each asset's dominant_cause to a specific, safe civil-engineering action.
Every row includes:
  - recommended_action     : what a crew should do
  - action_tier            : urgency level (immediate / scheduled / monitor)
  - expected_risk_reduction_pct
  - recommended_crew_type  : who should attend
  - risk_band              : critical / elevated / watch / normal
  - safety_note            : ALWAYS present — advisory only, never authorises live work

SAFETY CONSTRAINT (hard-coded, cannot be bypassed by the UI):
  No recommendation ever authorises opening breakers, energising or
  de-energising lines, excavation, or work on live equipment.
  All field actions require sign-off by a qualified licensed engineer.

Output: data/final_report.csv
"""

import os
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SRC_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SRC_DIR, "data")

# ---------------------------------------------------------------------------
# Safety footer — appended to EVERY recommendation row
# ---------------------------------------------------------------------------
SAFETY_NOTE = (
    "ADVISORY ONLY — This system does not authorise any field work. "
    "No switching, breaker operation, energisation, de-energisation, "
    "excavation, or work on or near live equipment is permitted without "
    "a written work order reviewed and signed off by a qualified licensed "
    "engineer in accordance with applicable utility safety procedures."
)

# ---------------------------------------------------------------------------
# Risk band thresholds
# ---------------------------------------------------------------------------
RISK_BANDS = [
    (70, "critical"),
    (45, "elevated"),
    (20, "watch"),
    (0,  "normal"),
]

def _risk_band(risk_score: float) -> str:
    for threshold, label in RISK_BANDS:
        if risk_score >= threshold:
            return label
    return "normal"


# ---------------------------------------------------------------------------
# Action table — ordered rules, first match wins
# ---------------------------------------------------------------------------
#
# Each entry is a dict:
#   cause         : dominant_cause value to match
#   action_tier   : "immediate" | "scheduled" | "monitor"
#   action        : advisory text (no live-work instructions)
#   risk_reduction: expected % risk reduction after action
#   crew          : recommended crew type
#
ACTION_TABLE = [
    {
        "cause":         "wind_foundation",
        "action_tier":   "immediate",
        "action": (
            "Conduct urgent visual inspection of foundation integrity and structural tilt. "
            "Arrange engineer-verified bracing assessment; if tilt exceeds safe tolerance, "
            "prepare replacement materials and stage crew for post-storm intervention. "
            "Do NOT approach or touch the structure during active high-wind conditions."
        ),
        "risk_reduction": 55,
        "crew": "Structural/civil engineer + two-person utility crew",
    },
    {
        "cause":         "flood_drainage",
        "action_tier":   "scheduled",
        "action": (
            "Inspect and clear all blocked drainage channels within 10 m of the asset. "
            "Check for evidence of scour or foundation undermining; photograph and report. "
            "Apply temporary erosion-control measures (sandbags, geotextile) if scour "
            "is observed. Stage dewatering equipment if significant flooding is forecast. "
            "Defer foundation stabilisation work until water has receded and site is safe."
        ),
        "risk_reduction": 48,
        "crew": "Civil/drainage engineer + maintenance crew",
    },
    {
        "cause":         "vegetation",
        "action_tier":   "scheduled",
        "action": (
            "Arrange targeted vegetation trimming to restore safe conductor clearance. "
            "Inspect conductor for signs of abrasion or tracking damage after trimming. "
            "Log encroaching tree species and height for future vegetation-management schedule. "
            "Trimming must be carried out by a qualified arborist with utility line clearance "
            "training; no cutting within minimum approach distance without engineer approval."
        ),
        "risk_reduction": 60,
        "crew": "Qualified arborist with utility clearance certification",
    },
    {
        "cause":         "corrosion_age",
        "action_tier":   "immediate",
        "action": (
            "Escalate to engineering team for detailed condition assessment. "
            "Review maintenance history and compare against asset life expectancy. "
            "Prepare a like-for-like replacement proposal and cost estimate. "
            "Stage materials and arrange crew availability before next forecast severe-weather "
            "event. Do not defer beyond current inspection cycle given combined corrosion "
            "and age indicators."
        ),
        "risk_reduction": 70,
        "crew": "Asset management engineer + specialist replacement crew",
    },
    {
        "cause":         "thermal_overload",
        "action_tier":   "immediate",
        "action": (
            "ADVISORY: Transformer/substation thermal anomaly detected via sensor fusion. "
            "Dispatch qualified electrical protection engineer to investigate. "
            "Review SCADA load data and verify cooling system operation; check fans, "
            "oil circulation, and radiator fins for blockage. "
            "If loading ratio exceeds rated capacity, coordinate with control room to "
            "arrange load transfer under engineer direction — DO NOT operate switching "
            "equipment without a written switching plan and authorised engineer present. "
            "Log all temperature readings and alert asset management team immediately."
        ),
        "risk_reduction": 65,
        "crew": "Electrical protection engineer + SCADA-qualified technician",
    },
    {
        "cause":         "insulation_degradation",
        "action_tier":   "immediate",
        "action": (
            "ADVISORY: Elevated partial-discharge count and/or oil quality degradation "
            "detected — indicative of insulation system stress. "
            "Arrange urgent oil sampling and DGA (dissolved gas analysis) by a qualified "
            "high-voltage engineer before next scheduled maintenance window. "
            "Initiate condition-based maintenance review; if DGA confirms thermal fault "
            "or arcing gases, escalate to emergency replacement planning. "
            "No live work on insulation systems is permitted without full isolation, "
            "earthing, and sign-off by a qualified licensed engineer."
        ),
        "risk_reduction": 72,
        "crew": "HV-qualified engineer + oil sampling specialist",
    },
]

# Default fallback if dominant_cause is unrecognised
DEFAULT_ACTION = {
    "action_tier":   "monitor",
    "action": (
        "Schedule routine inspection; review all available condition data and "
        "update asset record. Consult engineering team if any deterioration is observed."
    ),
    "risk_reduction": 20,
    "crew": "Maintenance crew",
}


def _lookup_action(dominant_cause: str) -> dict:
    for entry in ACTION_TABLE:
        if entry["cause"] == dominant_cause:
            return entry
    return {"cause": dominant_cause, **DEFAULT_ACTION}


# ---------------------------------------------------------------------------
# Per-row recommendation builder
# ---------------------------------------------------------------------------

def build_recommendation(row) -> dict:
    cause  = str(row.get("dominant_cause", "")).strip().lower()
    action = _lookup_action(cause)
    band   = _risk_band(float(row.get("risk_score", 0)))
    return {
        "recommended_action":           action["action"],
        "action_tier":                  action["action_tier"],
        "expected_risk_reduction_pct":  action["risk_reduction"],
        "recommended_crew_type":        action["crew"],
        "risk_band":                    band,
        "safety_note":                  SAFETY_NOTE,
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run():
    print("recommend — Loading priority_report.csv …")
    prio_path = os.path.join(DATA_DIR, "priority_report.csv")
    df = pd.read_csv(prio_path)

    rec_rows = [build_recommendation(row) for _, row in df.iterrows()]
    rec_df   = pd.DataFrame(rec_rows)
    result   = pd.concat([df.reset_index(drop=True), rec_df], axis=1)

    out_path = os.path.join(DATA_DIR, "final_report.csv")
    result.to_csv(out_path, index=False)
    print(f"  Written: {out_path}  ({len(result)} rows)")

    print("\n  Risk band distribution:")
    print(result["risk_band"].value_counts().to_string())
    print("\n  Action tier distribution:")
    print(result["action_tier"].value_counts().to_string())
    print("\nrecommend complete.")
    return result


if __name__ == "__main__":
    run()
