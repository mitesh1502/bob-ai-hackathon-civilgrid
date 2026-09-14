# docs/setup-guide.md — GridShield

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10 or later | [python.org/downloads](https://www.python.org/downloads/) — tick "Add Python to PATH" on Windows |
| pip | bundled with Python | Upgrade with `python -m pip install --upgrade pip` if needed |
| Streamlit | ≥ 1.30 | Installed by the command below |
| pandas | ≥ 2.0 | Installed by the command below |
| pytest | ≥ 7.0 | Only needed to run tests |

**No API keys, database connections, or environment variables are required.** GridShield reads and writes local CSV files only. See `src/.env.example` for optional settings.

---

## Install

```bash
# 1. Clone / download the repository
git clone https://github.com/<your-org>/bob-ai-hackathon-gridshield.git
cd bob-ai-hackathon-gridshield

# 2. Install Python dependencies
pip install streamlit pandas

# 3. (Optional) Install test dependencies
pip install pytest
```

That is the complete install. There are no other dependencies for the primary Streamlit app.

---

## Run the App

### Option A — Direct (recommended)

```bash
# From the submission root:
python -m streamlit run src/app.py --server.port 8502
```

Open your browser at **http://localhost:8502**

The app will detect whether `src/data/final_report.csv` already exists. If it does, the dashboard loads immediately. If not (fresh clone), use Option B first.

### Option B — Run the pipeline first, then launch

```bash
# Step 1: Generate synthetic data (writes 6 CSV files to src/data/)
python src/data/generate_data.py

# Step 2: Score all assets (writes src/data/risk_report.csv)
python src/scoring/risk_engine.py

# Step 3: Compute priority scores (writes src/data/priority_report.csv)
python src/scoring/priority_engine.py

# Step 4: Generate recommendations (writes src/data/final_report.csv)
python src/recommendation/recommend.py

# Step 5: Launch the app
python -m streamlit run src/app.py --server.port 8502
```

Or run all four pipeline steps with the convenience runner:

```bash
python src/pipeline.py
python -m streamlit run src/app.py --server.port 8502
```

### Option C — Windows one-click launcher

Double-click `src/scripts/run_demo.bat` from Windows Explorer. It checks Python, installs packages, runs the full pipeline, and launches the app.

---

## Verify It's Working

After launch, you should see:

1. The browser opens at `http://localhost:8502`
2. The sidebar shows **GridShield** with risk band legend
3. **Tab 1 (Ranked Risk Table)** shows 40 assets, with A-02, A-04, A-05, A-06 in the top rows coloured red (CRITICAL)
4. **Tab 2 (Asset Detail)** — select asset A-04 from the dropdown, confirm the Electrical sensor bars show non-zero values for thermal/vibration/PD
5. **Tab 3 (Advisor Chat)** — type "Why is A-01 ranked above A-15?" and confirm the response starts with a contrast sentence containing "ranks above"
6. **Tab 3** — type "Energize feeder F-100" and confirm the response is a refusal (contains "cannot be actioned")
7. **Tab 7 (BOB Quality Panel)** — confirm session log is visible and release checklist shows 14/14 ✅

---

## Run Tests

```bash
python -m pytest src/tests/ -v
```

Expected output:

```
tests/test_advisor.py::test_comparison_contains_both_asset_ids PASSED
tests/test_advisor.py::test_comparison_text_is_not_identical_for_two_assets PASSED
tests/test_advisor.py::test_comparison_contains_score_difference PASSED
tests/test_advisor.py::test_comparison_contrast_sentence_before_individual_text PASSED
tests/test_advisor.py::test_energize_feeder_refused PASSED
tests/test_advisor.py::test_answer_contains_grounding_footer PASSED
tests/test_risk_engine.py::test_electrical_factors_zero_for_pole PASSED
tests/test_risk_engine.py::test_electrical_factors_nonzero_for_alarmed_transformer PASSED
tests/test_risk_engine.py::test_dominant_cause_insulation_for_high_pd_vibration PASSED
tests/test_risk_engine.py::test_dominant_cause_thermal_for_high_temp_overload PASSED
tests/test_risk_engine.py::test_risk_score_capped_at_100 PASSED
tests/test_risk_engine.py::test_pole_civil_dominant_cause PASSED

12 passed
```

If any test fails, see the troubleshooting table below.

---

## Reset to Seeded Scenario

To restore the app to the original seeded state (SEED=42, 40 assets, 6 high-risk seeded):

**Option 1 — In-app reset:**
Click **"🔄 Rerun Full Pipeline"** in the left sidebar. This re-runs all four pipeline steps and refreshes the dashboard.

**Option 2 — Command line:**
```bash
python src/pipeline.py
```

**Option 3 — Windows:**
Re-run `src/scripts/run_demo.bat`.

---

## Environment Variables

No environment variables are required. The file `src/.env.example` documents optional settings:

| Variable | Default | Purpose |
|---|---|---|
| `STREAMLIT_SERVER_PORT` | 8502 | Override the default port |
| `WEATHER_API_KEY` | (none) | Future: connect to a live weather API |
| `DATABASE_URL` | (none) | Future: connect to a PostgreSQL database |

Copy `src/.env.example` to `src/.env` and uncomment any line you want to use. The app ignores unset variables.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'streamlit'` | Streamlit not installed | `pip install streamlit pandas` |
| App opens but shows "final_report.csv not found" | Pipeline has not been run yet | Run `python src/pipeline.py` first |
| App shows blank/empty table | Same as above | Run `python src/pipeline.py` first |
| Advisor returns "final_report.csv not found" | Pipeline not run, or DATA_DIR path mismatch | Run `python src/pipeline.py` from the submission root |
| Tests fail with `ModuleNotFoundError: No module named 'scoring'` | sys.path not injected | Run as `python -m pytest src/tests/` (not `pytest tests/` alone) |
| Port 8502 already in use | Another Streamlit instance running | Use `--server.port 8503` or stop the other instance |
| Windows: `python` not recognised | Python not on PATH | Reinstall Python, tick "Add Python to PATH" |
| Windows: bat file closes immediately | Execution policy issue | Right-click → "Run as Administrator", or run `Set-ExecutionPolicy RemoteSigned` in PowerShell |
| `streamlit_err.txt` says "address already in use" | Same as port conflict above | Change port or stop other instance |

---

## Bonus: MEAN-Stack Prototype

`src/gridshield-mean/` contains a complete Node.js/Express/Angular/MongoDB port of GridShield. To run it:

### Prerequisites
- Node.js 18+
- MongoDB Community Server running on `localhost:27017`

### Setup
```bash
cd src/gridshield-mean/backend
npm install
node src/pipeline/seed.js        # populate MongoDB
npm run dev                       # start Express API on :3000
```

```bash
cd src/gridshield-mean/frontend
npm install
npm start                         # start Angular dev server on :4200
```

Or use `src/gridshield-mean/start.bat` for a one-click Windows launch.

> The MEAN stack is a bonus deliverable and is **not required** for the primary submission evaluation. The primary app is `src/app.py` (Streamlit).

---

*GridShield Setup Guide · IBM Bob AI Hackathon 2026*
