# GridShield — Civil-Engineering-Aware Power Grid Advisor

**IBM Bob AI Hackathon 2026 · Challenge U1: Power Outage Prediction & Grid Equipment Failure Advisor**

> ⚠ All data is synthetic. This is a demonstration system. No real utility, geographic, sensor, or personal data is included.

---

## What We Built

GridShield is a transparent, rule-based advisory system that helps grid operators decide **which assets to inspect or repair first** before a failure occurs.

It fuses three data streams that are rarely combined in practice:
- **Electrical sensor telemetry** — temperature residual, vibration RMS, partial-discharge count, oil quality index, loading ratio (transformer and substation assets only)
- **Civil-engineering context** — drainage quality, erosion index, foundation tilt, corrosion score, vegetation clearance, asset age
- **3-day weather forecast** — wind gusts, rainfall, flood depth, lightning risk

Every asset receives a `risk_score` (0–100) built from 13 named, auditable factors. Assets are then ranked by a `priority_score` that accounts for **expected outage cost** (customers × criticality × probability of failure) divided by **intervention cost** — so a moderately risky asset that is cheap to fix and serves a hospital can rank above a higher raw-risk asset that is expensive to fix and has redundancy.

---

## Key Features

| Feature | Description |
|---|---|
| **Ranked risk queue** | All 40 assets sorted by priority score; color-coded by risk band (critical / elevated / watch / normal) |
| **Per-asset factor breakdown** | Bar chart of all 13 contributing factors; grouped Civil and Electrical sections for transformers |
| **NL Advisor** | Grounded question-answering using `final_report.csv` only — no hallucination possible. Answers single-asset questions, produces delta-based comparison for two assets, and **refuses any request to operate switching or live equipment** |
| **Reactive vs Preventive** | Side-by-side comparison of incident history vs the preventive priority queue — shows cost difference and estimated outages avoided |
| **Model & Evaluation** | Full leakage-controls documentation, stress-test results, data timestamp on every prediction |
| **Metrics panel** | PR-AUC, Recall@Top-10, Brier score, Macro F1, dominant-cause confusion matrix |
| **BOB quality panel** | Session log, change log, defects caught, time-saved estimate, release checklist |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Dashboard / UI | [Streamlit](https://streamlit.io) |
| Data pipeline | Python · pandas |
| Risk scoring | Rule-based transparent scoring (13 named factors — no black-box ML) |
| Advisor | Template-based NL engine grounded in `final_report.csv` |
| Bonus prototype | Node.js · Express · Angular · MongoDB (`src/gridshield-mean/`) |
| Tests | pytest · 91 unit tests |
| AI pair programmer | IBM Bob 2.0 |

---

## How to Run

### Prerequisites

```
Python 3.10+
pip install streamlit pandas
```

### One command

```bash
# From the submission root:
python -m streamlit run src/app.py
```

App opens at **http://localhost:8501**

The app auto-detects whether `final_report.csv` exists. If it does, the dashboard loads immediately. If not, click **"🔄 Rerun Full Pipeline"** in the sidebar.

### Run the pipeline manually

```bash
cd src
python data/generate_data.py
python scoring/risk_engine.py
python scoring/priority_engine.py
python recommendation/recommend.py
```

### Run tests

```bash
python -m pytest src/tests/ -v
# Expected: 91 passed
```

### Windows one-click launcher

```
src/scripts/run_demo.bat   ← double-click from Explorer
```

---

## Demo

| Resource | Location |
|---|---|
| Video walkthrough | See `demo/demo-video-link.txt` |
| Live demo (GitHub Pages) | https://mitesh1502.github.io/bob-ai-hackathon-civilgrid/ |
| Static website preview | `demo/website-preview.html` (open in browser) |
| Screenshots | `demo/screenshots/` |

---

## Docs

| Document | Purpose |
|---|---|
| [`docs/problem-statement.md`](docs/problem-statement.md) | Why this problem matters and who it affects |
| [`docs/solution-overview.md`](docs/solution-overview.md) | How GridShield works and what makes it different |
| [`docs/architecture.md`](docs/architecture.md) | Data flow diagram, component table, safety layer |
| [`docs/setup-guide.md`](docs/setup-guide.md) | Full install/run instructions with troubleshooting |
| [`docs/model_card.md`](docs/model_card.md) | Model inputs, outputs, limitations |
| [`docs/safety_case.md`](docs/safety_case.md) | Safety argument, refusal gate, hazard log |
| [`docs/evaluation_report.md`](docs/evaluation_report.md) | Metrics, leakage controls, stress tests |
| [`docs/bob-session-log.md`](docs/bob-session-log.md) | IBM Bob session log, defects caught, time saved |
| [`docs/data_dictionary.md`](docs/data_dictionary.md) | All CSV field definitions |

---

## Known Limitations

We're being honest:

- **Synthetic sensor data** — All electrical readings (temp, PD, oil) are generated from parametric distributions. Real IoT calibration is needed for production.
- **Illustrative cost table** — Intervention costs (e.g. $1,200 for flood drainage work) are approximate. A real deployment needs utility-calibrated cost data.
- **Rule-based, not ML** — The 13-factor scoring system cannot detect novel failure modes outside its defined factors. An ensemble approach (gradient boosting + rules) is the recommended production path.
- **No temporal learning** — Risk scores are recomputed from current inputs; there is no drift detection or trend analysis.
- **3-day weather window** — Weather is aggregated as max over a 3-day forecast. Hourly resolution would improve storm-timing accuracy.

---

## What We're Most Proud Of

1. **The safety architecture** — The advisor genuinely refuses control requests (test-verified). Every single output row carries a hard-coded safety note. These are not UI decorations — they are enforced in the data pipeline itself.

2. **The delta-based comparison** — When you ask "why is A-01 ranked above A-15?", the advisor doesn't give two parallel summaries. It produces a single explicit contrast sentence first, then a delta analysis explaining exactly which factors drove the gap and whether there's a score inversion.

3. **The priority formula** — We deliberately separated raw `risk_score` from `priority_score`. A hospital transformer with a moderate risk score and cheap intervention cost correctly outranks a remote pole with a higher raw score. The formula is fully auditable (expected loss / intervention cost) with no hidden double-counting of criticality.

4. **IBM Bob usage** — Bob caught four real defects during development (Windows CRLF in CSV writer, dark-theme colour contrast, electrical sensor columns missing from CSV header, advisor comparison producing parallel descriptions instead of a contrast). The session log is in `docs/bob-session-log.md` and rendered live in the BOB panel tab.

---

*Built with IBM Bob 2.0 · GridShield · IBM Bob AI Hackathon 2026*
