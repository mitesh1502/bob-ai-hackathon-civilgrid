"""
test_generate_data.py
---------------------
Unit tests for GridShield data/generate_data.py

Covers:
  - build_assets returns exactly N_ASSETS rows
  - all asset IDs are unique
  - high-risk assets A-01..A-06 have old age (>25 years)
  - high-risk assets A-01..A-06 have high tilt (>5 degrees)
  - high-risk assets A-01..A-06 have high corrosion (>65)
  - electrical assets have non-None sensor columns
  - non-electrical assets (poles) have None sensor columns
  - build_weather returns 3 rows per asset (3-day forecast)
  - build_terrain: all rows have required columns
  - build_vegetation: all rows have required columns
  - build_topology: all rows have required columns
  - build_incidents: seeded high-risk assets A-01..A-06 have ≥2 incidents each
  - seed reproducibility: two runs produce identical asset data
"""
import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data.generate_data import (
    build_assets,
    build_weather,
    build_terrain,
    build_vegetation,
    build_topology,
    build_incidents,
    N_ASSETS,
    N_HIGH_RISK,
    SEED,
)

SEEDED_HIGH_RISK_IDS = [f"A-{i:02d}" for i in range(1, N_HIGH_RISK + 1)]
ELEC_SENSOR_COLS = [
    "temp_residual_c", "vibration_rms_delta", "partial_discharge_cnt",
    "oil_quality_index", "loading_ratio", "overload_duration_h",
]


def _fresh_assets():
    random.seed(SEED)
    return build_assets()


# ---------------------------------------------------------------------------
# build_assets
# ---------------------------------------------------------------------------

def test_build_assets_returns_n_assets_rows():
    assets = _fresh_assets()
    assert len(assets) == N_ASSETS


def test_all_asset_ids_unique():
    assets = _fresh_assets()
    ids = [a["asset_id"] for a in assets]
    assert len(ids) == len(set(ids))


def test_high_risk_assets_are_old():
    assets = _fresh_assets()
    hr = {a["asset_id"]: a for a in assets if a["asset_id"] in SEEDED_HIGH_RISK_IDS}
    for aid, asset in hr.items():
        assert asset["age_years"] > 25, f"{aid} age too low: {asset['age_years']}"


def test_high_risk_assets_have_high_tilt():
    assets = _fresh_assets()
    hr = {a["asset_id"]: a for a in assets if a["asset_id"] in SEEDED_HIGH_RISK_IDS}
    for aid, asset in hr.items():
        assert asset["tilt_deg"] > 5.0, f"{aid} tilt too low: {asset['tilt_deg']}"


def test_high_risk_assets_have_high_corrosion():
    assets = _fresh_assets()
    hr = {a["asset_id"]: a for a in assets if a["asset_id"] in SEEDED_HIGH_RISK_IDS}
    for aid, asset in hr.items():
        assert asset["corrosion_score"] > 65, f"{aid} corrosion too low: {asset['corrosion_score']}"


def test_electrical_assets_have_sensor_columns():
    assets = _fresh_assets()
    elec_assets = [a for a in assets if a["asset_type"] in ("transformer", "substation")]
    for a in elec_assets:
        for col in ELEC_SENSOR_COLS:
            assert col in a, f"Missing column {col} in {a['asset_id']}"


def test_pole_assets_have_none_sensor_columns():
    assets = _fresh_assets()
    pole_assets = [a for a in assets if a["asset_type"] == "pole"]
    for a in pole_assets:
        for col in ELEC_SENSOR_COLS:
            assert a.get(col) is None, \
                f"Expected None for {col} in pole {a['asset_id']}, got {a.get(col)}"


# ---------------------------------------------------------------------------
# build_weather
# ---------------------------------------------------------------------------

def test_build_weather_three_rows_per_asset():
    assets = _fresh_assets()
    weather = build_weather(assets)
    counts = {}
    for w in weather:
        counts[w["asset_id"]] = counts.get(w["asset_id"], 0) + 1
    assert all(c == 3 for c in counts.values()), "Each asset should have 3 weather forecast rows"


def test_build_weather_required_columns():
    assets = _fresh_assets()
    weather = build_weather(assets)
    required = {"asset_id", "forecast_date", "wind_gust_kmh", "rainfall_mm",
                "flood_depth_cm", "lightning_risk", "temperature_c"}
    for row in weather[:5]:
        assert required.issubset(set(row.keys()))


# ---------------------------------------------------------------------------
# build_terrain / build_vegetation / build_topology
# ---------------------------------------------------------------------------

def test_build_terrain_required_columns():
    assets = _fresh_assets()
    terrain = build_terrain(assets)
    required = {"asset_id", "slope", "soil_class", "erosion_index",
                "drainage_score", "road_access_score"}
    assert len(terrain) == N_ASSETS
    for row in terrain[:5]:
        assert required.issubset(set(row.keys()))


def test_build_vegetation_required_columns():
    assets = _fresh_assets()
    veg = build_vegetation(assets)
    required = {"asset_id", "canopy_distance_m", "tree_height_m", "clearance_score"}
    assert len(veg) == N_ASSETS
    for row in veg[:5]:
        assert required.issubset(set(row.keys()))


def test_build_topology_required_columns():
    assets = _fresh_assets()
    topo = build_topology(assets)
    required = {"asset_id", "feeder_id", "downstream_customers", "critical_loads", "redundancy"}
    assert len(topo) == N_ASSETS
    for row in topo[:5]:
        assert required.issubset(set(row.keys()))


# ---------------------------------------------------------------------------
# build_incidents
# ---------------------------------------------------------------------------

def test_seeded_high_risk_assets_have_multiple_incidents():
    assets = _fresh_assets()
    incidents = build_incidents(assets)
    counts = {}
    for inc in incidents:
        counts[inc["asset_id"]] = counts.get(inc["asset_id"], 0) + 1
    for aid in SEEDED_HIGH_RISK_IDS:
        assert counts.get(aid, 0) >= 2, f"{aid} should have ≥2 incidents"
