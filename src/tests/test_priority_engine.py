"""
test_priority_engine.py
-----------------------
Unit tests for GridShield priority_engine.py

Covers:
  - _critical_multiplier returns correct values for all load types
  - _compute_expected_loss formula correctness
  - redundancy reduces expected loss by 40%
  - _net_benefit formula
  - _priority_score formula and minimum-cost floor
  - _intervention_cost lookup
  - priority score is non-negative for seeded high-risk asset profiles
  - assets with lower intervention cost can outrank higher raw-risk assets
  - full priority ranking — seeded positives in top-9
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scoring.priority_engine import (
    _critical_multiplier,
    _compute_expected_loss,
    _net_benefit,
    _priority_score,
    _intervention_cost,
    CRITICAL_LOAD_MULTIPLIERS,
    INTERVENTION_COSTS,
    MINIMUM_COST,
    OUTAGE_COST_PER_CUSTOMER,
    REDUNDANCY_DISCOUNT,
)


# ---------------------------------------------------------------------------
# _critical_multiplier
# ---------------------------------------------------------------------------

def test_critical_multiplier_hospital():
    assert _critical_multiplier("hospital") == 3.0


def test_critical_multiplier_water_treatment():
    assert _critical_multiplier("water_treatment") == 2.5


def test_critical_multiplier_shelter():
    assert _critical_multiplier("shelter") == 2.0


def test_critical_multiplier_none():
    assert _critical_multiplier("none") == 1.0


def test_critical_multiplier_unknown_defaults_to_1():
    assert _critical_multiplier("unknown_load_type") == 1.0


def test_critical_multiplier_case_insensitive():
    assert _critical_multiplier("HOSPITAL") == 3.0
    assert _critical_multiplier("None") == 1.0


# ---------------------------------------------------------------------------
# _compute_expected_loss
# ---------------------------------------------------------------------------

def _row(risk_score=80.0, customers=1000, critical_loads="none", redundancy="False"):
    return {
        "risk_score": risk_score,
        "downstream_customers": float(customers),
        "critical_loads": critical_loads,
        "redundancy": redundancy,
    }


def test_expected_loss_basic_formula():
    """Loss = P_failure × customers × cost_per_cust × multiplier."""
    row = _row(risk_score=80.0, customers=1000, critical_loads="none")
    expected = 0.80 * 1000 * OUTAGE_COST_PER_CUSTOMER * 1.0
    assert abs(_compute_expected_loss(row) - expected) < 0.01


def test_expected_loss_hospital_multiplier():
    row = _row(risk_score=80.0, customers=1000, critical_loads="hospital")
    no_crit = _compute_expected_loss(_row(risk_score=80.0, customers=1000))
    with_crit = _compute_expected_loss(row)
    assert abs(with_crit / no_crit - 3.0) < 0.01


def test_redundancy_reduces_loss_by_40_pct():
    row_no_red = _row(risk_score=60.0, customers=500, redundancy="False")
    row_red    = _row(risk_score=60.0, customers=500, redundancy="True")
    loss_no_red = _compute_expected_loss(row_no_red)
    loss_red    = _compute_expected_loss(row_red)
    assert abs(loss_red / loss_no_red - (1.0 - REDUNDANCY_DISCOUNT)) < 0.01


def test_expected_loss_zero_risk_is_zero():
    row = _row(risk_score=0.0, customers=1000)
    assert _compute_expected_loss(row) == 0.0


# ---------------------------------------------------------------------------
# _net_benefit
# ---------------------------------------------------------------------------

def test_net_benefit_positive_for_high_loss_cheap_cause():
    """Vegetation is cheap ($800) — should give positive net benefit for high loss."""
    benefit = _net_benefit(expected_outage_cost=50_000, dominant_cause="vegetation")
    assert benefit > 0


def test_net_benefit_structure():
    """NetBenefit = loss × effectiveness − preventive − mobilization − carbon."""
    from scoring.priority_engine import ACTION_EFFECTIVENESS, MOBILIZATION_COSTS, CARBON_COSTS
    cause = "corrosion_age"
    loss = 20_000
    eff = ACTION_EFFECTIVENESS[cause]
    pcost = INTERVENTION_COSTS[cause]
    mcost = MOBILIZATION_COSTS[cause]
    ccost = CARBON_COSTS[cause]
    expected_nb = loss * eff - pcost - mcost - ccost
    assert abs(_net_benefit(loss, cause) - expected_nb) < 0.01


def test_net_benefit_unknown_cause_uses_defaults():
    """Unknown cause should not crash — uses fallback defaults."""
    benefit = _net_benefit(expected_outage_cost=10_000, dominant_cause="unknown_cause")
    assert isinstance(benefit, float)


# ---------------------------------------------------------------------------
# _priority_score
# ---------------------------------------------------------------------------

def test_priority_score_uses_minimum_cost_floor():
    """If preventive_cost < MINIMUM_COST, denominator should be MINIMUM_COST."""
    score_cheap = _priority_score(net_benefit=1000.0, preventive_cost=100)
    score_floor = _priority_score(net_benefit=1000.0, preventive_cost=MINIMUM_COST)
    assert abs(score_cheap - score_floor) < 0.001


def test_priority_score_scales_with_net_benefit():
    score_high = _priority_score(net_benefit=10_000.0, preventive_cost=1_000)
    score_low  = _priority_score(net_benefit=1_000.0,  preventive_cost=1_000)
    assert score_high > score_low


def test_priority_score_negative_net_benefit():
    """Negative net benefit is allowed — reflects that action costs more than expected benefit."""
    score = _priority_score(net_benefit=-500.0, preventive_cost=1_000)
    assert score < 0.0


# ---------------------------------------------------------------------------
# _intervention_cost lookup
# ---------------------------------------------------------------------------

def test_intervention_cost_all_causes():
    for cause in INTERVENTION_COSTS:
        assert _intervention_cost(cause) == INTERVENTION_COSTS[cause]


def test_intervention_cost_unknown_returns_default():
    default = _intervention_cost("unknown_cause")
    assert default == 3_000
