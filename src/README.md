# src/README.md — GridShield Source Layout

This file explains what is in each subfolder of `src/` and how the parts fit together.

---

## Primary Application (Streamlit — Python)

The primary submission is the **Streamlit app** in this folder. It requires only Python and `pip install streamlit pandas`.

```
src/
├── app.py                  ← Streamlit entry point — run this to launch the dashboard
├── pipeline.py             ← CLI runner: executes all 4 pipeline steps in order
├── .env.example            ← Optional environment variable documentation
│
├── data/
│   ├── generate_data.py    ← Synthetic data generator (SEED=42, 40 assets, 6 seeded high-risk)
│   └── *.csv               ← Generated datasets (auto-created by pipeline; committed for convenience)
│
├── scoring/
│   ├── risk_engine.py      ← 13-factor transparent risk scoring; writes risk_report.csv
│   └── priority_engine.py  ← Cost-aware priority formula (expected loss / intervention cost)
│
├── recommendation/
│   └── recommend.py        ← Rule-based action table; writes final_report.csv with safety_note on every row
│
├── ai/
│   └── advisor.py          ← Template NL advisor grounded in final_report.csv
│                              Includes _is_control_request() refusal gate
│
├── app_pages/
│   ├── bob_panel.py        ← Tab 7: BOB Development Quality Panel
│   ├── metrics_panel.py    ← Tab 6: PR-AUC, Brier, F1, confusion matrix
│   └── model_eval.py       ← Tab 5: Model transparency, leakage controls
│
├── tests/
│   ├── test_risk_engine.py ← 6 unit tests for risk_engine.py factor scoring
│   └── test_advisor.py     ← 6 unit tests for advisor comparison, refusal, grounding
│
└── scripts/
    └── run_demo.bat        ← Windows one-click: installs deps + pipeline + app launch
```

**To launch:**
```bash
# From the submission root (one level above src/):
python -m streamlit run src/app.py --server.port 8502
```

**To run tests:**
```bash
python -m pytest src/tests/ -v
```

---

## Pipeline Order

```
generate_data.py  →  risk_engine.py  →  priority_engine.py  →  recommend.py  →  app.py
       ↓                   ↓                    ↓                    ↓
  6 raw CSVs         risk_report.csv    priority_report.csv    final_report.csv
```

Each step reads the output of the previous step. All steps are idempotent — re-running produces the same result (SEED=42).

---

## Bonus Deliverable: MEAN-Stack Prototype

`src/gridshield-mean/` is a **complete, parallel implementation** of GridShield in Node.js / Express / Angular / MongoDB.

- Every Python engine (generate_data, risk_engine, priority_engine, recommend, advisor) is faithfully ported to JavaScript with identical logic and factor weights
- The Angular frontend provides 5 pages: dashboard, risk table, asset detail, reactive vs preventive, advisor chat
- It is **not** the primary submission — the primary app is `src/app.py`
- `node_modules/` is excluded from version control (see `.gitignore`); run `npm install` in both `backend/` and `frontend/` to set it up
- Setup instructions: `src/gridshield-mean/README.md`

---

## No Secrets Required

GridShield reads and writes local CSV files only. There are no API keys, database credentials, or secrets needed to run the primary app. See `.env.example` for the optional future-integration variables.

---

*GridShield src/README.md · IBM Bob AI Hackathon 2026*
