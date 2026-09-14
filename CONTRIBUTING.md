# Contributing to GridShield

Thank you for your interest in GridShield — IBM Bob AI Hackathon 2026.

## Development Setup

```bash
pip install streamlit pandas pytest
cd src
python pipeline.py          # generate data + run all engines
python -m streamlit run app.py
```

## Running Tests

```bash
python -m pytest src/tests/ -v
```

Expected: **12 passed**

## Code Style

- Follow PEP 8
- All factor functions in `scoring/risk_engine.py` must be deterministic
- No recommendation may authorise live-line work or switching actions
- Every new recommendation must include the `SAFETY_NOTE` from `recommendation/recommend.py`

## Safety Policy

This is an advisory-only system. No contribution may:
- Remove or weaken the `_is_control_request` refusal gate in `ai/advisor.py`
- Remove the `SAFETY_NOTE` from any output row
- Add any UI element that implies the system can directly control field equipment

## Submitting Changes

Since this is a hackathon submission, the primary branch reflects the submitted state.
For evaluation queries contact the team lead listed in `submission.yaml`.
