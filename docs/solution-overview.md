# docs/solution-overview.md — GridShield

## How GridShield Works

GridShield is a **transparent, rule-based advisory system** that ranks power grid assets by the expected net benefit of a preventive intervention. It is not a black-box predictor — every point in a risk score has a named cause, an auditable formula, and a human-readable explanation.

---

## The Core Mechanism

```
Sensor telemetry + weather forecast + civil data
        ↓
    13-factor risk score (0–100, capped)
        ↓
    Expected outage cost × action effectiveness − intervention cost
        ↓
    Priority score (net benefit / cost)
        ↓
    Ranked maintenance queue + safety-bounded action plan
        ↓
    Natural-language advisor (grounded, delta-based, refusal gate)
```

### Stage 1: Risk Scoring (risk_engine.py)

Each asset receives points from up to 13 named factors:

**Civil / Weather factors (all asset types):**

| Factor | Max pts | What triggers it |
|---|---|---|
| `factor_wind` | 20 | Wind gust > 60 km/h |
| `factor_rain` | 20 | Rainfall > 40 mm or flood depth > 0 |
| `factor_tilt` | 15 | Foundation tilt > 3° |
| `factor_erosion` | 15 | Erosion index > 60 |
| `factor_corrosion` | 15 | Corrosion score > 60 |
| `factor_drainage` | 10 | Drainage score < 40 (inverted) |
| `factor_vegetation` | 15 | Clearance score < 40 (inverted) |
| `factor_age` | 10 | Age > 20 yrs or maintenance overdue > 12 months |

**Electrical / Sensor factors (transformers and substations only):**

| Factor | Max pts | What triggers it |
|---|---|---|
| `factor_thermal` | 20 | Temp residual > 10°C above ambient |
| `factor_vibration` | 12 | Vibration RMS delta > 0.5 mm/s |
| `factor_partial_dc` | 15 | Partial discharge > 50 events/hour |
| `factor_oil` | 12 | Oil quality index < 60 (inverted) |
| `factor_overload` | 16 | Loading ratio > 0.9 × rated capacity |

The sum is capped at 100. The highest-scoring factor group becomes the `dominant_cause` — the primary label for the crew recommendation.

### Stage 2: Priority Scoring (priority_engine.py)

Raw risk score alone is not enough to decide maintenance order. A risk-score-only queue would always put the highest-risk assets first regardless of cost, customer impact, or whether the asset has a redundant path.

The corrected formula:

```
P_failure        = risk_score / 100
ExpectedLoss     = P_failure × customers × $50/customer × criticality_multiplier
                   × (1 − 0.40 if feeder has redundancy)

criticality_multiplier: hospital=3.0 | water_treatment=2.5 | shelter=2.0 | none=1.0

NetBenefit       = ExpectedLoss × ActionEffectiveness
                   − InterventionCost − MobilizationCost − CarbonCost

PriorityScore    = NetBenefit / max(InterventionCost, $500)
```

**Key design decision:** Criticality is applied once — in `ExpectedLoss`. It is never multiplied again in the priority ratio. This prevents a hospital-connected asset from being automatically boosted regardless of whether the action is actually effective.

### Stage 3: Recommendations (recommend.py)

Each `dominant_cause` maps to a specific, safety-bounded advisory action. All six action types are in a readable action table with:
- `action_tier`: immediate / scheduled / monitor
- `recommended_action`: plain-English field instructions (no live-work instructions)
- `expected_risk_reduction_pct`: estimated % risk reduction after the action
- `recommended_crew_type`: who needs to attend (arborist, HV engineer, civil crew, etc.)
- `safety_note`: hard-coded on every row — cannot be overridden by the UI

---

## What Makes This Different From a Naive Predictor

### 1. The Civil-Engineering Explainability Layer

Most ML-based outage predictors output a score without explaining it. GridShield's factor breakdown means an engineer can look at an asset and say: *"It scores 78/100 because factor_partial_dc is 14.2 points and factor_drainage is 8.5 points — the insulation is degrading and the drainage is blocked."* This is actionable information, not just a number.

### 2. The Priority Formula Separates Risk From Value

A transformer with a risk score of 65 serving a hospital with no redundancy can correctly outrank a transformer with a risk score of 80 serving 50 customers with a backup path. The priority score captures this — the raw risk score does not.

### 3. The Hard Safety Gate

The advisor module contains `_is_control_request()` — a keyword scanner that fires before any data lookup. If a user asks to "energize feeder F-100" or "open breaker X", the response is a refusal, not an answer. This is tested:

```
test_advisor.py::test_energize_feeder_refused — PASSED
```

The safety note is also in every row of `final_report.csv` as a data field, not as a UI decoration. It cannot be suppressed by filtering or changing tabs.

### 4. Grounded Answers, Not Generated Text

The NL advisor in `ai/advisor.py` builds every response by formatting real values from `final_report.csv` into templates. It cannot hallucinate a risk score, a recommended action, or an intervention cost — because those values come directly from the data, not from a language model.

---

## Key Design Decisions

**Why rule-based scoring, not gradient boosting?**
With synthetic data and no real incident labels, a trained ML model would be fitting to noise. A rule-based system with explicit, calibrated factor weights is far more auditable, more defensible to a utility's engineering team, and more likely to behave correctly in the production edge cases that synthetic data doesn't cover. The model card documents this honestly.

**Why human approval is mandatory, not optional**
GridShield has no path to act on an asset without engineer sign-off. This is not just a legal disclaimer — it is enforced in the data pipeline (safety note on every row), the UI (persistent advisory badge on every tab), and the advisor (refusal gate). A system that could recommend AND act would require a different safety architecture entirely.

**Why separate `risk_score` from `priority_score`?**
Risk and priority answer different questions. Risk answers "how likely is this to fail?". Priority answers "given that I have a fixed maintenance budget this week, where does the greatest expected benefit lie?". Conflating them always favours high-risk expensive assets over low-risk cheap assets that serve critical loads.

---

*GridShield Solution Overview · IBM Bob AI Hackathon 2026*
