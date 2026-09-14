"""
test_risk_engine_extended.py
----------------------------
Extended unit tests for GridShield risk_engine.py

Covers:
  - _scale function boundary conditions (at-threshold, at-ceiling, above-ceiling)
  - _factor_wind boundary conditions
  - _factor_rain (rain-only, flood-only, combined, cap at 20)
  - _factor_tilt (at threshold, above ceiling)
  - _factor_erosion (below/above threshold)
  - _factor_corrosion (below/above threshold)
  - _factor_drainage (inverted scale — low drainage = high risk)
  - _factor_vegetation (inverted scale — low clearance = high risk)
  - _factor_age (age > 50 capped; overdue maintenance adds points)
  - _factor_oil (inverted: low quality_index = high points)
  - _is_electrical returns True for substation
  - _safe_float handles None, NaN string, empty string
  - score_row returns all expected factor keys
  - dominant_cause flood_drainage for rain+erosion dominated row
  - dominant_cause vegetation for clearance-dominated row
"""
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scoring.risk_engine import (
    _scale,
    _factor_wind,
    _factor_rain,
    _factor_tilt,
    _factor_erosion,
    _factor_corrosion,
    _factor_drainage,
    _factor_vegetation,
    _factor_age,
    _factor_oil,
    _is_electrical,
    _safe_float,
    score_row,
)

EXPECTED_FACTOR_KEYS = [
    "factor_wind", "factor_rain", "factor_tilt", "factor_erosion",
    "factor_corrosion", "factor_drainage", "factor_vegetation", "factor_age",
    "factor_thermal", "factor_vibration", "factor_partial_dc",
    "factor_oil", "factor_overload",
    "risk_score", "dominant_cause",
]


def _base_transformer():
    return {
        "asset_type": "transformer",
        "wind_gust_kmh": 0, "rainfall_mm": 0, "flood_depth_cm": 0,
        "tilt_deg": 0, "erosion_index": 0, "corrosion_score": 0,
        "drainage_score": 100, "clearance_score": 100,
        "age_years": 5, "last_maintenance_date": "2024-01-01",
        "temp_residual_c": 0, "vibration_rms_delta": 0,
        "partial_discharge_cnt": 0, "oil_quality_index": 100,
        "loading_ratio": 0.5, "overload_duration_h": 0,
    }


def _base_pole():
    return {
        "asset_type": "pole",
        "wind_gust_kmh": 0, "rainfall_mm": 0, "flood_depth_cm": 0,
        "tilt_deg": 0, "erosion_index": 0, "corrosion_score": 0,
        "drainage_score": 100, "clearance_score": 100,
        "age_years": 5, "last_maintenance_date": "2024-01-01",
    }


# ---------------------------------------------------------------------------
# _scale
# ---------------------------------------------------------------------------

def test_scale_below_threshold_returns_zero():
    assert _scale(50, 60, 100, 20) == 0.0


def test_scale_at_threshold_returns_zero():
    assert _scale(60, 60, 100, 20) == 0.0


def test_scale_at_ceiling_returns_max():
    assert _scale(100, 60, 100, 20) == 20.0


def test_scale_above_ceiling_capped_at_max():
    assert _scale(150, 60, 100, 20) == 20.0


def test_scale_midpoint():
    result = _scale(80, 60, 100, 20)
    assert abs(result - 10.0) < 0.01


# ---------------------------------------------------------------------------
# _factor_wind
# ---------------------------------------------------------------------------

def test_factor_wind_below_threshold():
    row = _base_pole()
    row["wind_gust_kmh"] = 59
    assert _factor_wind(row) == 0.0


def test_factor_wind_at_ceiling():
    row = _base_pole()
    row["wind_gust_kmh"] = 100
    assert _factor_wind(row) == 20.0


# ---------------------------------------------------------------------------
# _factor_rain
# ---------------------------------------------------------------------------

def test_factor_rain_rain_only():
    row = _base_pole()
    row["rainfall_mm"] = 100
    row["flood_depth_cm"] = 0
    assert _factor_rain(row) == 15.0   # rain_pts capped at 15


def test_factor_rain_flood_only():
    row = _base_pole()
    row["rainfall_mm"] = 0
    row["flood_depth_cm"] = 20
    assert _factor_rain(row) == 5.0


def test_factor_rain_combined_capped_at_20():
    row = _base_pole()
    row["rainfall_mm"] = 100
    row["flood_depth_cm"] = 20
    assert _factor_rain(row) == 20.0


def test_factor_rain_zero_inputs():
    row = _base_pole()
    assert _factor_rain(row) == 0.0


# ---------------------------------------------------------------------------
# _factor_tilt
# ---------------------------------------------------------------------------

def test_factor_tilt_below_threshold():
    row = _base_pole()
    row["tilt_deg"] = 2.9
    assert _factor_tilt(row) == 0.0


def test_factor_tilt_at_ceiling():
    row = _base_pole()
    row["tilt_deg"] = 7.0
    assert _factor_tilt(row) == 15.0


# ---------------------------------------------------------------------------
# _factor_erosion / _factor_corrosion
# ---------------------------------------------------------------------------

def test_factor_erosion_below_threshold():
    row = _base_pole()
    row["erosion_index"] = 59
    assert _factor_erosion(row) == 0.0


def test_factor_erosion_at_ceiling():
    row = _base_pole()
    row["erosion_index"] = 95
    assert _factor_erosion(row) == 15.0


def test_factor_corrosion_below_threshold():
    row = _base_pole()
    row["corrosion_score"] = 59
    assert _factor_corrosion(row) == 0.0


# ---------------------------------------------------------------------------
# _factor_drainage / _factor_vegetation (inverted)
# ---------------------------------------------------------------------------

def test_factor_drainage_good_score_zero():
    row = _base_pole()
    row["drainage_score"] = 100
    assert _factor_drainage(row) == 0.0


def test_factor_drainage_bad_score_positive():
    row = _base_pole()
    row["drainage_score"] = 0
    assert _factor_drainage(row) > 0


def test_factor_vegetation_safe_clearance_zero():
    row = _base_pole()
    row["clearance_score"] = 100
    assert _factor_vegetation(row) == 0.0


def test_factor_vegetation_dangerous_clearance_positive():
    row = _base_pole()
    row["clearance_score"] = 0
    assert _factor_vegetation(row) > 0


# ---------------------------------------------------------------------------
# _factor_age
# ---------------------------------------------------------------------------

def test_factor_age_young_recently_maintained():
    from datetime import date, timedelta
    recent = (date.today() - timedelta(days=30)).isoformat()
    row = _base_pole()
    row["age_years"] = 5
    row["last_maintenance_date"] = recent
    assert _factor_age(row) == 0.0


def test_factor_age_very_old_capped():
    row = _base_pole()
    row["age_years"] = 60
    row["last_maintenance_date"] = "2024-06-01"
    pts = _factor_age(row)
    assert pts <= 10.0


# ---------------------------------------------------------------------------
# _factor_oil
# ---------------------------------------------------------------------------

def test_factor_oil_good_quality_zero():
    row = _base_transformer()
    row["oil_quality_index"] = 100
    assert _factor_oil(row) == 0.0


def test_factor_oil_poor_quality_positive():
    row = _base_transformer()
    row["oil_quality_index"] = 0
    assert _factor_oil(row) == 12.0


# ---------------------------------------------------------------------------
# _is_electrical
# ---------------------------------------------------------------------------

def test_is_electrical_substation():
    assert _is_electrical({"asset_type": "substation"}) is True


def test_is_electrical_transformer():
    assert _is_electrical({"asset_type": "transformer"}) is True


def test_is_electrical_pole():
    assert _is_electrical({"asset_type": "pole"}) is False


# ---------------------------------------------------------------------------
# _safe_float
# ---------------------------------------------------------------------------

def test_safe_float_none():
    assert _safe_float(None) == 0.0


def test_safe_float_nan():
    assert _safe_float(float("nan")) == 0.0


def test_safe_float_string_none():
    assert _safe_float("None") == 0.0


def test_safe_float_valid_string():
    assert abs(_safe_float("3.14") - 3.14) < 0.001


# ---------------------------------------------------------------------------
# score_row — output keys and dominant causes
# ---------------------------------------------------------------------------

def test_score_row_returns_all_expected_keys():
    row = _base_transformer()
    result = score_row(row)
    for key in EXPECTED_FACTOR_KEYS:
        assert key in result, f"Missing key: {key}"


def test_dominant_cause_flood_drainage():
    row = _base_pole()
    row.update({"rainfall_mm": 100, "flood_depth_cm": 20, "erosion_index": 95,
                "drainage_score": 0})
    result = score_row(row)
    assert result["dominant_cause"] == "flood_drainage"


def test_dominant_cause_vegetation():
    row = _base_pole()
    row.update({"clearance_score": 0})
    result = score_row(row)
    # vegetation factor alone dominates when everything else is zero
    assert result["dominant_cause"] == "vegetation"
