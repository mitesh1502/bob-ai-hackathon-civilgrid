"""
risk_engine.py
--------------
Transparent, rule-based risk scoring for grid assets.
Every factor contributes a named, capped point value — nothing is a black box.

Risk score = sum of all factor points, capped at 100.

Civil / Weather factors
-----------------------
  factor_wind       : 0 – 20 pts   (wind_gust > 60 km/h, scaled to 100 km/h)
  factor_rain       : 0 – 20 pts   (rainfall > 40 mm OR flood_depth > 0)
  factor_tilt       : 0 – 15 pts   (tilt_deg > 3°, scaled to 7°)
  factor_erosion    : 0 – 15 pts   (erosion_index > 60, scaled to 95)
  factor_corrosion  : 0 – 15 pts   (corrosion_score > 60, scaled to 95)
  factor_drainage   : 0 – 10 pts   (drainage_score < 40)
  factor_vegetation : 0 – 15 pts   (clearance_score < 40)
  factor_age        : 0 – 10 pts   (age > 20 yrs OR maintenance overdue > 12 months)

Electrical / Sensor factors (transformer & substation only)
-----------------------------------------------------------
  factor_thermal    : 0 – 20 pts  (temp_residual > 10 °C, ceiling 45 °C)
  factor_vibration  : 0 – 12 pts  (vibration_rms_delta > 0.5, ceiling 4.0 mm/s)
  factor_partial_dc : 0 – 15 pts  (partial_discharge_cnt > 50, ceiling 800/h)
  factor_oil        : 0 – 12 pts  (oil_quality_index < 60, ceiling 0)
  factor_overload   : 0 – 16 pts  (loading_ratio > 0.9, overload_duration > 0)

Total maximum (elec assets) : 135+ raw → capped at 100.

Dominant cause grouping
-----------------------
  wind_foundation       ← factor_wind + factor_tilt
  flood_drainage        ← factor_rain + factor_erosion + factor_drainage
  vegetation            ← factor_vegetation
  corrosion_age         ← factor_corrosion + factor_age
  thermal_overload      ← factor_thermal + factor_overload       (elec only)
  insulation_degradation← factor_partial_dc + factor_vibration + factor_oil (elec only)

Output: data/risk_report.csv  (sorted by risk_score descending)
"""

import os
import sys
import pandas as pd
from datetime import date

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SRC_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SRC_DIR, "data")


def _load_csvs():
    assets    = pd.read_csv(os.path.join(DATA_DIR, "assets.csv"))
    weather   = pd.read_csv(os.path.join(DATA_DIR, "weather.csv"))
    terrain   = pd.read_csv(os.path.join(DATA_DIR, "terrain.csv"))
    vegetation = pd.read_csv(os.path.join(DATA_DIR, "vegetation.csv"))
    topology  = pd.read_csv(os.path.join(DATA_DIR, "topology.csv"))

    # Use worst-case (max) weather values across the 3-day forecast per asset
    weather_agg = (
        weather.groupby("asset_id")
        .agg(
            wind_gust_kmh =("wind_gust_kmh",  "max"),
            rainfall_mm   =("rainfall_mm",    "max"),
            flood_depth_cm=("flood_depth_cm", "max"),
            lightning_risk=("lightning_risk", lambda x: x.mode()[0]),
        )
        .reset_index()
    )

    df = (
        assets
        .merge(weather_agg, on="asset_id", how="left")
        .merge(terrain,     on="asset_id", how="left")
        .merge(vegetation,  on="asset_id", how="left")
        .merge(topology,    on="asset_id", how="left")
    )
    return df


# ---------------------------------------------------------------------------
# Individual factor scorers (all return float in [0, max_pts])
# ---------------------------------------------------------------------------

def _scale(value, threshold, ceiling, max_pts):
    """Linear scale from threshold → ceiling mapped to 0 → max_pts."""
    if value <= threshold:
        return 0.0
    if value >= ceiling:
        return float(max_pts)
    return round(max_pts * (value - threshold) / (ceiling - threshold), 2)


def _factor_wind(row):
    """High wind gust: 0–20 pts, threshold 60 km/h, ceiling 100 km/h."""
    return _scale(row["wind_gust_kmh"], 60, 100, 20)


def _factor_rain(row):
    """Heavy rain OR flooding: 0–20 pts."""
    rain_pts  = _scale(row["rainfall_mm"],    40, 100, 15)
    flood_pts = _scale(row["flood_depth_cm"],  0,  20,  5)
    return min(20, round(rain_pts + flood_pts, 2))


def _factor_tilt(row):
    """Foundation tilt: 0–15 pts, threshold 3°, ceiling 7°."""
    return _scale(row["tilt_deg"], 3, 7, 15)


def _factor_erosion(row):
    """Erosion index: 0–15 pts, threshold 60, ceiling 95."""
    return _scale(row["erosion_index"], 60, 95, 15)


def _factor_corrosion(row):
    """Corrosion score: 0–15 pts, threshold 60, ceiling 95."""
    return _scale(row["corrosion_score"], 60, 95, 15)


def _factor_drainage(row):
    """Poor drainage: 0–10 pts (drainage_score < 40 means bad)."""
    # Invert: low drainage_score → high risk. Clamp so scores ≥40 give 0.
    inverted = max(0.0, 40 - float(row["drainage_score"]))
    return _scale(inverted, 0, 40, 10)


def _factor_vegetation(row):
    """Low vegetation clearance: 0–15 pts (clearance_score < 40 is danger)."""
    inverted = max(0.0, 40 - float(row["clearance_score"]))
    return _scale(inverted, 0, 40, 15)


def _factor_age(row):
    """Old asset OR overdue maintenance: 0–10 pts."""
    pts = 0.0
    if row["age_years"] > 20:
        pts += _scale(row["age_years"], 20, 50, 6)
    try:
        last_maint = date.fromisoformat(str(row["last_maintenance_date"]))
        months_since = (date.today() - last_maint).days / 30.4
        if months_since > 12:
            pts += _scale(months_since, 12, 36, 4)
    except (ValueError, TypeError):
        pts += 4.0   # unknown maintenance date → penalise
    return round(min(10, pts), 2)


# ---------------------------------------------------------------------------
# Electrical / Sensor factors  (only active for transformer/substation)
# ---------------------------------------------------------------------------

def _is_electrical(row) -> bool:
    return str(row.get("asset_type", "")).strip().lower() in ("transformer", "substation")


def _safe_float(val, default=0.0):
    """Convert value to float, returning default for None/'None'/NaN."""
    import math
    if val is None:
        return default
    try:
        f = float(val)
        return default if math.isnan(f) else f
    except (ValueError, TypeError):
        return default


def _factor_thermal(row) -> float:
    """Thermal overrun: 0–20 pts. temp_residual > 10 °C, ceiling 45 °C."""
    if not _is_electrical(row):
        return 0.0
    val = _safe_float(row.get("temp_residual_c"))
    return _scale(val, 10, 45, 20)


def _factor_vibration(row) -> float:
    """Vibration RMS delta: 0–12 pts. threshold 0.5 mm/s, ceiling 4.0 mm/s."""
    if not _is_electrical(row):
        return 0.0
    val = _safe_float(row.get("vibration_rms_delta"))
    return _scale(val, 0.5, 4.0, 12)


def _factor_partial_dc(row) -> float:
    """Partial-discharge count: 0–15 pts. threshold 50/h, ceiling 800/h."""
    if not _is_electrical(row):
        return 0.0
    val = _safe_float(row.get("partial_discharge_cnt"))
    return _scale(val, 50, 800, 15)


def _factor_oil(row) -> float:
    """Oil quality degradation: 0–12 pts. low quality = high risk (inverted)."""
    if not _is_electrical(row):
        return 0.0
    val = _safe_float(row.get("oil_quality_index"), default=100.0)
    inverted = max(0.0, 60.0 - val)   # 0 quality → 60 pts inverted
    return _scale(inverted, 0, 60, 12)


def _factor_overload(row) -> float:
    """Loading ratio overload + duration: 0–16 pts."""
    if not _is_electrical(row):
        return 0.0
    ratio    = _safe_float(row.get("loading_ratio"))
    duration = _safe_float(row.get("overload_duration_h"))
    ratio_pts    = _scale(ratio,    0.9, 1.4, 10)
    duration_pts = _scale(duration, 0,   24,   6)
    return round(min(16, ratio_pts + duration_pts), 2)


# ---------------------------------------------------------------------------
# Dominant-cause classification
# ---------------------------------------------------------------------------

def _dominant_cause(factors: dict) -> str:
    """Return the dominant risk group name."""
    groups = {
        "wind_foundation":        factors["factor_wind"]  + factors["factor_tilt"],
        "flood_drainage":         factors["factor_rain"]  + factors["factor_erosion"] + factors["factor_drainage"],
        "vegetation":             factors["factor_vegetation"],
        "corrosion_age":          factors["factor_corrosion"] + factors["factor_age"],
        "thermal_overload":       factors["factor_thermal"]   + factors["factor_overload"],
        "insulation_degradation": factors["factor_partial_dc"] + factors["factor_vibration"] + factors["factor_oil"],
    }
    return max(groups, key=groups.get)


# ---------------------------------------------------------------------------
# Per-row scoring
# ---------------------------------------------------------------------------

def score_row(row) -> dict:
    factors = {
        "factor_wind":        _factor_wind(row),
        "factor_rain":        _factor_rain(row),
        "factor_tilt":        _factor_tilt(row),
        "factor_erosion":     _factor_erosion(row),
        "factor_corrosion":   _factor_corrosion(row),
        "factor_drainage":    _factor_drainage(row),
        "factor_vegetation":  _factor_vegetation(row),
        "factor_age":         _factor_age(row),
        # Electrical/sensor (zero for poles/conductors)
        "factor_thermal":     _factor_thermal(row),
        "factor_vibration":   _factor_vibration(row),
        "factor_partial_dc":  _factor_partial_dc(row),
        "factor_oil":         _factor_oil(row),
        "factor_overload":    _factor_overload(row),
    }
    raw_score = sum(factors.values())
    risk_score = round(min(100, raw_score), 1)
    dominant   = _dominant_cause(factors)
    return {**factors, "risk_score": risk_score, "dominant_cause": dominant}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run():
    print("risk_engine — Loading data …")
    df = _load_csvs()

    scored_rows = []
    for _, row in df.iterrows():
        s = score_row(row)
        scored_rows.append(s)

    score_df = pd.DataFrame(scored_rows)
    result = pd.concat([df.reset_index(drop=True), score_df], axis=1)

    # Keep only the columns we need downstream (avoids duplicate merges later)
    keep = [
        "asset_id", "asset_type", "latitude", "longitude",
        "age_years", "material", "inspection_score", "tilt_deg",
        "corrosion_score", "foundation_type", "last_maintenance_date",
        "wind_gust_kmh", "rainfall_mm", "flood_depth_cm",
        "erosion_index", "drainage_score", "road_access_score",
        "clearance_score", "canopy_distance_m", "tree_height_m",
        "feeder_id", "downstream_customers", "critical_loads", "redundancy",
        # Civil / weather factors
        "factor_wind", "factor_rain", "factor_tilt", "factor_erosion",
        "factor_corrosion", "factor_drainage", "factor_vegetation", "factor_age",
        # Electrical / sensor factors
        "factor_thermal", "factor_vibration", "factor_partial_dc",
        "factor_oil", "factor_overload",
        # Electrical sensor raw readings (for display)
        "temp_residual_c", "vibration_rms_delta", "partial_discharge_cnt",
        "oil_quality_index", "loading_ratio", "overload_duration_h",
        "risk_score", "dominant_cause",
    ]
    result = result[[c for c in keep if c in result.columns]]
    result = result.sort_values("risk_score", ascending=False).reset_index(drop=True)

    out_path = os.path.join(DATA_DIR, "risk_report.csv")
    result.to_csv(out_path, index=False)
    print(f"  Written: {out_path}  ({len(result)} rows)")

    # Print top 10 for quick sanity check
    print("\n  Top 10 by risk_score:")
    print(result[["asset_id", "risk_score", "dominant_cause"]].head(10).to_string(index=False))
    print("\nrisk_engine complete.")
    return result


if __name__ == "__main__":
    run()
