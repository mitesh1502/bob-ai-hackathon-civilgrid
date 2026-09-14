/**
 * recommendEngine.js
 * ------------------
 * Port of recommend.py — same action table, same risk bands, same safety note.
 */

"use strict";

const SAFETY_NOTE =
  "ADVISORY ONLY — This system does not authorise any field work. " +
  "No switching, breaker operation, energisation, de-energisation, " +
  "excavation, or work on or near live equipment is permitted without " +
  "a written work order reviewed and signed off by a qualified licensed " +
  "engineer in accordance with applicable utility safety procedures.";

const RISK_BANDS = [
  [70, "critical"],
  [45, "elevated"],
  [20, "watch"],
  [0,  "normal"],
];

function riskBand(risk_score) {
  for (const [threshold, label] of RISK_BANDS) {
    if (risk_score >= threshold) return label;
  }
  return "normal";
}

const ACTION_TABLE = [
  {
    cause:       "wind_foundation",
    action_tier: "immediate",
    action:
      "Conduct urgent visual inspection of foundation integrity and structural tilt. " +
      "Arrange engineer-verified bracing assessment; if tilt exceeds safe tolerance, " +
      "prepare replacement materials and stage crew for post-storm intervention. " +
      "Do NOT approach or touch the structure during active high-wind conditions.",
    risk_reduction: 55,
    crew: "Structural/civil engineer + two-person utility crew",
  },
  {
    cause:       "flood_drainage",
    action_tier: "scheduled",
    action:
      "Inspect and clear all blocked drainage channels within 10 m of the asset. " +
      "Check for evidence of scour or foundation undermining; photograph and report. " +
      "Apply temporary erosion-control measures (sandbags, geotextile) if scour is observed. " +
      "Stage dewatering equipment if significant flooding is forecast. " +
      "Defer foundation stabilisation work until water has receded and site is safe.",
    risk_reduction: 48,
    crew: "Civil/drainage engineer + maintenance crew",
  },
  {
    cause:       "vegetation",
    action_tier: "scheduled",
    action:
      "Arrange targeted vegetation trimming to restore safe conductor clearance. " +
      "Inspect conductor for signs of abrasion or tracking damage after trimming. " +
      "Log encroaching tree species and height for future vegetation-management schedule. " +
      "Trimming must be carried out by a qualified arborist with utility line clearance training; " +
      "no cutting within minimum approach distance without engineer approval.",
    risk_reduction: 60,
    crew: "Qualified arborist with utility clearance certification",
  },
  {
    cause:       "corrosion_age",
    action_tier: "immediate",
    action:
      "Escalate to engineering team for detailed condition assessment. " +
      "Review maintenance history and compare against asset life expectancy. " +
      "Prepare a like-for-like replacement proposal and cost estimate. " +
      "Stage materials and arrange crew availability before next forecast severe-weather event. " +
      "Do not defer beyond current inspection cycle given combined corrosion and age indicators.",
    risk_reduction: 70,
    crew: "Asset management engineer + specialist replacement crew",
  },
];

const DEFAULT_ACTION = {
  action_tier: "monitor",
  action:
    "Schedule routine inspection; review all available condition data and " +
    "update asset record. Consult engineering team if any deterioration is observed.",
  risk_reduction: 20,
  crew: "Maintenance crew",
};

function lookupAction(dominant_cause) {
  return ACTION_TABLE.find((e) => e.cause === dominant_cause) || { cause: dominant_cause, ...DEFAULT_ACTION };
}

function buildRecommendation(row) {
  const action = lookupAction(String(row.dominant_cause || "").trim().toLowerCase());
  return {
    recommended_action:          action.action,
    action_tier:                 action.action_tier,
    expected_risk_reduction_pct: action.risk_reduction,
    recommended_crew_type:       action.crew,
    risk_band:                   riskBand(parseFloat(row.risk_score || 0)),
    safety_note:                 SAFETY_NOTE,
  };
}

module.exports = { buildRecommendation, riskBand, SAFETY_NOTE };
