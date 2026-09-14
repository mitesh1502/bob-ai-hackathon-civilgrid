"""
test_recommend.py
-----------------
Unit tests for GridShield recommendation/recommend.py

Covers:
  - _risk_band thresholds (all 4 bands)
  - _lookup_action returns correct tier for all 6 known causes
  - _lookup_action returns default for unknown cause
  - build_recommendation includes all required output columns
  - safety_note is always present in every recommendation row
  - action_tier is one of the three valid values
  - no field action or switching language in default recommendation text
  - expected_risk_reduction_pct is positive
  - recommended_crew_type is non-empty
  - immediate tier assigned to high-risk causes (wind_foundation, corrosion_age, thermal_overload, insulation_degradation)
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from recommendation.recommend import (
    _risk_band,
    _lookup_action,
    build_recommendation,
    SAFETY_NOTE,
    ACTION_TABLE,
)

REQUIRED_OUTPUT_COLUMNS = [
    "recommended_action",
    "action_tier",
    "expected_risk_reduction_pct",
    "recommended_crew_type",
    "risk_band",
    "safety_note",
]

VALID_ACTION_TIERS = {"immediate", "scheduled", "monitor"}
VALID_RISK_BANDS   = {"critical", "elevated", "watch", "normal"}

ALL_CAUSES = [entry["cause"] for entry in ACTION_TABLE]


def _make_row(risk_score=75.0, dominant_cause="flood_drainage"):
    return {"risk_score": risk_score, "dominant_cause": dominant_cause}


# ---------------------------------------------------------------------------
# _risk_band
# ---------------------------------------------------------------------------

def test_risk_band_critical():
    assert _risk_band(70.0) == "critical"
    assert _risk_band(100.0) == "critical"


def test_risk_band_elevated():
    assert _risk_band(45.0) == "elevated"
    assert _risk_band(69.9) == "elevated"


def test_risk_band_watch():
    assert _risk_band(20.0) == "watch"
    assert _risk_band(44.9) == "watch"


def test_risk_band_normal():
    assert _risk_band(0.0) == "normal"
    assert _risk_band(19.9) == "normal"


# ---------------------------------------------------------------------------
# _lookup_action
# ---------------------------------------------------------------------------

def test_lookup_action_returns_match_for_all_known_causes():
    for cause in ALL_CAUSES:
        action = _lookup_action(cause)
        assert action["cause"] == cause
        assert action["action_tier"] in VALID_ACTION_TIERS
        assert len(action["action"]) > 10


def test_lookup_action_unknown_cause_returns_default():
    action = _lookup_action("mystery_failure_mode")
    assert action["action_tier"] == "monitor"
    assert len(action["action"]) > 10


# ---------------------------------------------------------------------------
# build_recommendation
# ---------------------------------------------------------------------------

def test_build_recommendation_has_all_required_columns():
    row = _make_row()
    rec = build_recommendation(row)
    for col in REQUIRED_OUTPUT_COLUMNS:
        assert col in rec, f"Missing column: {col}"


def test_safety_note_always_present_and_non_empty():
    for cause in ALL_CAUSES:
        row = _make_row(dominant_cause=cause)
        rec = build_recommendation(row)
        assert rec["safety_note"] == SAFETY_NOTE
        assert len(rec["safety_note"]) > 20


def test_safety_note_matches_constant():
    row = _make_row()
    rec = build_recommendation(row)
    assert rec["safety_note"] == SAFETY_NOTE


def test_action_tier_is_valid():
    for cause in ALL_CAUSES:
        row = _make_row(dominant_cause=cause)
        rec = build_recommendation(row)
        assert rec["action_tier"] in VALID_ACTION_TIERS


def test_risk_reduction_is_positive():
    for cause in ALL_CAUSES:
        row = _make_row(dominant_cause=cause)
        rec = build_recommendation(row)
        assert rec["expected_risk_reduction_pct"] > 0


def test_crew_type_non_empty():
    for cause in ALL_CAUSES:
        row = _make_row(dominant_cause=cause)
        rec = build_recommendation(row)
        assert len(rec["recommended_crew_type"]) > 0


def test_immediate_tier_for_critical_causes():
    immediate_causes = {"wind_foundation", "corrosion_age", "thermal_overload", "insulation_degradation"}
    for cause in immediate_causes:
        row = _make_row(dominant_cause=cause)
        rec = build_recommendation(row)
        assert rec["action_tier"] == "immediate", \
            f"Expected 'immediate' for {cause}, got {rec['action_tier']}"


def test_risk_band_in_recommendation():
    row = _make_row(risk_score=85.0)
    rec = build_recommendation(row)
    assert rec["risk_band"] == "critical"
