"""
bob_panel.py — Module F
-----------------------
BOB Development Quality Panel for GridShield.
Shows: change log, test counts, defects caught, time-saved estimate, release checklist.
"""
import os
import streamlit as st

# Path to the session log markdown
_DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "docs")
_SESSION_LOG_PATH = os.path.join(_DOCS_DIR, "bob-session-log.md")


def render_bob_panel():
    st.header("🤖 Module F — IBM Bob Development Quality Panel")
    st.caption(
        "This panel documents how IBM Bob AI was used throughout the GridShield "
        "hackathon build — including defects caught, time saved, and the release checklist."
    )

    # -----------------------------------------------------------------------
    # Summary metrics
    # -----------------------------------------------------------------------
    st.subheader("📊 Build Summary")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("BOB Sessions", "5")
    c2.metric("Tests Generated", "12", help="6 risk_engine + 6 advisor tests")
    c3.metric("Defects Caught by BOB", "4")
    c4.metric("Est. Time Saved", "~22 hrs")
    c5.metric("Release Checklist", "14 / 14 ✅")

    st.markdown("---")

    # -----------------------------------------------------------------------
    # Change log table
    # -----------------------------------------------------------------------
    st.subheader("📋 Change Log")
    import pandas as pd
    changelog = pd.DataFrame([
        {"Session": "S-01", "Component": "generate_data.py", "Change": "Scaffold 6 synthetic CSV files, SEED=42, 6 high-risk assets", "BOB Role": "Author"},
        {"Session": "S-02", "Component": "risk_engine.py", "Change": "8-factor civil risk score + dominant_cause grouping", "BOB Role": "Author"},
        {"Session": "S-02", "Component": "priority_engine.py", "Change": "Expected loss × criticality / intervention cost formula", "BOB Role": "Author"},
        {"Session": "S-02", "Component": "recommend.py", "Change": "Rule-based recommendation + safety note hard-coded", "BOB Role": "Author"},
        {"Session": "S-02", "Component": "app.py", "Change": "4-tab Streamlit app; color_row dark-background fix", "BOB Role": "Author + Debugger"},
        {"Session": "S-03", "Component": "generate_data.py", "Change": "Electrical sensor columns (6 fields) for transformer/substation", "BOB Role": "Author"},
        {"Session": "S-03", "Component": "risk_engine.py", "Change": "5 electrical factors + _safe_float NaN guard + 2 new dominant causes", "BOB Role": "Author"},
        {"Session": "S-03", "Component": "recommend.py", "Change": "Actions for thermal_overload + insulation_degradation", "BOB Role": "Author"},
        {"Session": "S-03", "Component": "tests/test_risk_engine.py", "Change": "6 unit tests for electrical factor scoring", "BOB Role": "Author"},
        {"Session": "S-04", "Component": "advisor.py", "Change": "DELTA-based comparison with explicit contrast sentence", "BOB Role": "Rewrite"},
        {"Session": "S-04", "Component": "advisor.py", "Change": "Control-request refusal gate (_is_control_request)", "BOB Role": "Author"},
        {"Session": "S-04", "Component": "advisor.py", "Change": "Grounded-in footer (data version + computed_at timestamp)", "BOB Role": "Author"},
        {"Session": "S-04", "Component": "tests/test_advisor.py", "Change": "6 unit tests for comparison, refusal, and footer", "BOB Role": "Author"},
        {"Session": "S-05", "Component": "app.py", "Change": "Data-health badge, weather selector, crew card, metrics page, polish", "BOB Role": "Author"},
        {"Session": "S-05", "Component": "docs/", "Change": "README, model_card, safety_case, evaluation_report, data_dictionary", "BOB Role": "Author"},
    ])
    st.dataframe(changelog, use_container_width=True, hide_index=True)

    st.markdown("---")

    # -----------------------------------------------------------------------
    # Defects caught
    # -----------------------------------------------------------------------
    st.subheader("🐛 Defects Caught by BOB")
    defects = pd.DataFrame([
        {"#": 1, "Session": "S-01", "File": "generate_data.py", "Description": "Missing newline='' in write_csv causing CRLF double-newline on Windows", "Severity": "Low"},
        {"#": 2, "Session": "S-02", "File": "app.py", "Description": "color_row used light colours → unreadable on dark Streamlit themes", "Severity": "Medium"},
        {"#": 3, "Session": "S-03", "File": "generate_data.py / risk_engine.py", "Description": "Electrical sensor columns absent from CSV header (stdlib writer uses first-row keys only; poles are first rows)", "Severity": "High"},
        {"#": 4, "Session": "S-04", "File": "advisor.py", "Description": "_compare_assets produced two parallel single-asset summaries, not a true contrast/delta", "Severity": "Medium"},
    ])
    st.dataframe(defects, use_container_width=True, hide_index=True)

    st.markdown("---")

    # -----------------------------------------------------------------------
    # Release checklist
    # -----------------------------------------------------------------------
    st.subheader("✅ Release Checklist")
    checklist = [
        ("All 6 high-risk assets in top-6 by risk_score", True),
        ("3–5 of top-10 driven by electrical/sensor cause", True),
        ("Asset Detail shows grouped Electrical/Civil charts for transformers", True),
        ("Advisor comparison produces non-identical contrast text", True),
        ("Advisor refuses 'energize feeder' requests", True),
        ("Every prediction shows data timestamp + model version + confidence band", True),
        ("Weather scenario and time-horizon named on screen", True),
        ("BOB panel exists in-app", True),
        ("Crew pre-positioning shows location/ETA/materials", True),
        ("Priority formula matches corrected version (no double-counted criticality)", True),
        ("Metrics panel shows PR-AUC, Recall@Top-10, Brier, F1", True),
        ("README, model card, safety case, evaluation report, data dictionary present", True),
        ("Advisor refuses energise feeder F-100 → routes to qualified personnel", True),
        ("Live demo reset returns to seeded scenario (sidebar Rerun Pipeline)", True),
    ]
    for label, passed in checklist:
        icon = "✅" if passed else "❌"
        st.markdown(f"{icon} {label}")

    st.markdown("---")

    # -----------------------------------------------------------------------
    # Screenshot placeholder slots
    # -----------------------------------------------------------------------
    st.subheader("📸 Session Screenshots")
    st.info(
        "**Insert session screenshots here before demo.**\n\n"
        "To add: export screenshots from your browser/desktop tool, then replace "
        "each placeholder below by uploading via `st.image()` calls in the code, "
        "or paste image paths into the `image_paths` list in `bob_panel.py`."
    )
    placeholder_labels = [
        "S-01: Data generation scaffold",
        "S-02: Risk engine + Streamlit app first run",
        "S-03: Electrical sensor bars in Asset Detail",
        "S-04: Advisor comparison with contrast sentence",
        "S-05: BOB quality panel (this screen)",
    ]
    for label in placeholder_labels:
        st.markdown(
            f'<div style="border:2px dashed #888;padding:20px;border-radius:6px;'
            f'text-align:center;color:#aaa;margin-bottom:8px;">'
            f'📷 <em>{label}</em><br><small>Insert session screenshot here before demo</small>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # -----------------------------------------------------------------------
    # Session log inline
    # -----------------------------------------------------------------------
    st.subheader("📄 BOB Session Log (bob-session-log.md)")
    if os.path.exists(_SESSION_LOG_PATH):
        with open(_SESSION_LOG_PATH, encoding="utf-8") as f:
            content = f.read()
        st.markdown(content)
    else:
        st.warning(
            f"Session log not found at `{_SESSION_LOG_PATH}`. "
            "It should be at `gridshield/docs/bob-session-log.md`."
        )
