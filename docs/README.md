# GridShield — Power Grid Equipment Failure Advisor

**IBM Bob AI Hackathon 2026 · Challenge U1: Power Outage Prediction & Grid Equipment Failure Advisor**

---

## Overview

GridShield is a transparent, rule-based advisory system that prioritises power grid maintenance interventions using civil engineering, weather forecast, terrain, vegetation, topology, and electrical sensor data.

**Key capabilities:**
- Ranks grid assets by a cost-aware priority score (expected loss ÷ intervention cost)
- Electrical sensor-fusion layer for transformers and substations (temperature, vibration, partial discharge, oil quality, loading ratio)
- Grounded natural-language advisor with comparison and refusal gates
- Crew pre-positioning card with staging location, ETA, and materials checklist
- Model & Evaluation page with full leakage controls documentation
- Metrics panel (PR-AUC, Recall@Top-10, Brier score, Macro F1, confusion matrix)

---

## Quick Start

### Prerequisites
```
Python 3.10+
pip install streamlit pandas
```

### Run
```bash
cd bob-ai-hackathon-gridshield
python -m streamlit run src/app.py
```

App will be available at: **http://localhost:8501**

### Reset to seeded scenario
Click **"🔄 Rerun Full Pipeline"** in the sidebar, or run:
```bash
python bob-ai-hackathon-gridshield/src/pipeline.py
```

---

## Architecture

```
bob-ai-hackathon-gridshield/
├── src/
│   ├── app.py                        ← Streamlit entry point (7 tabs)
│   ├── data/
│   │   ├── generate_data.py          ← Synthetic data generator (SEED=42)
│   │   └── *.csv                     ← Generated datasets
│   ├── scoring/
│   │   ├── risk_engine.py            ← 13-factor transparent risk scoring
│   │   └── priority_engine.py        ← Cost-aware priority + net-benefit
│   ├── recommendation/
│   │   └── recommend.py              ← Rule-based action mapping
│   ├── ai/
│   │   └── advisor.py                ← NL advisor with DELTA comparison
│   └── app_pages/
│       ├── bob_panel.py              ← Module F: BOB quality panel
│       ├── model_eval.py             ← Leakage controls + model docs
│       └── metrics_panel.py          ← PR-AUC, Brier, F1, confusion matrix
├── tests/
│   ├── test_risk_engine.py           ← 6 unit tests
│   ├── test_risk_engine_extended.py  ← Extended electrical factor tests
│   ├── test_advisor.py               ← 6 unit tests
│   ├── test_generate_data.py
│   ├── test_priority_engine.py
│   └── test_recommend.py
└── docs/
    ├── README.md (this file)
    ├── model_card.md
    ├── safety_case.md
    ├── evaluation_report.md
    ├── bob-session-log.md
    └── data_dictionary.md
```

---

## Pipeline

```
generate_data.py → risk_engine.py → priority_engine.py → recommend.py → app.py
```

Each step outputs a CSV that the next step reads. All steps are idempotent with SEED=42.

---

## Safety Constraint

**GridShield is advisory only.** No output from this system authorises:
- Opening or closing breakers
- Energising or de-energising lines
- Excavation
- Work on or near live equipment

All field actions require a written work order reviewed and signed off by a **qualified licensed engineer**.

---

## Tests

```bash
python -m pytest bob-ai-hackathon-gridshield/src/tests/ -q
```

Expected: **12 passed**

---

## Docs

| Document | Purpose |
|----------|---------|
| [model_card.md](model_card.md) | Model architecture, inputs, outputs, limitations |
| [safety_case.md](safety_case.md) | Safety argument and refusal gates |
| [evaluation_report.md](evaluation_report.md) | Metrics, leakage controls, stress test |
| [bob-session-log.md](bob-session-log.md) | IBM Bob development session log |
| [data/data_dictionary.md](../src/data/data_dictionary.md) | All CSV field definitions |

---

*Built with IBM Bob 2.0 · GridShield Hackathon 2026*
