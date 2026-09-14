/**
 * seed.js
 * -------
 * Runs the full pipeline and saves all computed records to MongoDB.
 * Run once:  node src/pipeline/seed.js
 * The API server calls this automatically if the DB is empty.
 */

"use strict";

require("dotenv").config({ path: require("path").join(__dirname, "../../.env.local") });
// fallback to env.example values if no .env present
const MONGO_URI = process.env.MONGO_URI || "mongodb://localhost:27017/gridshield";

const mongoose  = require("mongoose");
const Asset     = require("../models/Asset");
const Incident  = require("../models/Incident");

const { generateAll }         = require("./generateData");
const { scoreRow: riskScore } = require("./riskEngine");
const { scoreRow: prioScore } = require("./priorityEngine");
const { buildRecommendation } = require("./recommendEngine");

async function runPipeline() {
  console.log("GridShield pipeline starting…");

  // 1. Generate synthetic data
  const { assets, weather, terrain, vegetation, topology, incidents } = generateAll();
  console.log(`  Generated ${assets.length} assets, ${incidents.length} incidents`);

  // 2. Build lookup maps for quick join
  // Weather: max per asset
  const weatherMap = {};
  weather.forEach((w) => {
    if (!weatherMap[w.asset_id]) {
      weatherMap[w.asset_id] = { wind_gust_kmh: 0, rainfall_mm: 0, flood_depth_cm: 0 };
    }
    weatherMap[w.asset_id].wind_gust_kmh  = Math.max(weatherMap[w.asset_id].wind_gust_kmh,  w.wind_gust_kmh);
    weatherMap[w.asset_id].rainfall_mm    = Math.max(weatherMap[w.asset_id].rainfall_mm,    w.rainfall_mm);
    weatherMap[w.asset_id].flood_depth_cm = Math.max(weatherMap[w.asset_id].flood_depth_cm, w.flood_depth_cm);
  });
  const terrainMap    = Object.fromEntries(terrain.map((r) => [r.asset_id, r]));
  const vegMap        = Object.fromEntries(vegetation.map((r) => [r.asset_id, r]));
  const topologyMap   = Object.fromEntries(topology.map((r) => [r.asset_id, r]));

  // 3. Merge and run engines
  const assetDocs = assets.map((a) => {
    const merged = {
      ...a,
      ...(weatherMap[a.asset_id]  || {}),
      ...(terrainMap[a.asset_id]  || {}),
      ...(vegMap[a.asset_id]      || {}),
      ...(topologyMap[a.asset_id] || {}),
    };
    const risk  = riskScore(merged);
    const prio  = prioScore({ ...merged, ...risk });
    const rec   = buildRecommendation({ ...merged, ...risk });
    return { ...merged, ...risk, ...prio, ...rec };
  });

  // 4. Save to MongoDB
  await Asset.deleteMany({});
  await Incident.deleteMany({});
  await Asset.insertMany(assetDocs);
  await Incident.insertMany(incidents);
  console.log(`  Saved ${assetDocs.length} assets and ${incidents.length} incidents to MongoDB`);

  // Summary
  const top5 = [...assetDocs].sort((a, b) => b.priority_score - a.priority_score).slice(0, 5);
  console.log("\n  Top 5 by priority_score:");
  top5.forEach((a) => console.log(`    ${a.asset_id}  risk=${a.risk_score}  priority=${a.priority_score}  cause=${a.dominant_cause}`));
  console.log("\nPipeline complete.");
}

// Called standalone: node src/pipeline/seed.js
if (require.main === module) {
  mongoose.connect(MONGO_URI).then(async () => {
    try { await runPipeline(); }
    finally { mongoose.disconnect(); }
  }).catch((e) => { console.error(e); process.exit(1); });
}

module.exports = { runPipeline };
