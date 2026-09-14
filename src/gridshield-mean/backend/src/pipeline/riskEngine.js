/**
 * riskEngine.js
 * -------------
 * Port of risk_engine.py — exact same factor formulas, same dominant-cause logic.
 * Input:  merged row object { ...asset, ...weather, ...terrain, ...vegetation, ...topology }
 * Output: factor scores + risk_score + dominant_cause
 */

"use strict";

function scale(value, threshold, ceiling, maxPts) {
  if (value <= threshold) return 0;
  if (value >= ceiling)   return maxPts;
  return parseFloat((maxPts * (value - threshold) / (ceiling - threshold)).toFixed(2));
}

function factorWind(row) {
  return scale(row.wind_gust_kmh, 60, 100, 20);
}

function factorRain(row) {
  const rainPts  = scale(row.rainfall_mm,    40, 100, 15);
  const floodPts = scale(row.flood_depth_cm,  0,  20,  5);
  return Math.min(20, parseFloat((rainPts + floodPts).toFixed(2)));
}

function factorTilt(row) {
  return scale(row.tilt_deg, 3, 7, 15);
}

function factorErosion(row) {
  return scale(row.erosion_index, 60, 95, 15);
}

function factorCorrosion(row) {
  return scale(row.corrosion_score, 60, 95, 15);
}

function factorDrainage(row) {
  const inverted = Math.max(0, 40 - parseFloat(row.drainage_score));
  return scale(inverted, 0, 40, 10);
}

function factorVegetation(row) {
  const inverted = Math.max(0, 40 - parseFloat(row.clearance_score));
  return scale(inverted, 0, 40, 15);
}

function factorAge(row) {
  let pts = 0;
  if (row.age_years > 20) {
    pts += scale(row.age_years, 20, 50, 6);
  }
  try {
    const last = new Date(row.last_maintenance_date);
    const monthsSince = (Date.now() - last.getTime()) / (1000 * 60 * 60 * 24 * 30.4);
    if (monthsSince > 12) {
      pts += scale(monthsSince, 12, 36, 4);
    }
  } catch {
    pts += 4;
  }
  return parseFloat(Math.min(10, pts).toFixed(2));
}

function dominantCause(factors) {
  const groups = {
    wind_foundation: factors.factor_wind + factors.factor_tilt,
    flood_drainage:  factors.factor_rain + factors.factor_erosion + factors.factor_drainage,
    vegetation:      factors.factor_vegetation,
    corrosion_age:   factors.factor_corrosion + factors.factor_age,
  };
  return Object.entries(groups).sort((a, b) => b[1] - a[1])[0][0];
}

function scoreRow(row) {
  const factors = {
    factor_wind:       factorWind(row),
    factor_rain:       factorRain(row),
    factor_tilt:       factorTilt(row),
    factor_erosion:    factorErosion(row),
    factor_corrosion:  factorCorrosion(row),
    factor_drainage:   factorDrainage(row),
    factor_vegetation: factorVegetation(row),
    factor_age:        factorAge(row),
  };
  const rawScore = Object.values(factors).reduce((s, v) => s + v, 0);
  const risk_score   = parseFloat(Math.min(100, rawScore).toFixed(1));
  const dominant_cause = dominantCause(factors);
  return { ...factors, risk_score, dominant_cause };
}

module.exports = { scoreRow };
