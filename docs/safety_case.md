# Safety Case — GridShield Advisory System

**Document type:** Safety argument  
**System:** GridShield v0.3  
**Author:** GridShield Dev Team  
**Hackathon:** IBM Bob 2026 · Challenge U1

---

## 1. System Scope and Safety Boundary

GridShield is a **decision-support tool** for qualified utility engineers. It produces ranked maintenance recommendations and risk assessments. It does **not**:

- Issue switching commands
- Control SCADA or EMS systems
- Authorise any field work
- Override any operational control system

---

## 2. Top-Level Safety Claim

**Claim SC-1:** GridShield will not cause or contribute to an unsafe electrical condition on the grid.

**Argument:**
1. All outputs are labelled "ADVISORY ONLY" and cannot directly actuate any field equipment.
2. All recommendations require a written work order reviewed and signed off by a qualified licensed engineer before any action is taken.
3. The advisor module contains a hard-coded refusal gate that detects and refuses any question requesting a switching, energisation, de-energisation, isolation, or breaker operation action.

---

## 3. Hard-Coded Safety Constraints

### 3.1 Safety Note on Every Output

Every row in `final_report.csv` includes:
```
ADVISORY ONLY — This system does not authorise any field work.
No switching, breaker operation, energisation, de-energisation,
excavation, or work on or near live equipment is permitted without
a written work order reviewed and signed off by a qualified licensed
engineer in accordance with applicable utility safety procedures.
```

This note cannot be disabled, overridden, or removed by any user action in the UI.

### 3.2 Advisor Refusal Gate

The `advisor.py` module contains `_is_control_request()` which scans for keywords:
```
energis, energiz, de-energis, de-energiz, switch, open breaker,
close breaker, trip, isolat, reenergis, re-energis
```

When detected, `answer_question()` returns `_control_refusal()` before any other processing:
```
⛔ This request cannot be actioned by GridShield.
GridShield is an ADVISORY system only...
This request must be routed to a qualified licensed engineer...
```

### 3.3 Persistent Advisory Badge

Every page in the Streamlit app displays:
> ⚠ Advisory only — human approval required

This badge cannot be hidden by filter or tab selection.

---

## 4. Hazard Log

| ID | Hazard | Likelihood | Severity | Mitigation | Residual Risk |
|----|--------|-----------|---------|-----------|--------------|
| H-01 | User treats advisory as an operational command | Low | Critical | Safety note on every output + refusal gate + badge | Very Low |
| H-02 | Incorrect risk ranking leads to wrong intervention priority | Medium | Medium | Transparent factor breakdown visible; engineer reviews before acting | Low |
| H-03 | Stale data used for risk scoring | Medium | Medium | Data timestamp badge on every prediction; pipeline reruns visible | Low |
| H-04 | Synthetic sensor data mistaken for real telemetry | Low | High | Data dictionary clearly labels all fields as synthetic | Low |
| H-05 | Advisor answers a control question | Low | Critical | Hard refusal gate in `_is_control_request()` | Very Low |

---

## 5. Testing Evidence

- `test_advisor.py::test_energize_feeder_refused` — verifies that "Energize feeder F-100 now" returns the refusal message
- `test_advisor.py::test_answer_contains_grounding_footer` — verifies all answers include grounding provenance
- Safety note tested in `recommend.py` — present in every output row

---

## 6. Assumptions and Dependencies

- The end user is a qualified utility engineer who understands the advisory nature of the tool
- The grid operator's SCADA/EMS system has independent safety interlocks not connected to GridShield
- The app is deployed on an internal utility network, not publicly accessible

---

*GridShield Safety Case · v0.3 · IBM Bob Hackathon 2026*
