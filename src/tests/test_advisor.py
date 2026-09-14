"""
test_advisor.py
---------------
Tests for advisor.py comparison logic, refusal gate, and grounding footer.
"""
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ai.advisor import answer_question, _compare_assets, _is_control_request


def _make_df():
    """Minimal final_report-style DataFrame with two distinct assets."""
    return pd.DataFrame([
        {
            "asset_id": "A-01",
            "asset_type": "transformer",
            "risk_score": 90.0,
            "priority_score": 3.5,
            "expected_loss": 4200.0,
            "estimated_intervention_cost": 1200,
            "dominant_cause": "flood_drainage",
            "critical_loads": "hospital",
            "downstream_customers": 1500,
            "redundancy": False,
            "risk_band": "critical",
            "action_tier": "immediate",
            "recommended_action": "Inspect drainage channels and clear blockages.",
            "recommended_crew_type": "Civil engineer",
            "expected_risk_reduction_pct": 48,
            "safety_note": "Advisory only.",
        },
        {
            "asset_id": "A-15",
            "asset_type": "pole",
            "risk_score": 55.0,
            "priority_score": 0.9,
            "expected_loss": 900.0,
            "estimated_intervention_cost": 1000,
            "dominant_cause": "corrosion_age",
            "critical_loads": "none",
            "downstream_customers": 200,
            "redundancy": False,
            "risk_band": "elevated",
            "action_tier": "scheduled",
            "recommended_action": "Escalate to engineering team for assessment.",
            "recommended_crew_type": "Asset engineer",
            "expected_risk_reduction_pct": 70,
            "safety_note": "Advisory only.",
        },
    ])


def test_comparison_contains_both_asset_ids():
    df = _make_df()
    answer = answer_question("Why is A-01 ranked above A-15?", df)
    assert "A-01" in answer
    assert "A-15" in answer


def test_comparison_text_is_not_identical_for_two_assets():
    df = _make_df()
    answer_compare = answer_question("Compare A-01 and A-15", df)
    answer_a01 = answer_question("Tell me about A-01", df)
    answer_a15 = answer_question("Tell me about A-15", df)
    # Compare answer must differ from individual summaries
    assert answer_compare != answer_a01
    assert answer_compare != answer_a15


def test_comparison_contains_score_difference():
    df = _make_df()
    answer = answer_question("Compare A-01 and A-15", df)
    # Delta value (3.5 - 0.9 = 2.6) should appear in the text as score values
    assert "3.5" in answer or "0.9" in answer or "2.6" in answer or "delta" in answer.lower()


def test_comparison_contrast_sentence_before_individual_text():
    df = _make_df()
    answer = answer_question("Why is A-01 ranked above A-15?", df)
    # The contrast sentence must appear before the detailed recommendation
    # "ranks above" should appear before the word "Recommended"
    idx_ranks = answer.lower().find("ranks above")
    idx_action = answer.lower().find("next action")
    assert idx_ranks != -1, "Missing 'ranks above' contrast sentence"
    assert idx_action == -1 or idx_ranks < idx_action, \
        "Contrast sentence should appear before action text"


def test_energize_feeder_refused():
    df = _make_df()
    answer = answer_question("Energize feeder F-100 now", df)
    assert "cannot be actioned" in answer.lower() or "advisory system" in answer.lower()


def test_answer_contains_grounding_footer():
    df = _make_df()
    answer = answer_question("Tell me about A-01", df)
    assert "grounded in" in answer.lower()
    assert "final_report.csv" in answer.lower()
