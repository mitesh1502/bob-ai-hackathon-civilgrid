/**
 * advisor.js
 * ----------
 * Port of advisor.py — template-based NL advisor grounded entirely in DB data.
 * No free-form generation; every sentence is built from real field values.
 */

"use strict";

const { SAFETY_NOTE } = require("../pipeline/recommendEngine");

// ── Asset ID detection ────────────────────────────────────────────────────────
const ID_PATTERNS = [
  /\bA-(\d{1,2})\b/gi,
  /\bA(\d{1,2})\b/gi,
  /\basset[-\s]*(\d{1,2})\b/gi,
];

function detectAssetIds(question, allIds) {
  const found = new Set();
  for (const pattern of ID_PATTERNS) {
    for (const m of question.matchAll(pattern)) {
      const candidate = `A-${String(parseInt(m[1])).padStart(2, "0")}`;
      if (allIds.includes(candidate)) found.add(candidate);
    }
  }
  // Also verbatim check
  const q = question.toUpperCase();
  allIds.forEach((id) => { if (q.includes(id.toUpperCase())) found.add(id); });
  return [...found].sort();
}

// ── Formatters ────────────────────────────────────────────────────────────────
function fmtCurrency(v) { return `$${Number(v).toLocaleString()}`; }
function fmtScore(v, dp = 1) { return Number(v).toFixed(dp); }

// ── Single-asset summary ──────────────────────────────────────────────────────
function assetSummary(a) {
  const redundancyNote =
    a.redundancy === true || a.redundancy === "true" || a.redundancy === "True"
      ? "This feeder has a redundant path, which reduces expected customer impact by 40%."
      : "This feeder has NO redundancy — a failure here directly affects all downstream customers.";

  const critNote = a.critical_loads !== "none"
    ? ` including a ${String(a.critical_loads).replace("_", " ")}`
    : "";

  return (
    `Asset ${a.asset_id} is a ${a.asset_type} rated ${String(a.risk_band).toUpperCase()} risk ` +
    `(risk score ${fmtScore(a.risk_score)}/100, priority score ${fmtScore(a.priority_score, 4)}).\n\n` +
    `Primary concern: ${String(a.dominant_cause).replace(/_/g, " ")}.\n\n` +
    `It serves ${Number(a.downstream_customers).toLocaleString()} downstream customers${critNote}, ` +
    `giving an expected loss index of ${fmtScore(a.expected_loss)}. ${redundancyNote}\n\n` +
    `Recommended action (${a.action_tier}, ${a.recommended_crew_type}):\n  ${a.recommended_action}\n\n` +
    `Estimated intervention cost: ${fmtCurrency(a.estimated_intervention_cost)}. ` +
    `Expected risk reduction after action: ${a.expected_risk_reduction_pct}%.\n`
  );
}

// ── Compare two assets ────────────────────────────────────────────────────────
function compareAssets(a, b) {
  const [higher, lower] = a.priority_score >= b.priority_score ? [a, b] : [b, a];
  const lines = [
    `Comparing ${a.asset_id} vs ${b.asset_id}:`,
    "",
    `  ${higher.asset_id} has a HIGHER priority score (${fmtScore(higher.priority_score, 4)}) ` +
      `vs ${lower.asset_id} (${fmtScore(lower.priority_score, 4)}).`,
    "",
    "Why?",
  ];

  if (parseFloat(higher.risk_score) < parseFloat(lower.risk_score)) {
    lines.push(
      `  Interesting case: ${lower.asset_id} actually has a higher raw risk score ` +
      `(${fmtScore(lower.risk_score)}) vs ${higher.asset_id} (${fmtScore(higher.risk_score)}), ` +
      `but ${higher.asset_id} is ranked higher because the cost-to-fix is lower ` +
      `(${fmtCurrency(higher.estimated_intervention_cost)} vs ${fmtCurrency(lower.estimated_intervention_cost)}) ` +
      `and/or it serves more exposed customers — making the intervention better value.`
    );
  } else {
    lines.push(
      `  ${higher.asset_id} has a higher raw risk score (${fmtScore(higher.risk_score)}/100) ` +
      `vs ${lower.asset_id} (${fmtScore(lower.risk_score)}/100).`
    );
  }

  const ch = String(higher.critical_loads);
  const cl = String(lower.critical_loads);
  if (higher.downstream_customers !== lower.downstream_customers) {
    lines.push(
      `  Customer exposure: ${higher.asset_id} serves ${Number(higher.downstream_customers).toLocaleString()} customers` +
      (ch !== "none" ? ` including a ${ch.replace("_", " ")}` : " (no critical loads)") +
      `; ${lower.asset_id} serves ${Number(lower.downstream_customers).toLocaleString()}` +
      (cl !== "none" ? ` including a ${cl.replace("_", " ")}` : " (no critical loads)") + "."
    );
  }
  lines.push(
    `  Primary cause for ${higher.asset_id}: ${String(higher.dominant_cause).replace(/_/g," ")}  |  Intervention cost: ${fmtCurrency(higher.estimated_intervention_cost)}`,
    `  Primary cause for ${lower.asset_id}: ${String(lower.dominant_cause).replace(/_/g," ")}  |  Intervention cost: ${fmtCurrency(lower.estimated_intervention_cost)}`,
    "",
    `Recommended action for ${higher.asset_id}: ${higher.recommended_action}`,
    "",
    `Recommended action for ${lower.asset_id}: ${lower.recommended_action}`
  );
  return lines.join("\n");
}

// ── Public API ────────────────────────────────────────────────────────────────
function answerQuestion(question, assets) {
  const allIds   = assets.map((a) => a.asset_id);
  const detected = detectAssetIds(question, allIds);

  let body;
  if (detected.length >= 2) {
    const a = assets.find((x) => x.asset_id === detected[0]);
    const b = assets.find((x) => x.asset_id === detected[1]);
    body = compareAssets(a, b);
  } else if (detected.length === 1) {
    const a = assets.find((x) => x.asset_id === detected[0]);
    body = assetSummary(a);
  } else {
    const top = assets[0];
    body =
      "No specific asset was identified in your question. " +
      "Here is a summary of the highest-priority asset in the current queue:\n\n" +
      assetSummary(top);
  }

  const safety = "\n\n---\n⚠ SAFETY REMINDER: " + SAFETY_NOTE;
  return body + safety;
}

module.exports = { answerQuestion };
