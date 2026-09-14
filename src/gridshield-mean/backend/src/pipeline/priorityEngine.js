/**
 * priorityEngine.js
 * -----------------
 * Port of priority_engine.py — same formulas, same constants.
 */

"use strict";

const CRITICAL_LOAD_MULTIPLIERS = {
  hospital:        3.0,
  water_treatment: 2.5,
  shelter:         2.0,
  none:            1.0,
};

const INTERVENTION_COSTS = {
  vegetation:      800,
  flood_drainage:  1200,
  wind_foundation: 4500,
  corrosion_age:   6000,
};

const REDUNDANCY_DISCOUNT = 0.40;

function criticalMultiplier(critical_loads) {
  const val = String(critical_loads).trim().toLowerCase();
  return CRITICAL_LOAD_MULTIPLIERS[val] || 1.0;
}

function computeExpectedLoss(row) {
  const mult = criticalMultiplier(row.critical_loads);
  let loss = (row.risk_score / 100) * row.downstream_customers * mult;
  if (row.redundancy === true || row.redundancy === "true" || row.redundancy === "True") {
    loss *= 1 - REDUNDANCY_DISCOUNT;
  }
  return parseFloat(loss.toFixed(2));
}

function interventionCost(dominant_cause) {
  return INTERVENTION_COSTS[String(dominant_cause).trim().toLowerCase()] || 3000;
}

function priorityScore(expected_loss, cost) {
  if (!cost) return 0;
  return parseFloat((expected_loss / cost).toFixed(6));
}

function scoreRow(row) {
  const critical_load_multiplier    = criticalMultiplier(row.critical_loads);
  const expected_loss               = computeExpectedLoss(row);
  const estimated_intervention_cost = interventionCost(row.dominant_cause);
  const priority_score_val          = priorityScore(expected_loss, estimated_intervention_cost);
  return {
    critical_load_multiplier,
    expected_loss,
    estimated_intervention_cost,
    priority_score: priority_score_val,
  };
}

module.exports = { scoreRow, INTERVENTION_COSTS, CRITICAL_LOAD_MULTIPLIERS };
