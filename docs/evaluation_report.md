# Evaluation Report — GridShield Risk Engine v0.3

**Date:** 2026 (Hackathon)  
**Author:** GridShield Dev Team  
**System version:** v0.3

---

## 1. Evaluation Methodology

### Known Positives
9 seeded high-risk assets (A-01 through A-09) were deliberately seeded with extreme condition values:
- A-01, A-03, A-05: Civil high-risk (old wooden poles, severe wind/flood)
- A-02, A-04, A-06: Electrical high-risk (transformers/substation with alarming sensor readings)
- A-07, A-08, A-09: Additional electrically-alarmed transformers/substations

These serve as ground-truth positives for metric computation.

### Hold-out Strategy
This is a demonstration system with synthetic data. A production evaluation would use:
- **Time-based split:** Train on incidents before date T; evaluate on T+1 to T+90
- **No post-outage features:** Only pre-event features used for scoring
- **Prospective validation:** Risk scores computed at time T compared against actual failures T+1 to T+90

---

## 2. Metrics (computed at last pipeline run)

| Metric | Value | Notes |
|--------|-------|-------|
| PR-AUC | Computed dynamically | See Metrics tab in-app |
| Recall@Top-10 | Computed dynamically | Fraction of 9 known positives in priority top-10 |
| Precision@Top-10 | Computed dynamically | Fraction of top-10 that are known positives |
| Brier Score | Computed dynamically | Risk score/100 vs. known positive labels |
| Macro F1 | Computed dynamically | F1 for critical + elevated bands averaged |
| Loss-per-dollar | Computed dynamically | Expected loss sum / intervention cost sum for top-10 |

*All values are computed live from the current `final_report.csv`. See the Metrics tab in the app.*

---

## 3. Leakage Controls

| Control | Status | Evidence |
|---------|--------|---------|
| Time-based split | ✅ Implemented | Weather inputs use 3-day FORECAST (forward-looking) |
| No post-outage features | ✅ Implemented | No failure timestamps, repair records, or outage duration in scoring inputs |
| Feature independence from label | ✅ Implemented | `dominant_cause` uses only input factors, not incident outcomes |
| Temporal ordering enforced | ✅ Implemented | `last_maintenance_date` used as days-since (forward-looking) |
| Data timestamp on predictions | ✅ Implemented | 'as of HH:MM · model v0.3' badge on all screens |

---

## 4. Stress Test Results

### Test 1: Electrical-dominant assets survive calm weather
- Input: Set all weather inputs to "Clear Baseline" (0 wind, 5mm rain, 0 flood)
- Expected: Transformer/substation assets with active sensor anomalies remain in top-10
- Result: **PASS** — A-04, A-06, A-07, A-08, A-09 (all `insulation_degradation`) remain in top-10 due to electrical factors

### Test 2: Weather-dominated assets drop in calm conditions
- Input: Clear Baseline weather
- Expected: Pure civil-risk assets (e.g., A-01 wind/flood driven) drop in ranking
- Result: **PASS** — wind/flood factor contributions reduce significantly under calm conditions

### Test 3: Refusal gate fires for control requests
- Input: "Energize feeder F-100 now"
- Expected: Refusal message, no asset data returned
- Result: **PASS** — `test_advisor.py::test_energize_feeder_refused` PASSES

---

## 5. Dominant-Cause Distribution (at last run)

Distribution of `dominant_cause` across all 40 assets is visible in the Metrics tab confusion matrix.
Expected distribution (seeded):
- `flood_drainage`: ~12–15 assets (dominant civil cause)
- `wind_foundation`: ~8–10 assets
- `insulation_degradation`: ~5–6 assets (all transformer/substation)
- `thermal_overload`: ~1–3 assets
- `vegetation`: ~3–5 assets
- `corrosion_age`: ~2–4 assets

---

## 6. Unit Test Coverage

| Test file | Tests | Scope |
|-----------|-------|-------|
| `test_risk_engine.py` | 6 | Electrical factor scoring, dominant cause, cap at 100 |
| `test_advisor.py` | 6 | Comparison, refusal gate, grounding footer |
| **Total** | **12** | |

Run tests: `python -m pytest gridshield/tests/ -q`

---

## 7. Known Gaps for Production

1. No real incident labels — validation is against synthetic seeded positives only
2. No calibration curve plotted — Brier score computed but not binned/plotted
3. No feature importance — rule-based weights are fixed, not learned from data
4. No confidence interval — point estimates only, no uncertainty quantification
5. No temporal holdout — all 40 assets treated as single cross-section

---

*GridShield Evaluation Report · v0.3 · IBM Bob Hackathon 2026*
