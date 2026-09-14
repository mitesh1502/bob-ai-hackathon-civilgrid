"""
test_risk_engine.py
-------------------
Unit tests for GridShield risk_engine.py
"""
import sys
import os
import math

# Ensure src/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scoring.risk_engine import (
    score_row, _dominant_cause, _factor_thermal, _factor_vibration,
    _factor_partial_dc, _factor_oil, _factor_overload,
    _factor_wind, _factor_rain, _is_electrical,
)


def _base_transformer():
    """Minimal transformer row with no anomalies."""
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
    """Minimal pole row with no anomalies."""
    return {
        "asset_type": "pole",
        "wind_gust_kmh": 0, "rainfall_mm": 0, "flood_depth_cm": 0,
        "tilt_deg": 0, "erosion_index": 0, "corrosion_score": 0,
        "drainage_score": 100, "clearance_score": 100,
        "age_years": 5, "last_maintenance_date": "2024-01-01",
    }


def test_electrical_factors_zero_for_pole():
    row = _base_pole()
    assert _factor_thermal(row) == 0.0
    assert _factor_vibration(row) == 0.0
    assert _factor_partial_dc(row) == 0.0
    assert _factor_oil(row) == 0.0
    assert _factor_overload(row) == 0.0


def test_electrical_factors_nonzero_for_alarmed_transformer():
    row = _base_transformer()
    row.update({
        "temp_residual_c": 40,
        "vibration_rms_delta": 3.5,
        "partial_discharge_cnt": 700,
        "oil_quality_index": 10,
        "loading_ratio": 1.30,
        "overload_duration_h": 18,
    })
    assert _factor_thermal(row) > 10
    assert _factor_vibration(row) > 8
    assert _factor_partial_dc(row) > 10
    assert _factor_oil(row) > 8
    assert _factor_overload(row) > 10


def test_dominant_cause_insulation_for_high_pd_vibration():
    row = _base_transformer()
    row.update({
        "partial_discharge_cnt": 700,
        "vibration_rms_delta": 3.5,
        "oil_quality_index": 5,
        "loading_ratio": 0.5,
        "overload_duration_h": 0,
    })
    result = score_row(row)
    assert result["dominant_cause"] == "insulation_degradation"


def test_dominant_cause_thermal_for_high_temp_overload():
    row = _base_transformer()
    row.update({
        "temp_residual_c": 44,
        "loading_ratio": 1.38,
        "overload_duration_h": 22,
        "partial_discharge_cnt": 0,
        "oil_quality_index": 90,
        "vibration_rms_delta": 0,
    })
    result = score_row(row)
    assert result["dominant_cause"] == "thermal_overload"


def test_risk_score_capped_at_100():
    row = _base_transformer()
    row.update({
        "wind_gust_kmh": 100, "rainfall_mm": 100, "flood_depth_cm": 20,
        "tilt_deg": 7, "erosion_index": 95, "corrosion_score": 95,
        "drainage_score": 0, "clearance_score": 0,
        "age_years": 50, "last_maintenance_date": "2018-01-01",
        "temp_residual_c": 45, "vibration_rms_delta": 4.0,
        "partial_discharge_cnt": 800, "oil_quality_index": 0,
        "loading_ratio": 1.4, "overload_duration_h": 24,
    })
    result = score_row(row)
    assert result["risk_score"] <= 100.0


def test_pole_civil_dominant_cause():
    row = _base_pole()
    row.update({"wind_gust_kmh": 100, "tilt_deg": 7})
    result = score_row(row)
    assert result["dominant_cause"] == "wind_foundation"
