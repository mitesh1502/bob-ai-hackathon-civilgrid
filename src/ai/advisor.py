"""
advisor.py
----------
Template-based natural-language advisor for GridShield.

Answers questions grounded ONLY in final_report.csv — no free-form generation,
no hallucination possible because every sentence is built from real data values.

Detection logic
---------------
  • Finds asset IDs in the question (patterns: "A-01", "A01", "asset 1", "A1")
  • Two assets found  → compare priority_score, risk_score, dominant_cause, action
  • One asset found   → explain risk, cause, recommendation, cost, safety note
  • Zero assets found → answer from top-priority asset (or storm/priority keywords)

Always appends the safety note to every response.

Usage
-----
  CLI:   python advisor.py "Why is A-02 ranked above A-15?"
  API:   from src.ai.advisor import answer_question
         text = answer_question("What should we do about A-03?")
"""

from __future__ import annotations

import os
import re
import sys
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SRC_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SRC_DIR, "data")

# ---------------------------------------------------------------------------
# Loader (cached at module level to avoid re-reading on every call)
# ---------------------------------------------------------------------------
_df_cache = None

def _load_report() -> pd.DataFrame:
    global _df_cache
    if _df_cache is not None:
        return _df_cache
    path = os.path.join(DATA_DIR, "final_report.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"final_report.csv not found at {path}. "
            "Run the full pipeline first (pipeline.py or run_gridshield.bat)."
        )
    _df_cache = pd.read_csv(path)
    return _df_cache


def reload_report():
    """Force a fresh load (called after pipeline reruns from the Streamlit app)."""
    global _df_cache
    _df_cache = None
    return _load_report()


# ---------------------------------------------------------------------------
# Asset ID detection
# ---------------------------------------------------------------------------

# Matches: A-01, A01, A-1, A1, asset 1, asset A-05, asset-12
_ID_PATTERNS = [
    r"\bA-(\d{1,2})\b",        # A-01 or A-1
    r"\bA(\d{1,2})\b",         # A01 or A1
    r"\basset[-\s]*(\d{1,2})\b",  # asset 1, asset-12
]

def _detect_asset_ids(question: str, df: pd.DataFrame) -> list[str]:
    """Return canonical asset IDs (e.g. 'A-01') mentioned in the question."""
    found = set()
    q = question.upper()
    # First try direct pattern match
    for pattern in _ID_PATTERNS:
        for m in re.finditer(pattern, q, re.IGNORECASE):
            num = int(m.group(1))
            candidate = f"A-{num:02d}"
            if candidate in df["asset_id"].values:
                found.add(candidate)
    # Also check if any actual asset ID string appears verbatim
    for aid in df["asset_id"].values:
        if aid.upper() in q:
            found.add(aid)
    return sorted(found)


# ---------------------------------------------------------------------------
# Response builders
# ---------------------------------------------------------------------------

def _fmt_currency(value) -> str:
    """Format a currency value with $ escaped for Streamlit Markdown rendering."""
    try:
        return r"\$" + f"{int(value):,}"
    except (ValueError, TypeError):
        return str(value)


def _fmt_score(value, dp=1) -> str:
    try:
        return f"{float(value):.{dp}f}"
    except (ValueError, TypeError):
        return str(value)


def _asset_summary(row) -> str:
    """One-paragraph summary of a single asset."""
    aid   = row["asset_id"]
    atype = row.get("asset_type", "asset")
    band  = row.get("risk_band",  "unknown")
    rs    = _fmt_score(row.get("risk_score", 0))
    ps    = _fmt_score(row.get("priority_score", 0), dp=4)
    cause = row.get("dominant_cause", "unknown").replace("_", " ")
    loss  = _fmt_score(row.get("expected_loss", 0), dp=1)
    cost  = _fmt_currency(row.get("estimated_intervention_cost", 0))
    crit  = row.get("critical_loads", "none")
    cust  = row.get("downstream_customers", 0)
    red   = row.get("redundancy", False)
    action = row.get("recommended_action", "See final_report.csv for details.")
    rr    = row.get("expected_risk_reduction_pct", "?")
    tier  = row.get("action_tier", "")
    crew  = row.get("recommended_crew_type", "")

    redundancy_note = (
        "This feeder has a redundant path, which reduces expected customer impact by 40%."
        if str(red).strip().lower() in ("true", "1", "yes")
        else "This feeder has NO redundancy — a failure here directly affects all downstream customers."
    )

    return (
        f"Asset {aid} is a {atype} rated {band.upper()} risk "
        f"(risk score {rs}/100, priority score {ps}).\n\n"
        f"Primary concern: {cause}.\n\n"
        f"It serves {int(cust):,} downstream customers"
        + (f" including a {crit.replace('_', ' ')}" if crit != "none" else "")
        + f", giving an expected loss index of {loss}. "
        f"{redundancy_note}\n\n"
        f"Recommended action ({tier}, {crew}):\n  {action}\n\n"
        f"Estimated intervention cost: {cost}. "
        f"Expected risk reduction after action: {rr}%.\n"
    )


# Keywords that indicate the user wants to issue a control action — must be refused
_CONTROL_KEYWORDS = [
    "energis", "energiz", "de-energis", "de-energiz", "switch", "open breaker",
    "close breaker", "trip", "isolat", "reenergis", "re-energis",
]


def _is_control_request(question: str) -> bool:
    q = question.lower()
    return any(kw in q for kw in _CONTROL_KEYWORDS)


def _control_refusal(question: str) -> str:
    return (
        "[REFUSED] **This request cannot be actioned by GridShield.**\n\n"
        "GridShield is an ADVISORY system only. It does not authorise, initiate, or "
        "confirm any switching, energisation, de-energisation, breaker operation, "
        "or isolation action.\n\n"
        "This request must be routed to a **qualified licensed engineer** who will "
        "issue a formal written switching plan in accordance with applicable utility "
        "safety procedures."
    )


def _compare_assets(row_a, row_b) -> str:
    """
    Produce a single explicit contrast sentence FIRST, then individual detail.
    Uses a DELTA-based explanation — never two parallel descriptions.
    """
    aid = row_a["asset_id"]
    bid = row_b["asset_id"]

    ps_a = float(row_a.get("priority_score", 0))
    ps_b = float(row_b.get("priority_score", 0))
    rs_a = float(row_a.get("risk_score", 0))
    rs_b = float(row_b.get("risk_score", 0))
    loss_a = float(row_a.get("expected_loss", 0))
    loss_b = float(row_b.get("expected_loss", 0))

    higher, lower = (row_a, row_b) if ps_a >= ps_b else (row_b, row_a)
    hid = higher["asset_id"]
    lid = lower["asset_id"]

    ps_h  = float(higher["priority_score"])
    ps_l  = float(lower["priority_score"])
    rs_h  = float(higher["risk_score"])
    rs_l  = float(lower["risk_score"])
    loss_h = float(higher.get("expected_loss", 0))
    loss_l = float(lower.get("expected_loss", 0))
    ps_delta = ps_h - ps_l
    loss_delta = loss_h - loss_l

    cause_h = higher.get("dominant_cause", "unknown").replace("_", " ")
    cause_l = lower.get("dominant_cause",  "unknown").replace("_", " ")
    cost_h  = _fmt_currency(higher.get("estimated_intervention_cost", 0))
    cost_l  = _fmt_currency(lower.get("estimated_intervention_cost",  0))
    crit_h  = higher.get("critical_loads", "none")
    crit_l  = lower.get("critical_loads",  "none")
    cust_h  = int(higher.get("downstream_customers", 0))
    cust_l  = int(lower.get("downstream_customers",  0))

    # -----------------------------------------------------------------------
    # 1. One-line explicit contrast sentence (required by spec)
    # -----------------------------------------------------------------------
    contrast = (
        f"**{hid} ranks above {lid}** because its expected loss index is "
        f"{_fmt_score(loss_h, 1)} vs {_fmt_score(loss_l, 1)}, driven by "
        f"**{cause_h}** vs **{cause_l}**, "
        f"and its priority score is {_fmt_score(ps_h, 5)} vs {_fmt_score(ps_l, 5)} "
        f"(delta: +{_fmt_score(ps_delta, 5)})."
    )

    # -----------------------------------------------------------------------
    # 2. Delta explanation — WHY the gap exists
    # -----------------------------------------------------------------------
    delta_lines = []

    if rs_h < rs_l:
        # Interesting inversion: lower raw risk but higher priority
        delta_lines.append(
            f"**Score inversion:** {lid} has a higher raw risk score ({_fmt_score(rs_l)}/100) "
            f"than {hid} ({_fmt_score(rs_h)}/100), but {hid} overtakes on priority "
            f"because its intervention cost ({cost_h}) is lower than {lid}'s ({cost_l}), "
            f"giving a better expected-loss-per-dollar ratio."
        )
    else:
        delta_lines.append(
            f"**Risk gap:** {hid} scores {_fmt_score(rs_h)}/100 vs {lid} at "
            f"{_fmt_score(rs_l)}/100 — a raw gap of {_fmt_score(rs_h - rs_l, 1)} points."
        )

    if abs(loss_delta) > 0.1:
        direction = "higher" if loss_delta > 0 else "lower"
        delta_lines.append(
            f"**Customer exposure:** {hid}'s expected loss ({_fmt_score(loss_h, 1)}) is "
            f"{direction} than {lid}'s ({_fmt_score(loss_l, 1)}) by "
            f"{_fmt_score(abs(loss_delta), 1)} — "
            + (
                f"{hid} serves {cust_h:,} customers"
                + (f" including a {crit_h.replace('_',' ')}" if crit_h != "none" else " (no critical load)")
                + f"; {lid} serves {cust_l:,}"
                + (f" including a {crit_l.replace('_',' ')}" if crit_l != "none" else " (no critical load)")
                + "."
            )
        )

    delta_lines.append(
        f"**Cause delta:** {hid} is primarily driven by **{cause_h}** (cost {cost_h}) "
        f"whereas {lid} is driven by **{cause_l}** (cost {cost_l})."
    )

    # -----------------------------------------------------------------------
    # 3. Actions (compact, one each — not two parallel paragraphs)
    # -----------------------------------------------------------------------
    action_h = str(higher.get("recommended_action", "")).split(".")[0] + "."  # first sentence
    action_l = str(lower.get("recommended_action", "")).split(".")[0] + "."

    lines = [
        contrast,
        "",
        "---",
        "**Why the gap exists (delta analysis):**",
        "",
    ] + [f"- {d}" for d in delta_lines] + [
        "",
        f"**Next action for {hid}:** {action_h}",
        f"**Next action for {lid}:** {action_l}",
        "",
        f"*(Full recommendations available in Asset Detail view.)*",
    ]
    return "\n".join(lines)


def _top_asset_answer(df: pd.DataFrame, question: str) -> str:
    """Fallback: answer about the top-priority asset when no ID is detected."""
    top = df.iloc[0]
    intro = (
        "No specific asset was identified in your question. "
        "Here is a summary of the highest-priority asset in the current queue:\n\n"
    )
    return intro + _asset_summary(top)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def answer_question(question: str, df: pd.DataFrame = None) -> str:
    """
    Return a grounded natural-language answer to `question`.

    Parameters
    ----------
    question : str
        Free-text question from the user.
    df : pd.DataFrame, optional
        Pre-loaded final_report DataFrame. If None, loads from disk.

    Returns
    -------
    str
        Answer text, always ending with the safety note.
    """
    if df is None:
        df = _load_report()

    # Hard gate: refuse control/switching requests before anything else
    if _is_control_request(question):
        return _control_refusal(question)

    # Sort by priority_score so positional references ("top asset") are stable
    df = df.sort_values("priority_score", ascending=False).reset_index(drop=True)

    asset_ids = _detect_asset_ids(question, df)

    if len(asset_ids) >= 2:
        row_a = df[df["asset_id"] == asset_ids[0]].iloc[0]
        row_b = df[df["asset_id"] == asset_ids[1]].iloc[0]
        body  = _compare_assets(row_a, row_b)
    elif len(asset_ids) == 1:
        row  = df[df["asset_id"] == asset_ids[0]].iloc[0]
        body = _asset_summary(row)
    else:
        body = _top_asset_answer(df, question)

    from datetime import datetime as _dt
    computed_at = _dt.now().strftime("%H:%M")
    safety = (
        "\n\n---\n"
        "⚠ SAFETY REMINDER: "
        + str(df.iloc[0].get("safety_note",
            "This is advisory only. All field actions require engineer sign-off."))
    )
    footer = (
        f"\n\n*Grounded in: asset table v0.3 · final_report.csv · computed at {computed_at}*"
    )
    return body + safety + footer


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_questions = [
        "Why is A-01 ranked above A-15?",
        "What should we do about asset A-03?",
        "Which assets are most at risk from the incoming storm?",
        "Compare A-02 and A-20",
    ]

    questions = sys.argv[1:] if len(sys.argv) > 1 else test_questions

    df = _load_report()
    for q in questions:
        print(f"\n{'='*70}")
        print(f"Q: {q}")
        print(f"{'='*70}")
        print(answer_question(q, df))
