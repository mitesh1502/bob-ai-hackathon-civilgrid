"""
generate_data.py
----------------
Generates six synthetic CSV files that feed the GridShield risk pipeline.
All data is reproducible (fixed random seed = 42).

Six assets (IDs A-01 … A-06) are deliberately seeded as HIGH-RISK so the
demo tells a clear, credible story:
  • Old infrastructure (age > 30 years)
  • Structural tilt (> 5 °)
  • Poor drainage / high erosion
  • Low vegetation clearance
  • Connected to critical-load feeders (hospital / water-treatment)
  • Recent storm weather forecast

Output files (written to the same directory as this script):
  assets.csv | weather.csv | terrain.csv | vegetation.csv |
  topology.csv | incidents.csv
"""

import os
import random
from datetime import date, timedelta
import math

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SEED = 42
N_ASSETS = 40
N_HIGH_RISK = 6          # A-01 … A-06
DATA_DIR = os.path.dirname(os.path.abspath(__file__))

random.seed(SEED)

# Base geographic centre (fictional UK grid area)
BASE_LAT = 51.50
BASE_LON = -0.12

ASSET_TYPES = ["pole", "transformer", "substation"]
MATERIALS = ["wood", "steel", "concrete"]
FOUNDATION_TYPES = ["direct_buried", "concrete_pad", "rock_anchor"]
SOIL_CLASSES = ["clay", "sandy_loam", "gravel", "peat"]
FEEDER_IDS = ["F-100", "F-101", "F-102", "F-103", "F-104"]
CRITICAL_LOADS = ["hospital", "water_treatment", "shelter", "none"]
CAUSES = ["wind", "flood", "vegetation_contact", "corrosion", "equipment_age",
          "thermal_overload", "insulation_degradation", "unknown"]


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def rand_float(lo, hi, dp=1):
    return round(random.uniform(lo, hi), dp)


def rand_int(lo, hi):
    return random.randint(lo, hi)


def rand_date(years_back=5):
    """Return a random past date within the last `years_back` years."""
    days = rand_int(0, years_back * 365)
    return (date.today() - timedelta(days=days)).isoformat()


def jitter_coord(base, spread=0.4):
    return round(base + random.uniform(-spread, spread), 5)


# ---------------------------------------------------------------------------
# Asset ID helpers
# ---------------------------------------------------------------------------

def asset_id(i):
    return f"A-{i:02d}"


# ---------------------------------------------------------------------------
# 1. assets.csv
# ---------------------------------------------------------------------------

# Electrical sensor columns present for ALL assets; non-electrical assets get NaN markers
ELEC_SENSOR_NA = {
    "temp_residual_c":       None,
    "vibration_rms_delta":   None,
    "partial_discharge_cnt": None,
    "oil_quality_index":     None,
    "loading_ratio":         None,
    "overload_duration_h":   None,
}


def _elec_sensors_high(atype):
    """Generate alarming electrical sensor readings for high-risk transformers/substations."""
    if atype not in ("transformer", "substation"):
        return dict(ELEC_SENSOR_NA)
    return {
        "temp_residual_c":       rand_float(32, 44),      # strongly above ambient baseline → max thermal pts
        "vibration_rms_delta":   rand_float(2.8, 3.9),    # near ceiling → max vibration pts
        "partial_discharge_cnt": rand_int(550, 800),       # PD events per hour → near ceiling
        "oil_quality_index":     rand_int(5, 22),          # very degraded oil → max oil pts
        "loading_ratio":         rand_float(1.20, 1.38),   # heavily overloaded
        "overload_duration_h":   rand_float(14.0, 22.0),  # extended overload duration
    }


def _elec_sensors_normal(atype):
    """Generate normal / low-alarm electrical sensor readings."""
    if atype not in ("transformer", "substation"):
        return dict(ELEC_SENSOR_NA)
    return {
        "temp_residual_c":       rand_float(-2, 10),
        "vibration_rms_delta":   rand_float(0.0, 0.4),
        "partial_discharge_cnt": rand_int(0, 30),
        "oil_quality_index":     rand_int(60, 95),
        "loading_ratio":         rand_float(0.30, 0.85),
        "overload_duration_h":   0.0,
    }


def build_assets():
    rows = []

    # --- 6 seeded high-risk assets ---
    high_risk_profiles = [
        # (asset_type, age_years, material, inspection_score, tilt_deg, corrosion_score, foundation_type, last_maint_offset_days)
        ("pole",         38, "wood",     32, 6.2, 78, "direct_buried", 480),
        ("transformer",  41, "steel",    28, 5.8, 82, "direct_buried", 520),
        ("pole",         35, "wood",     35, 6.7, 71, "direct_buried", 410),
        ("substation",   44, "steel",    22, 5.1, 85, "concrete_pad",  600),
        ("pole",         33, "wood",     30, 7.0, 74, "direct_buried", 390),
        ("transformer",  29, "steel",    40, 5.4, 68, "concrete_pad",  450),
    ]
    for i, (atype, age, mat, insp, tilt, corr, fnd, maint_days) in enumerate(high_risk_profiles, start=1):
        last_maint = (date.today() - timedelta(days=maint_days)).isoformat()
        base = {
            "asset_id":             asset_id(i),
            "asset_type":           atype,
            "latitude":             jitter_coord(BASE_LAT),
            "longitude":            jitter_coord(BASE_LON),
            "age_years":            age,
            "material":             mat,
            "inspection_score":     insp,
            "tilt_deg":             tilt,
            "corrosion_score":      corr,
            "foundation_type":      fnd,
            "last_maintenance_date": last_maint,
        }
        base.update(_elec_sensors_high(atype))
        rows.append(base)

    # --- 3 extra electrically-alarmed assets (A-07 … A-09) ---
    # These have moderate civil exposure but strong sensor anomalies,
    # ensuring 3+ electrical-dominant assets appear in the risk top-10.
    elec_alarm_profiles = [
        # (asset_type, age, material, insp, tilt, corr, fnd, maint_days)
        ("transformer", 22, "steel", 55, 1.5, 40, "concrete_pad",  200),
        ("substation",  18, "steel", 60, 0.8, 35, "concrete_pad",  180),
        ("transformer", 20, "steel", 52, 2.0, 42, "concrete_pad",  220),
    ]
    for i, (atype, age, mat, insp, tilt, corr, fnd, maint_days) in enumerate(elec_alarm_profiles, start=N_HIGH_RISK + 1):
        last_maint = (date.today() - timedelta(days=maint_days)).isoformat()
        base = {
            "asset_id":             asset_id(i),
            "asset_type":           atype,
            "latitude":             jitter_coord(BASE_LAT),
            "longitude":            jitter_coord(BASE_LON),
            "age_years":            age,
            "material":             mat,
            "inspection_score":     insp,
            "tilt_deg":             tilt,
            "corrosion_score":      corr,
            "foundation_type":      fnd,
            "last_maintenance_date": last_maint,
        }
        # Strong electrical anomaly, moderate civil exposure
        base.update({
            "temp_residual_c":       rand_float(28, 42),
            "vibration_rms_delta":   rand_float(2.2, 3.8),
            "partial_discharge_cnt": rand_int(450, 780),
            "oil_quality_index":     rand_int(8, 25),
            "loading_ratio":         rand_float(1.10, 1.32),
            "overload_duration_h":   rand_float(10.0, 20.0),
        })
        rows.append(base)

    # --- 31 normal / mixed assets (A-10 … A-40) ---
    for i in range(N_HIGH_RISK + 4, N_ASSETS + 1):
        age = rand_int(2, 25)
        # Some moderate-risk mixed in deliberately
        tilt = rand_float(0, 4.5)
        corr = rand_int(10, 65)
        insp = rand_int(45, 95)
        maint_days = rand_int(10, 360)
        last_maint = (date.today() - timedelta(days=maint_days)).isoformat()
        atype = random.choice(ASSET_TYPES)
        base = {
            "asset_id":             asset_id(i),
            "asset_type":           atype,
            "latitude":             jitter_coord(BASE_LAT),
            "longitude":            jitter_coord(BASE_LON),
            "age_years":            age,
            "material":             random.choice(MATERIALS),
            "inspection_score":     insp,
            "tilt_deg":             tilt,
            "corrosion_score":      corr,
            "foundation_type":      random.choice(FOUNDATION_TYPES),
            "last_maintenance_date": last_maint,
        }
        base.update(_elec_sensors_normal(atype))
        rows.append(base)
    return rows


# ---------------------------------------------------------------------------
# 2. weather.csv
# ---------------------------------------------------------------------------

def build_weather(asset_rows):
    rows = []
    forecast_base = date.today() + timedelta(days=1)

    for asset in asset_rows:
        aid = asset["asset_id"]
        is_hr = aid in [asset_id(i) for i in range(1, N_HIGH_RISK + 1)]

        if is_hr:
            # Severe incoming weather for high-risk assets
            wind  = rand_float(72, 98)
            rain  = rand_float(48, 90)
            flood = rand_float(4, 18)
            lightning = random.choice(["high", "high", "medium"])
            temp  = rand_float(5, 18)
        else:
            wind  = rand_float(15, 75)
            rain  = rand_float(0, 55)
            flood = rand_float(0, 5)
            lightning = random.choice(["low", "medium", "high"])
            temp  = rand_float(8, 28)

        for day_offset in range(3):   # 3-day forecast window
            rows.append({
                "asset_id":       aid,
                "forecast_date":  (forecast_base + timedelta(days=day_offset)).isoformat(),
                "wind_gust_kmh":  wind + rand_float(-5, 5),
                "rainfall_mm":    max(0, rain + rand_float(-8, 8)),
                "lightning_risk": lightning,
                "temperature_c":  temp,
                "flood_depth_cm": max(0, flood + rand_float(-2, 2)),
            })
    return rows


# ---------------------------------------------------------------------------
# 3. terrain.csv
# ---------------------------------------------------------------------------

def build_terrain(asset_rows):
    rows = []
    for asset in asset_rows:
        aid = asset["asset_id"]
        is_hr = aid in [asset_id(i) for i in range(1, N_HIGH_RISK + 1)]

        if is_hr:
            slope         = rand_float(12, 28)
            soil          = random.choice(["clay", "peat"])
            erosion       = rand_int(68, 95)
            drainage      = rand_int(8, 35)    # low = poor
            road_access   = rand_int(12, 40)   # low = hard to reach
        else:
            slope         = rand_float(0, 18)
            soil          = random.choice(SOIL_CLASSES)
            erosion       = rand_int(5, 72)
            drainage      = rand_int(30, 95)
            road_access   = rand_int(30, 95)

        rows.append({
            "asset_id":          aid,
            "slope":             slope,
            "soil_class":        soil,
            "erosion_index":     erosion,
            "drainage_score":    drainage,
            "road_access_score": road_access,
        })
    return rows


# ---------------------------------------------------------------------------
# 4. vegetation.csv
# ---------------------------------------------------------------------------

def build_vegetation(asset_rows):
    rows = []
    for asset in asset_rows:
        aid = asset["asset_id"]
        is_hr = aid in [asset_id(i) for i in range(1, N_HIGH_RISK + 1)]

        if is_hr:
            canopy   = rand_float(0.3, 1.8)
            height   = rand_float(14, 28)
            clearance = rand_int(5, 32)
        else:
            canopy   = rand_float(0.5, 8.0)
            height   = rand_float(2, 20)
            clearance = rand_int(25, 95)

        rows.append({
            "asset_id":          aid,
            "canopy_distance_m": canopy,
            "tree_height_m":     height,
            "clearance_score":   clearance,
        })
    return rows


# ---------------------------------------------------------------------------
# 5. topology.csv
# ---------------------------------------------------------------------------

def build_topology(asset_rows):
    rows = []
    for asset in asset_rows:
        aid = asset["asset_id"]
        is_hr = aid in [asset_id(i) for i in range(1, N_HIGH_RISK + 1)]

        if is_hr:
            feeder   = random.choice(["F-100", "F-101"])   # critical feeders
            cust     = rand_int(800, 3500)
            cl       = random.choice(["hospital", "water_treatment", "hospital", "shelter"])
            redundancy = False
        else:
            feeder   = random.choice(FEEDER_IDS)
            cust     = rand_int(50, 1500)
            cl       = random.choice(CRITICAL_LOADS)
            redundancy = random.choice([True, False])

        rows.append({
            "asset_id":             aid,
            "feeder_id":            feeder,
            "downstream_customers": cust,
            "critical_loads":       cl,
            "redundancy":           redundancy,
        })
    return rows


# ---------------------------------------------------------------------------
# 6. incidents.csv
# ---------------------------------------------------------------------------

def build_incidents(asset_rows):
    rows = []
    # High-risk assets get 2-3 historical incidents each
    for i in range(1, N_HIGH_RISK + 1):
        aid = asset_id(i)
        n_incidents = rand_int(2, 3)
        for _ in range(n_incidents):
            rows.append({
                "asset_id":      aid,
                "incident_date": rand_date(years_back=4),
                "cause":         random.choice(["wind", "flood", "vegetation_contact", "corrosion"]),
                "downtime_hours": rand_float(4, 72),
            })

    # A few random normal assets also have 1 past incident
    normal_ids = [asset_id(i) for i in range(N_HIGH_RISK + 1, N_ASSETS + 1)]
    random.shuffle(normal_ids)
    for aid in normal_ids[:8]:
        rows.append({
            "asset_id":      aid,
            "incident_date": rand_date(years_back=5),
            "cause":         random.choice(CAUSES),
            "downtime_hours": rand_float(1, 24),
        })
    return rows


# ---------------------------------------------------------------------------
# CSV writer (no pandas dependency here — stdlib only)
# ---------------------------------------------------------------------------

def write_csv(filename, rows):
    if not rows:
        return
    path = os.path.join(DATA_DIR, filename)
    keys = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        f.write(",".join(keys) + "\n")
        for row in rows:
            f.write(",".join(str(row[k]) for k in keys) + "\n")
    print(f"  Written: {path}  ({len(rows)} rows)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate_all():
    print("GridShield — Generating synthetic data …")
    assets    = build_assets()
    weather   = build_weather(assets)
    terrain   = build_terrain(assets)
    vegetation = build_vegetation(assets)
    topology  = build_topology(assets)
    incidents = build_incidents(assets)

    write_csv("assets.csv",    assets)
    write_csv("weather.csv",   weather)
    write_csv("terrain.csv",   terrain)
    write_csv("vegetation.csv", vegetation)
    write_csv("topology.csv",  topology)
    write_csv("incidents.csv", incidents)
    print("Data generation complete.")


if __name__ == "__main__":
    generate_all()
