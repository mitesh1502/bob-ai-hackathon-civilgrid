# Data Dictionary — GridShield Datasets

**Version:** v0.3  
**Generator:** `bob-ai-hackathon-gridshield/src/data/generate_data.py` (SEED=42)
**Note:** All data is synthetic. No real utility, geographic, or personal data is included.

---

## assets.csv

Primary asset registry with condition data and electrical sensor readings.

| Column | Type | Range / Values | Description |
|--------|------|---------------|-------------|
| `asset_id` | string | A-01 … A-40 | Unique asset identifier |
| `asset_type` | string | pole / transformer / substation | Type of grid asset |
| `latitude` | float | ~51.0–52.0 | Asset latitude (fictional UK grid area) |
| `longitude` | float | ~-0.5–0.2 | Asset longitude |
| `age_years` | int | 2–44 | Age of asset in years |
| `material` | string | wood / steel / concrete | Construction material |
| `inspection_score` | int | 22–95 | Last inspection score (0=fail, 100=perfect) |
| `tilt_deg` | float | 0–7.0 | Foundation tilt in degrees |
| `corrosion_score` | int | 10–85 | Corrosion severity (0=none, 100=severe) |
| `foundation_type` | string | direct_buried / concrete_pad / rock_anchor | Foundation type |
| `last_maintenance_date` | date | ISO 8601 | Date of last maintenance visit |
| `temp_residual_c` | float / NULL | -2–44 | Thermal residual above ambient baseline (°C). NULL for poles. |
| `vibration_rms_delta` | float / NULL | 0–3.9 | Vibration RMS delta from baseline (mm/s). NULL for poles. |
| `partial_discharge_cnt` | int / NULL | 0–800 | Partial discharge events per hour. NULL for poles. |
| `oil_quality_index` | int / NULL | 5–95 | Oil quality index (0=terrible, 100=perfect). NULL for poles. |
| `loading_ratio` | float / NULL | 0.30–1.38 | Load as fraction of rated capacity (>1.0 = overloaded). NULL for poles. |
| `overload_duration_h` | float / NULL | 0–22 | Hours asset has been operating above rated capacity. NULL for poles. |

---

## weather.csv

3-day forecast weather data per asset.

| Column | Type | Range / Values | Description |
|--------|------|---------------|-------------|
| `asset_id` | string | A-01 … A-40 | Asset identifier |
| `forecast_date` | date | ISO 8601 | Forecast date (T+1, T+2, T+3) |
| `wind_gust_kmh` | float | 10–103 | Peak wind gust in km/h |
| `rainfall_mm` | float | 0–98 | Total rainfall in mm |
| `lightning_risk` | string | low / medium / high | Lightning risk category |
| `temperature_c` | float | 5–28 | Air temperature in °C |
| `flood_depth_cm` | float | 0–20 | Flood depth at asset location in cm |

---

## terrain.csv

Terrain and geotechnical properties per asset.

| Column | Type | Range / Values | Description |
|--------|------|---------------|-------------|
| `asset_id` | string | A-01 … A-40 | Asset identifier |
| `slope` | float | 0–28 | Slope angle in degrees |
| `soil_class` | string | clay / sandy_loam / gravel / peat | Soil classification |
| `erosion_index` | int | 5–95 | Erosion risk index (0=low, 100=severe) |
| `drainage_score` | int | 8–95 | Drainage quality (0=blocked, 100=excellent) |
| `road_access_score` | int | 12–95 | Road/vehicle access score (0=impassable, 100=excellent) |

---

## vegetation.csv

Vegetation encroachment data per asset.

| Column | Type | Range / Values | Description |
|--------|------|---------------|-------------|
| `asset_id` | string | A-01 … A-40 | Asset identifier |
| `canopy_distance_m` | float | 0.3–8.0 | Distance from nearest tree canopy in metres |
| `tree_height_m` | float | 2–28 | Height of nearest tree in metres |
| `clearance_score` | int | 5–95 | Conductor clearance score (0=contact risk, 100=safe) |

---

## topology.csv

Grid topology and downstream load data per asset.

| Column | Type | Range / Values | Description |
|--------|------|---------------|-------------|
| `asset_id` | string | A-01 … A-40 | Asset identifier |
| `feeder_id` | string | F-100 … F-104 | Feeder this asset belongs to |
| `downstream_customers` | int | 50–3500 | Number of customers downstream |
| `critical_loads` | string | hospital / water_treatment / shelter / none | Most critical downstream load |
| `redundancy` | bool | True / False | Whether the feeder has a redundant path |

---

## incidents.csv

Historical incident records.

| Column | Type | Range / Values | Description |
|--------|------|---------------|-------------|
| `asset_id` | string | A-01 … A-40 | Asset identifier |
| `incident_date` | date | ISO 8601 | Date of incident |
| `cause` | string | wind / flood / vegetation_contact / corrosion / equipment_age / thermal_overload / insulation_degradation / unknown | Cause of incident |
| `downtime_hours` | float | 1–72 | Duration of outage in hours |

---

## risk_report.csv (generated)

Output of `risk_engine.py`. Contains all `assets.csv` fields merged with weather, terrain, vegetation, topology, plus scoring outputs.

| Column | Type | Description |
|--------|------|-------------|
| `factor_wind` | float | Wind factor points (0–20) |
| `factor_rain` | float | Rain/flood factor points (0–20) |
| `factor_tilt` | float | Tilt factor points (0–15) |
| `factor_erosion` | float | Erosion factor points (0–15) |
| `factor_corrosion` | float | Corrosion factor points (0–15) |
| `factor_drainage` | float | Drainage factor points (0–10) |
| `factor_vegetation` | float | Vegetation factor points (0–15) |
| `factor_age` | float | Age/maintenance factor points (0–10) |
| `factor_thermal` | float | Thermal overrun factor (0–20; 0 for poles) |
| `factor_vibration` | float | Vibration factor (0–12; 0 for poles) |
| `factor_partial_dc` | float | Partial discharge factor (0–15; 0 for poles) |
| `factor_oil` | float | Oil quality factor (0–12; 0 for poles) |
| `factor_overload` | float | Overload factor (0–16; 0 for poles) |
| `risk_score` | float | Sum of all factors, capped at 100 |
| `dominant_cause` | string | Highest-scoring factor group |

---

## priority_report.csv (generated)

Output of `priority_engine.py`. Adds priority scoring to risk_report.

| Column | Type | Description |
|--------|------|-------------|
| `critical_load_multiplier` | float | 1.0 – 3.0 |
| `expected_loss` | float | `risk_score/100 × customers × multiplier × (1 - redundancy_discount)` |
| `estimated_intervention_cost` | int | Illustrative USD cost to fix (by dominant_cause) |
| `priority_score` | float | `expected_loss / intervention_cost` |

---

## final_report.csv (generated)

Output of `recommend.py`. Adds recommendations to priority_report.

| Column | Type | Description |
|--------|------|-------------|
| `recommended_action` | string | Advisory action text |
| `action_tier` | string | immediate / scheduled / monitor |
| `expected_risk_reduction_pct` | int | Estimated % risk reduction after action |
| `recommended_crew_type` | string | Type of crew required |
| `risk_band` | string | critical / elevated / watch / normal |
| `safety_note` | string | Hard-coded safety advisory (always present) |

---

*GridShield Data Dictionary · v0.3 · IBM Bob Hackathon 2026*
