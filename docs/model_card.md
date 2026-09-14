# Model Card — GridShield Risk Engine v0.3

**Date:** 2026 (Hackathon)  
**Model type:** Rule-based transparent scoring (no black-box ML)  
**Version:** v0.3  
**Owner:** GridShield Dev Team

---

## Model Description

GridShield uses a deterministic, fully auditable factor-based scoring system.
Every point contributed to a risk score has a named, human-readable cause with an auditable formula.

**This is not a machine-learning model.** There are no trained weights, no embeddings, and no hidden activations. Every decision is explainable to a non-technical stakeholder.

---

## Inputs

### Civil / Weather Factors (all asset types)

| Factor | Input columns | Weight (max pts) | Notes |
|--------|--------------|-----------------|-------|
| `factor_wind` | `wind_gust_kmh` | 20 | Threshold 60 km/h, ceiling 100 km/h |
| `factor_rain` | `rainfall_mm`, `flood_depth_cm` | 20 | Rain ≥40mm + flood depth |
| `factor_tilt` | `tilt_deg` | 15 | Threshold 3°, ceiling 7° |
| `factor_erosion` | `erosion_index` | 15 | Threshold 60, ceiling 95 |
| `factor_corrosion` | `corrosion_score` | 15 | Threshold 60, ceiling 95 |
| `factor_drainage` | `drainage_score` | 10 | Inverted: low score = high risk |
| `factor_vegetation` | `clearance_score` | 15 | Inverted: low clearance = high risk |
| `factor_age` | `age_years`, `last_maintenance_date` | 10 | Age >20 yrs + overdue >12 months |

### Electrical / Sensor Factors (transformer and substation only)

| Factor | Input columns | Weight (max pts) | Notes |
|--------|--------------|-----------------|-------|
| `factor_thermal` | `temp_residual_c` | 20 | Threshold 10°C, ceiling 45°C |
| `factor_vibration` | `vibration_rms_delta` | 12 | Threshold 0.5 mm/s, ceiling 4.0 mm/s |
| `factor_partial_dc` | `partial_discharge_cnt` | 15 | Threshold 50/h, ceiling 800/h |
| `factor_oil` | `oil_quality_index` | 12 | Inverted: low quality = high risk |
| `factor_overload` | `loading_ratio`, `overload_duration_h` | 16 | Loading >0.9 × rated |

**Total maximum raw score:** ~135 (capped at 100)

---

## Outputs

| Output | Type | Range | Description |
|--------|------|-------|-------------|
| `risk_score` | float | [0, 100] | Sum of factor points, capped at 100 |
| `dominant_cause` | string | 6 categories | Highest-scoring factor group |
| `expected_loss` | float | ≥0 | `risk_score/100 × customers × criticality_multiplier` |
| `priority_score` | float | ≥0 | `expected_loss / intervention_cost` |
| `risk_band` | string | 4 levels | critical(≥70) / elevated(45-69) / watch(20-44) / normal(<20) |
| `recommended_action` | string | — | Rule-based advisory text |
| `action_tier` | string | 3 levels | immediate / scheduled / monitor |

---

## Dominant Cause Groups

| Cause | Contributing factors |
|-------|---------------------|
| `wind_foundation` | factor_wind + factor_tilt |
| `flood_drainage` | factor_rain + factor_erosion + factor_drainage |
| `vegetation` | factor_vegetation |
| `corrosion_age` | factor_corrosion + factor_age |
| `thermal_overload` | factor_thermal + factor_overload |
| `insulation_degradation` | factor_partial_dc + factor_vibration + factor_oil |

---

## Known Limitations

1. **Synthetic sensor data** — All electrical sensor readings are generated from parametric ranges. Real IoT calibration is required for production.
2. **Illustrative cost table** — Intervention costs are approximate. Must be calibrated with actual utility operations data.
3. **Rule-based scoring** — Cannot detect novel failure modes not captured in the 13 factors.
4. **No temporal learning** — Scores are recomputed from current inputs only; no trend or drift detection.
5. **3-day forecast window** — Weather uses max over 3-day forecast; hourly resolution would improve storm-timing accuracy.

---

## Intended Use

- **Intended:** Advisory prioritisation of grid maintenance interventions for qualified utility engineers
- **Not intended for:** Automated switching, real-time control, or any operational action without human sign-off

---

## Safety

All outputs carry a hard-coded safety note. The advisor module refuses control/switching requests.
See `docs/safety_case.md` for the full safety argument.

---

*GridShield Model Card · v0.3 · IBM Bob Hackathon 2026*
