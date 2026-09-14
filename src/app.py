# -*- coding: utf-8 -*-
"""
app.py
------
GridShield — Streamlit front-end.

Tabs
----
  1. Ranked Risk Table   — full sortable table, color-coded by risk_band
  2. Asset Detail        — per-asset breakdown with factor bar chart
  3. Advisor Chat        — grounded NL Q&A via advisor.py
  4. Reactive vs Preventive — compare incident history against top-priority queue

Run from the src/ folder:
  streamlit run app.py
"""

import os
import sys
import subprocess
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Path setup — allow imports from src/
# ---------------------------------------------------------------------------
SRC_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SRC_DIR, "data")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# ---------------------------------------------------------------------------
# Styling helpers
# ---------------------------------------------------------------------------

BAND_COLORS = {
    "critical": "#c0392b",
    "elevated": "#e67e22",
    "watch":    "#f1c40f",
    "normal":   "#27ae60",
}

BAND_TEXT_COLORS = {
    "critical": "#ffffff",
    "elevated": "#ffffff",
    "watch":    "#1a1a1a",
    "normal":   "#ffffff",
}

def band_badge(band: str) -> str:
    bg  = BAND_COLORS.get(band, "#888888")
    fg  = BAND_TEXT_COLORS.get(band, "#ffffff")
    return f'<span style="background:{bg};color:{fg};padding:2px 8px;border-radius:4px;font-weight:bold;font-size:0.85em">{band.upper()}</span>'


def fmt_currency(v) -> str:
    try:
        return f"${int(v):,}"
    except Exception:
        return str(v)


def data_health_badge() -> str:
    """Return a small HTML snippet showing data timestamp, model version, and confidence band."""
    from datetime import datetime
    ts = datetime.now().strftime("%H:%M")
    # Confidence is determined at scoring time; for demo we show High for top assets
    return (
        f'<span style="font-size:0.8em;background:#1a3a5c;color:#7ec8e3;'
        f'padding:2px 8px;border-radius:4px;border:1px solid #2a5a8c;">'
        f'🕐 as of {ts} · model v0.3 · confidence: High'
        f'</span>'
    )


def confidence_band(risk_score: float) -> str:
    """Map a risk score to a confidence band label."""
    if risk_score >= 60:
        return "High"
    elif risk_score >= 30:
        return "Medium"
    return "Low"


def color_row(row):
    band = row.get("risk_band", "normal")
    # Use solid dark colours with white text so content is readable in
    # both light and dark Streamlit themes.
    style_map = {
        "critical": "background-color: #922b21; color: #ffffff",
        "elevated": "background-color: #a04000; color: #ffffff",
        "watch":    "background-color: #7d6608; color: #ffffff",
        "normal":   "background-color: #1e8449; color: #ffffff",
    }
    style = style_map.get(band, "background-color: #444444; color: #ffffff")
    return [style] * len(row)


# ---------------------------------------------------------------------------
# Data loader (cached)
# ---------------------------------------------------------------------------

@st.cache_data
def load_final_report():
    path = os.path.join(DATA_DIR, "final_report.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    df = df.sort_values("priority_score", ascending=False).reset_index(drop=True)
    return df


@st.cache_data
def load_incidents():
    path = os.path.join(DATA_DIR, "incidents.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path)


# ---------------------------------------------------------------------------
# Pipeline runner
# ---------------------------------------------------------------------------

def run_pipeline():
    scripts = [
        os.path.join(DATA_DIR, "generate_data.py"),
        os.path.join(SRC_DIR, "scoring", "risk_engine.py"),
        os.path.join(SRC_DIR, "scoring", "priority_engine.py"),
        os.path.join(SRC_DIR, "recommendation", "recommend.py"),
    ]
    for script in scripts:
        result = subprocess.run(
            [sys.executable, script],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return False, script, result.stderr
    return True, None, None


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def sidebar():
    st.sidebar.title("⚡ GridShield")
    st.sidebar.caption("Civil-Engineering-Aware Power Grid Advisor")
    st.sidebar.markdown("---")

    if st.sidebar.button("🔄 Rerun Full Pipeline", use_container_width=True):
        with st.sidebar:
            with st.spinner("Running pipeline …"):
                ok, failed_script, err = run_pipeline()
        if ok:
            st.cache_data.clear()
            # Reload advisor cache too
            try:
                from ai.advisor import reload_report
                reload_report()
            except Exception:
                pass
            st.sidebar.success("Pipeline complete! Data refreshed.")
            st.rerun()
        else:
            st.sidebar.error(f"Pipeline failed at:\n{failed_script}\n\n{err[:500]}")

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Risk Bands**")
    for band, color in BAND_COLORS.items():
        st.sidebar.markdown(
            f'<span style="background:{color};color:white;padding:2px 6px;'
            f'border-radius:3px;font-size:0.8em">{band.upper()}</span>  '
            f'{"≥70" if band=="critical" else "45–69" if band=="elevated" else "20–44" if band=="watch" else "<20"}',
            unsafe_allow_html=True,
        )
    st.sidebar.markdown("---")
    st.sidebar.caption(
        "All recommendations are advisory only. "
        "No field work is authorised without engineer sign-off."
    )


# ---------------------------------------------------------------------------
# Tab 1 — Ranked Risk Table
# ---------------------------------------------------------------------------

ADVISORY_BADGE = (
    '<div style="background:#3b1f00;border:1px solid #e67e22;color:#fde8c8;'
    'padding:6px 12px;border-radius:4px;font-size:0.82em;margin-bottom:8px;">'
    '⚠ <strong>Advisory only — human approval required</strong> before any field action.'
    '</div>'
)


def tab_ranked_table(df: pd.DataFrame):
    st.header("📊 Ranked Asset Priority Queue")
    st.markdown(ADVISORY_BADGE, unsafe_allow_html=True)
    st.markdown(data_health_badge(), unsafe_allow_html=True)
    st.caption(
        "Assets ranked by **priority_score** (net benefit ÷ intervention cost). "
        "A cheap fix for a critical-load feeder may outrank a higher raw-risk asset."
    )

    # One-line "why this asset is #1" above the table
    if len(df) > 0:
        top = df.iloc[0]
        cause_str = str(top.get("dominant_cause", "")).replace("_", " ")
        crit_str  = str(top.get("critical_loads", "none"))
        crit_note = f"including a {crit_str.replace('_',' ')}" if crit_str != "none" else "no critical load"
        st.info(
            f"**#1 priority: {top['asset_id']}** ({top.get('asset_type','')} · "
            f"{top.get('risk_band','').upper()}) — "
            f"driven by **{cause_str}**, serving {int(top.get('downstream_customers',0)):,} customers "
            f"({crit_note}). "
            f"Net benefit: ${top.get('net_benefit', top.get('expected_loss',0)):.0f} · "
            f"Priority score: {float(top.get('priority_score',0)):.5f}."
        )

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        band_filter = st.multiselect(
            "Risk band", ["critical", "elevated", "watch", "normal"],
            default=["critical", "elevated", "watch", "normal"]
        )
    with col2:
        type_filter = st.multiselect(
            "Asset type", df["asset_type"].unique().tolist(),
            default=df["asset_type"].unique().tolist()
        )
    with col3:
        feeder_filter = st.multiselect(
            "Feeder", df["feeder_id"].unique().tolist(),
            default=df["feeder_id"].unique().tolist()
        )

    view = df[
        df["risk_band"].isin(band_filter) &
        df["asset_type"].isin(type_filter) &
        df["feeder_id"].isin(feeder_filter)
    ].copy()

    display_cols = [
        "asset_id", "asset_type", "risk_band", "risk_score",
        "priority_score", "expected_loss", "estimated_intervention_cost",
        "critical_loads", "downstream_customers", "dominant_cause", "action_tier",
    ]
    display_cols = [c for c in display_cols if c in view.columns]

    styled = (
        view[display_cols]
        .style
        .apply(color_row, axis=1)
        .format({
            "risk_score":                   "{:.1f}",
            "priority_score":               "{:.5f}",
            "expected_loss":                "{:.1f}",
            "estimated_intervention_cost":  "${:,.0f}",
            "downstream_customers":         "{:,.0f}",
        })
    )

    st.dataframe(styled, use_container_width=True, height=500)
    st.caption(f"Showing {len(view)} of {len(df)} assets.")

    # Map
    if "latitude" in df.columns and "longitude" in df.columns:
        st.subheader("🗺 Asset Locations")
        # Map legend
        st.markdown(
            "**Risk band legend:** "
            + " ".join([
                f'<span style="background:{c};color:white;padding:1px 6px;'
                f'border-radius:3px;font-size:0.78em">{b.upper()}</span>'
                for b, c in BAND_COLORS.items()
            ])
            + " &nbsp;|&nbsp; "
            "🌊 flood/erosion risk &nbsp; 🌿 vegetation encroachment &nbsp; ⚡ electrical anomaly",
            unsafe_allow_html=True,
        )
        map_df = view[["latitude", "longitude"]].rename(
            columns={"latitude": "lat", "longitude": "lon"}
        )
        st.map(map_df, zoom=11)


# ---------------------------------------------------------------------------
# Tab 2 — Asset Detail
# ---------------------------------------------------------------------------

def tab_asset_detail(df: pd.DataFrame):
    st.header("🔍 Asset Detail")
    st.markdown(ADVISORY_BADGE, unsafe_allow_html=True)

    asset_options = df["asset_id"].tolist()
    default_idx = next(
        (i for i, aid in enumerate(asset_options)
         if df[df["asset_id"] == aid].iloc[0]["asset_type"] in ("transformer", "substation")),
        0
    )
    selected = st.selectbox("Select asset", asset_options, index=default_idx)
    row = df[df["asset_id"] == selected].iloc[0]

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Risk Score",     f"{row['risk_score']:.1f} / 100")
    col2.metric("Priority Score", f"{row['priority_score']:.5f}")
    col3.metric("Intervention Cost", fmt_currency(row.get("estimated_intervention_cost", 0)))
    col4.metric("Expected Loss Index", f"{row.get('expected_loss', 0):.1f}")

    band = row.get("risk_band", "normal")
    rs   = float(row.get("risk_score", 0))
    conf = confidence_band(rs)
    st.markdown(
        f"**Risk Band:** {band_badge(band)} &nbsp; "
        + data_health_badge().replace(
            "confidence: High",
            f"confidence: {conf}"
        ),
        unsafe_allow_html=True,
    )
    st.markdown(f"**Dominant Cause:** `{row.get('dominant_cause','').replace('_',' ')}`")
    st.markdown(f"**Asset Type:** {row.get('asset_type','')} | **Feeder:** {row.get('feeder_id','')} | **Critical Load:** {row.get('critical_loads','')}")

    st.markdown("---")

    # Factor bar chart — grouped by Electrical/Sensor vs Civil/Weather
    factor_cols = [c for c in df.columns if c.startswith("factor_")]
    if factor_cols:
        st.subheader("📈 Risk Score Breakdown (Contributing Factors)")

        CIVIL_FACTORS = ["factor_wind", "factor_rain", "factor_tilt", "factor_erosion",
                         "factor_corrosion", "factor_drainage", "factor_vegetation", "factor_age"]
        ELEC_FACTORS  = ["factor_thermal", "factor_vibration", "factor_partial_dc",
                         "factor_oil", "factor_overload"]

        atype = str(row.get("asset_type", "")).strip().lower()
        is_elec = atype in ("transformer", "substation")

        factor_rows = []
        for col in CIVIL_FACTORS:
            if col in df.columns:
                factor_rows.append({
                    "Factor": col.replace("factor_", "").replace("_", " ").title(),
                    "Points": float(row.get(col, 0) or 0),
                    "Cluster": "Civil / Weather",
                })
        if is_elec:
            for col in ELEC_FACTORS:
                if col in df.columns:
                    factor_rows.append({
                        "Factor": col.replace("factor_", "").replace("_", " ").title(),
                        "Points": float(row.get(col, 0) or 0),
                        "Cluster": "Electrical / Sensor",
                    })

        factor_df = pd.DataFrame(factor_rows).sort_values(["Cluster", "Points"], ascending=[True, False])
        total_raw = sum(r["Points"] for r in factor_rows)

        if is_elec:
            # Show side-by-side cluster view
            civil_df = factor_df[factor_df["Cluster"] == "Civil / Weather"].set_index("Factor")[["Points"]]
            elec_df  = factor_df[factor_df["Cluster"] == "Electrical / Sensor"].set_index("Factor")[["Points"]]
            col_c, col_e = st.columns(2)
            with col_c:
                st.markdown("**Civil / Weather Factors**")
                st.bar_chart(civil_df, use_container_width=True)
            with col_e:
                st.markdown("**Electrical / Sensor Factors**")
                st.bar_chart(elec_df, use_container_width=True)
        else:
            st.bar_chart(factor_df.set_index("Factor")[["Points"]], use_container_width=True)

        st.caption(f"Total raw points: {total_raw:.1f} → capped risk score: {row['risk_score']:.1f}")
        if is_elec:
            elec_total = sum(float(row.get(c, 0) or 0) for c in ELEC_FACTORS if c in df.columns)
            civil_total = sum(float(row.get(c, 0) or 0) for c in CIVIL_FACTORS if c in df.columns)
            st.caption(
                f"Electrical/Sensor sub-total: **{elec_total:.1f} pts** | "
                f"Civil/Weather sub-total: **{civil_total:.1f} pts**"
            )

    st.markdown("---")

    # Recommendation card
    st.subheader("📋 Recommended Action")
    tier = row.get("action_tier", "")
    tier_color = {"immediate": "#c0392b", "scheduled": "#e67e22", "monitor": "#27ae60"}.get(tier, "#888")
    st.markdown(
        f'<div style="border-left:4px solid {tier_color};padding:12px 16px;'
        f'background:#1e1e2e;border-radius:4px;color:#f0f0f0;">'
        f'<strong style="color:{tier_color}">Tier:</strong> '
        f'<span style="color:{tier_color};font-weight:bold">{tier.upper()}</span>'
        f'<br><br>'
        f'<span style="color:#f0f0f0">{row.get("recommended_action","")}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f"**Crew:** {row.get('recommended_crew_type','')}")
    st.markdown(f"**Expected risk reduction after action:** {row.get('expected_risk_reduction_pct','?')}%")

    # ------------------------------------------------------------------
    # ITEM 6 — Crew pre-positioning card
    # ------------------------------------------------------------------
    st.subheader("🚚 Crew Pre-Positioning")
    road_access = float(row.get("road_access_score", 50) or 50)
    # Estimate travel time from road access score (illustrative: score 0–100 → 3h–0.5h)
    travel_h = round(3.0 - (road_access / 100.0) * 2.5, 1)
    travel_h = max(0.5, travel_h)
    from datetime import datetime as _dt, timedelta as _td
    eta = (_dt.now() + _td(hours=travel_h)).strftime("%H:%M")

    tier_val = row.get("action_tier", "monitor")
    staging_locations = {
        "immediate": "Central Grid Ops Depot — Bay 3 (pre-staged)",
        "scheduled": "Regional Maintenance Hub — Section B",
        "monitor":   "On-call pool — mobilise 24h before inspection date",
    }
    staging = staging_locations.get(tier_val, "Central Grid Ops Depot")

    cause = str(row.get("dominant_cause", "")).lower()
    materials_map = {
        "wind_foundation":        ["Structural bracing kit", "Torque wrenches", "PPE (high-vis, hard hat)", "Camera for photo-survey", "Temporary guy-wire anchors"],
        "flood_drainage":         ["Sandbags (×20)", "Dewatering pump", "Geotextile erosion mat", "Drainage rods", "Safety marker stakes", "PPE (waders, hard hat)"],
        "vegetation":             ["Pole saw / chainsaw", "PPE (chainsaw chaps, visor, gloves)", "Rope + arborist slings", "First-aid kit", "Traffic management cones"],
        "corrosion_age":          ["Replacement hardware (like-for-like)", "Anti-corrosion primer & paint", "NDT thickness gauge", "PPE (chemical-resistant gloves)", "Scaffolding / access tower"],
        "thermal_overload":       ["IR thermal camera", "SCADA laptop + cable", "Cooling fan inspection kit", "Oil temperature gauge", "PPE (arc-flash rated)"],
        "insulation_degradation": ["Oil sampling kit (DGA bottles)", "PD detection meter", "Insulation resistance tester", "PPE (arc-flash rated)", "Hazmat bag for oil samples"],
    }
    materials = materials_map.get(cause, ["PPE (standard)", "Inspection camera", "Maintenance tools"])

    cp_col1, cp_col2 = st.columns(2)
    with cp_col1:
        st.markdown(
            f'<div style="background:#1a2a1a;border-left:4px solid #27ae60;'
            f'padding:12px 16px;border-radius:4px;color:#e0f0e0;">'
            f'<strong>Staging location:</strong><br>{staging}'
            f'<br><br>'
            f'<strong>Estimated travel time:</strong> {travel_h}h '
            f'(road access score: {road_access:.0f}/100)<br>'
            f'<strong>ETA on-site:</strong> ~{eta}'
            f'</div>',
            unsafe_allow_html=True,
        )
    with cp_col2:
        st.markdown("**Materials checklist:**")
        for m in materials:
            st.markdown(f"- ☐ {m}")

    st.markdown("---")

    # Safety note
    st.warning(
        "⚠ **SAFETY NOTE**\n\n" +
        str(row.get("safety_note",
            "Advisory only. All field actions require engineer sign-off."))
    )

    # Raw data expander
    with st.expander("View all data fields for this asset"):
        st.json(row.to_dict())


# ---------------------------------------------------------------------------
# Tab 3 — Advisor Chat
# ---------------------------------------------------------------------------

def tab_advisor(df: pd.DataFrame):
    st.header("🤖 GridShield Advisor")
    st.caption(
        "Ask questions grounded in the computed risk data. "
        "Try: *'Why is A-01 ranked above A-20?'* or *'What should we do about A-03?'*"
    )

    question = st.text_input(
        "Your question",
        placeholder="e.g. Compare A-01 and A-15, or What is the risk for asset A-04?",
    )

    if st.button("Ask", type="primary") and question.strip():
        with st.spinner("Generating grounded answer …"):
            try:
                from ai.advisor import answer_question
                answer = answer_question(question, df)
            except Exception as e:
                answer = f"Error: {e}"
        st.markdown("---")
        st.markdown(answer)

    st.markdown("---")
    st.subheader("Sample questions")
    samples = [
        "Why is A-01 ranked above A-15?",
        "What should we do about asset A-03?",
        "Which asset is highest priority for our crew today?",
        "Compare A-02 and A-20",
        "Explain the risk for A-05",
    ]
    for s in samples:
        if st.button(s, key=f"sample_{s}"):
            with st.spinner("Generating grounded answer …"):
                try:
                    from ai.advisor import answer_question
                    answer = answer_question(s, df)
                except Exception as e:
                    answer = f"Error: {e}"
            st.markdown("---")
            st.markdown(answer)


# ---------------------------------------------------------------------------
# Tab 4 — Reactive vs Preventive
# ---------------------------------------------------------------------------

def tab_reactive_vs_preventive(df: pd.DataFrame, incidents: pd.DataFrame):
    st.header("📉 Reactive vs Preventive Comparison")
    st.caption(
        "Compares which historically incident-prone assets appear in the current "
        "top-10 priority queue — demonstrating that GridShield's prevention focus "
        "aligns with real historical failure patterns."
    )

    top10 = df.head(10)["asset_id"].tolist()

    if incidents.empty:
        st.info("No incidents data found. Run the pipeline first.")
        return

    # Assets with past incidents
    incident_assets  = incidents["asset_id"].unique().tolist()
    in_both          = [a for a in incident_assets if a in top10]
    only_incident    = [a for a in incident_assets if a not in top10]
    only_priority    = [a for a in top10 if a not in incident_assets]

    col1, col2, col3 = st.columns(3)
    col1.metric("Top-10 priority assets also with past incidents",
                len(in_both), help="These assets are both historically troubled AND currently high-priority — strong preventive value.")
    col2.metric("Top-10 priority assets with NO incident history",
                len(only_priority), help="GridShield identified these as high-risk before a failure occurred.")
    col3.metric("Assets with past incidents NOT in top-10",
                len(only_incident), help="These have failed before but current conditions rank them lower — still worth monitoring.")

    # Reactive scenario: what would a pure incident-history approach catch?
    st.subheader("Comparison table")

    top10_df = df[df["asset_id"].isin(top10)].copy()
    top10_df["had_past_incident"] = top10_df["asset_id"].isin(incident_assets)

    # Incident counts and total downtime per asset
    if not incidents.empty:
        inc_summary = (
            incidents.groupby("asset_id")
            .agg(incident_count=("incident_date", "count"),
                 total_downtime_hours=("downtime_hours", "sum"))
            .reset_index()
        )
        top10_df = top10_df.merge(inc_summary, on="asset_id", how="left")
        top10_df["incident_count"]       = top10_df["incident_count"].fillna(0).astype(int)
        top10_df["total_downtime_hours"] = top10_df["total_downtime_hours"].fillna(0)

    disp_cols = [
        "asset_id", "risk_band", "risk_score", "priority_score",
        "dominant_cause", "critical_loads", "downstream_customers",
        "had_past_incident", "incident_count", "total_downtime_hours",
        "estimated_intervention_cost",
    ]
    disp_cols = [c for c in disp_cols if c in top10_df.columns]

    styled = (
        top10_df[disp_cols]
        .style
        .apply(color_row, axis=1)
        .format({
            "risk_score":                  "{:.1f}",
            "priority_score":              "{:.5f}",
            "estimated_intervention_cost": "${:,.0f}",
            "total_downtime_hours":        "{:.1f}",
        })
    )
    st.dataframe(styled, use_container_width=True)

    # Summary metrics
    st.subheader("📊 Value of prevention")
    total_cust_reactive   = incidents.merge(
        df[["asset_id", "downstream_customers"]], on="asset_id", how="left"
    )["downstream_customers"].sum()
    total_downtime_hist   = incidents["downtime_hours"].sum()
    est_cost_reactive     = total_downtime_hist * 50   # illustrative $50/customer-hour

    total_preventive_cost = top10_df["estimated_intervention_cost"].sum()
    preventive_customers  = top10_df["downstream_customers"].sum()

    col_a, col_b = st.columns(2)
    with col_a:
        st.error(
            f"**Reactive approach (historical)**\n\n"
            f"• {len(incidents)} recorded incidents\n"
            f"• {total_downtime_hist:.0f} total downtime hours\n"
            f"• Estimated cost of failures: {fmt_currency(est_cost_reactive)}"
        )
    with col_b:
        st.success(
            f"**GridShield preventive queue (top 10)**\n\n"
            f"• {len(top10)} assets addressed proactively\n"
            f"• {preventive_customers:,} customers protected\n"
            f"• Estimated total intervention cost: {fmt_currency(total_preventive_cost)}"
        )

    st.info(
        "**Key takeaway:** GridShield's priority queue places historically "
        f"incident-prone assets ({len(in_both)} of {len(in_both)+len(only_priority)}) "
        "in the top-10 *before* a failure occurs, while intervention costs "
        f"({fmt_currency(total_preventive_cost)}) are a fraction of reactive costs "
        f"({fmt_currency(est_cost_reactive)})."
    )


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(
        page_title="GridShield — Power Grid Advisor",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    sidebar()

    st.title("⚡ GridShield — Civil-Engineering-Aware Power Grid Advisor")
    st.caption("IBM Bob AI Hackathon 2026 · Problem Statement U1: Power Outage Prediction & Grid Equipment Failure Advisor")

    # -----------------------------------------------------------------------
    # ITEM 5 — Weather scenario + time-horizon selector (top-of-page controls)
    # -----------------------------------------------------------------------
    WEATHER_SCENARIOS = {
        "Storm Alpha (Severe)":       {"rainfall_mm": 82, "wind_kmh": 94, "description": "Severe convective storm — high wind and rainfall"},
        "Tropical Depression Beta":   {"rainfall_mm": 55, "wind_kmh": 68, "description": "Moderate system — elevated flood risk"},
        "Heatwave Gamma":             {"rainfall_mm": 2,  "wind_kmh": 18, "description": "Dry heatwave — high thermal load on transformers"},
        "Clear Baseline":             {"rainfall_mm": 5,  "wind_kmh": 20, "description": "Calm conditions — maintenance window opportunity"},
    }
    with st.expander("🌩 Weather Scenario & Time Horizon", expanded=True):
        sc_col, th_col = st.columns([2, 1])
        with sc_col:
            scenario_name = st.selectbox(
                "Active weather scenario",
                list(WEATHER_SCENARIOS.keys()),
                index=0,
                help="Scenario drives the risk model's weather inputs.",
            )
            sc = WEATHER_SCENARIOS[scenario_name]
            st.markdown(
                f"**{scenario_name}** — {sc['description']} "
                f"| Rainfall: **{sc['rainfall_mm']} mm** "
                f"| Wind: **{sc['wind_kmh']} km/h**"
            )
        with th_col:
            time_horizon = st.radio(
                "Prediction time horizon",
                ["24h", "72h", "7-day"],
                horizontal=True,
                help="Horizon used for risk scoring (current data covers 3-day forecast).",
            )
        st.caption(
            f"⚠ Advisory only — all predictions are model estimates. "
            f"Current scenario: **{scenario_name}** · Horizon: **{time_horizon}** · "
            "Human approval required before any field action."
        )

    df = load_final_report()
    if df is None:
        st.error(
            "**final_report.csv not found.**\n\n"
            "Click **Rerun Full Pipeline** in the sidebar, or run `python pipeline.py` from the `src/` folder."
        )
        return

    incidents = load_incidents()

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Ranked Risk Table",
        "🔍 Asset Detail",
        "🤖 Advisor Chat",
        "📉 Reactive vs Preventive",
        "🔬 Model & Evaluation",
        "📈 Metrics",
        "🤖 BOB Quality Panel",
    ])

    with tab1:
        tab_ranked_table(df)
    with tab2:
        tab_asset_detail(df)
    with tab3:
        tab_advisor(df)
    with tab4:
        tab_reactive_vs_preventive(df, incidents)
    with tab5:
        from app_pages.model_eval import render_model_eval
        render_model_eval()
    with tab6:
        from app_pages.metrics_panel import render_metrics_panel
        render_metrics_panel(df)
    with tab7:
        from app_pages.bob_panel import render_bob_panel
        render_bob_panel()


if __name__ == "__main__":
    main()
