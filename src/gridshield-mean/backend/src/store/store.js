/**
 * store.js
 * --------
 * In-memory data store. Runs the full pipeline once on startup.
 * No MongoDB or Mongoose required.
 */

"use strict";

const { generateAll }         = require("../pipeline/generateData");
const { scoreRow: riskScore } = require("../pipeline/riskEngine");
const { scoreRow: prioScore } = require("../pipeline/priorityEngine");
const { buildRecommendation } = require("../pipeline/recommendEngine");

let _assets    = [];
let _incidents = [];

function runPipeline() {
  console.log("GridShield pipeline starting…");
  const { assets, weather, terrain, vegetation, topology, incidents } = generateAll();

  // Aggregate weather: max per asset across 3-day forecast
  const weatherMap = {};
  weather.forEach((w) => {
    if (!weatherMap[w.asset_id]) weatherMap[w.asset_id] = { wind_gust_kmh: 0, rainfall_mm: 0, flood_depth_cm: 0 };
    const m = weatherMap[w.asset_id];
    m.wind_gust_kmh  = Math.max(m.wind_gust_kmh,  w.wind_gust_kmh);
    m.rainfall_mm    = Math.max(m.rainfall_mm,    w.rainfall_mm);
    m.flood_depth_cm = Math.max(m.flood_depth_cm, w.flood_depth_cm);
  });

  const terrainMap  = Object.fromEntries(terrain.map((r) => [r.asset_id, r]));
  const vegMap      = Object.fromEntries(vegetation.map((r) => [r.asset_id, r]));
  const topoMap     = Object.fromEntries(topology.map((r) => [r.asset_id, r]));

  _assets = assets.map((a) => {
    const merged = {
      ...a,
      ...(weatherMap[a.asset_id]  || {}),
      ...(terrainMap[a.asset_id]  || {}),
      ...(vegMap[a.asset_id]      || {}),
      ...(topoMap[a.asset_id]     || {}),
    };
    const risk = riskScore(merged);
    const prio = prioScore({ ...merged, ...risk });
    const rec  = buildRecommendation({ ...merged, ...risk });
    return { ...merged, ...risk, ...prio, ...rec };
  });

  // Sort by priority_score descending
  _assets.sort((a, b) => b.priority_score - a.priority_score);
  _incidents = incidents;

  console.log(`  Loaded ${_assets.length} assets, ${_incidents.length} incidents`);
  const top3 = _assets.slice(0, 3);
  top3.forEach((a) => console.log(`    ${a.asset_id}  risk=${a.risk_score}  priority=${a.priority_score.toFixed(4)}  cause=${a.dominant_cause}`));
  console.log("Pipeline complete.\n");
}

function getAssets()    { return _assets; }
function getIncidents() { return _incidents; }
function getAsset(id)   { return _assets.find((a) => a.asset_id === id) || null; }

function getStats() {
  const critical  = _assets.filter(a => a.risk_band === "critical").length;
  const elevated  = _assets.filter(a => a.risk_band === "elevated").length;
  const watch     = _assets.filter(a => a.risk_band === "watch").length;
  const normal    = _assets.filter(a => a.risk_band === "normal").length;
  const immediate = _assets.filter(a => a.action_tier === "immediate").length;
  const totalCustomers = _assets.reduce((s, a) => s + a.downstream_customers, 0);
  return {
    total: _assets.length, critical, elevated, watch, normal,
    immediate, totalCustomers, incidentCount: _incidents.length,
  };
}

module.exports = { runPipeline, getAssets, getIncidents, getAsset, getStats };
