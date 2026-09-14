/**
 * generateData.js
 * ---------------
 * Pure-JS port of generate_data.py (seed=42, same logic, same asset counts).
 * Returns { assets, weather, terrain, vegetation, topology, incidents }
 * as plain arrays — no file I/O here; the seed.js pipeline saves to MongoDB.
 */

"use strict";

// ── Seeded PRNG (mulberry32) so results are reproducible ──────────────────────
function mkRng(seed) {
  let s = seed >>> 0;
  return () => {
    s += 0x6d2b79f5;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const rng = mkRng(42);

function randFloat(lo, hi, dp = 1) {
  return parseFloat((lo + rng() * (hi - lo)).toFixed(dp));
}
function randInt(lo, hi) {
  return Math.floor(lo + rng() * (hi - lo + 1));
}
function jitter(base, spread = 0.4) {
  return parseFloat((base + (rng() * 2 - 1) * spread).toFixed(5));
}

const BASE_LAT = 51.5, BASE_LON = -0.12;
const N_ASSETS = 40, N_HIGH_RISK = 6;
const ASSET_TYPES = ["pole", "transformer", "substation"];
const MATERIALS = ["wood", "steel", "concrete"];
const FOUNDATION_TYPES = ["direct_buried", "concrete_pad", "rock_anchor"];
const SOIL_CLASSES = ["clay", "sandy_loam", "gravel", "peat"];
const FEEDER_IDS = ["F-100", "F-101", "F-102", "F-103", "F-104"];
const CRITICAL_LOADS = ["hospital", "water_treatment", "shelter", "none"];
const CAUSES = ["wind", "flood", "vegetation_contact", "corrosion", "equipment_age", "unknown"];

function assetId(i) { return `A-${String(i).padStart(2, "0")}`; }

function addDays(daysBack) {
  const d = new Date();
  d.setDate(d.getDate() - daysBack);
  return d.toISOString().split("T")[0];
}

// ── 1. Assets ────────────────────────────────────────────────────────────────
function buildAssets() {
  const highRisk = [
    ["pole",        38, "wood",     32, 6.2, 78, "direct_buried", 480],
    ["transformer", 41, "steel",    28, 5.8, 82, "direct_buried", 520],
    ["pole",        35, "wood",     35, 6.7, 71, "direct_buried", 410],
    ["substation",  44, "steel",    22, 5.1, 85, "concrete_pad",  600],
    ["pole",        33, "wood",     30, 7.0, 74, "direct_buried", 390],
    ["transformer", 29, "steel",    40, 5.4, 68, "concrete_pad",  450],
  ];
  const rows = [];
  highRisk.forEach(([atype, age, mat, insp, tilt, corr, fnd, maintDays], idx) => {
    rows.push({
      asset_id: assetId(idx + 1), asset_type: atype, latitude: jitter(BASE_LAT),
      longitude: jitter(BASE_LON), age_years: age, material: mat,
      inspection_score: insp, tilt_deg: tilt, corrosion_score: corr,
      foundation_type: fnd, last_maintenance_date: addDays(maintDays),
    });
  });
  for (let i = N_HIGH_RISK + 1; i <= N_ASSETS; i++) {
    rows.push({
      asset_id: assetId(i),
      asset_type: ASSET_TYPES[randInt(0, 2)],
      latitude: jitter(BASE_LAT), longitude: jitter(BASE_LON),
      age_years: randInt(2, 25), material: MATERIALS[randInt(0, 2)],
      inspection_score: randInt(45, 95), tilt_deg: randFloat(0, 4.5),
      corrosion_score: randInt(10, 65),
      foundation_type: FOUNDATION_TYPES[randInt(0, 2)],
      last_maintenance_date: addDays(randInt(10, 360)),
    });
  }
  return rows;
}

// ── 2. Weather ───────────────────────────────────────────────────────────────
function buildWeather(assets) {
  const rows = [];
  const highIds = new Set(Array.from({ length: N_HIGH_RISK }, (_, i) => assetId(i + 1)));
  const base = new Date(); base.setDate(base.getDate() + 1);
  assets.forEach((asset) => {
    const isHR = highIds.has(asset.asset_id);
    const wind  = isHR ? randFloat(72, 98) : randFloat(15, 75);
    const rain  = isHR ? randFloat(48, 90) : randFloat(0, 55);
    const flood = isHR ? randFloat(4, 18)  : randFloat(0, 5);
    const lChoices = isHR ? ["high", "high", "medium"] : ["low", "medium", "high"];
    const lightning = lChoices[randInt(0, 2)];
    const temp  = isHR ? randFloat(5, 18) : randFloat(8, 28);
    for (let d = 0; d < 3; d++) {
      const fd = new Date(base); fd.setDate(fd.getDate() + d);
      rows.push({
        asset_id: asset.asset_id,
        forecast_date: fd.toISOString().split("T")[0],
        wind_gust_kmh:  Math.max(0, wind  + randFloat(-5, 5)),
        rainfall_mm:    Math.max(0, rain  + randFloat(-8, 8)),
        lightning_risk: lightning,
        temperature_c:  temp,
        flood_depth_cm: Math.max(0, flood + randFloat(-2, 2)),
      });
    }
  });
  return rows;
}

// ── 3. Terrain ───────────────────────────────────────────────────────────────
function buildTerrain(assets) {
  const highIds = new Set(Array.from({ length: N_HIGH_RISK }, (_, i) => assetId(i + 1)));
  return assets.map((a) => {
    const isHR = highIds.has(a.asset_id);
    return isHR
      ? { asset_id: a.asset_id, slope: randFloat(12, 28),
          soil_class: ["clay","peat"][randInt(0,1)],
          erosion_index: randInt(68, 95), drainage_score: randInt(8, 35), road_access_score: randInt(12, 40) }
      : { asset_id: a.asset_id, slope: randFloat(0, 18),
          soil_class: SOIL_CLASSES[randInt(0, 3)],
          erosion_index: randInt(5, 72), drainage_score: randInt(30, 95), road_access_score: randInt(30, 95) };
  });
}

// ── 4. Vegetation ─────────────────────────────────────────────────────────────
function buildVegetation(assets) {
  const highIds = new Set(Array.from({ length: N_HIGH_RISK }, (_, i) => assetId(i + 1)));
  return assets.map((a) => {
    const isHR = highIds.has(a.asset_id);
    return isHR
      ? { asset_id: a.asset_id, canopy_distance_m: randFloat(0.3, 1.8), tree_height_m: randFloat(14, 28), clearance_score: randInt(5, 32) }
      : { asset_id: a.asset_id, canopy_distance_m: randFloat(0.5, 8.0), tree_height_m: randFloat(2, 20),  clearance_score: randInt(25, 95) };
  });
}

// ── 5. Topology ───────────────────────────────────────────────────────────────
function buildTopology(assets) {
  const highIds = new Set(Array.from({ length: N_HIGH_RISK }, (_, i) => assetId(i + 1)));
  return assets.map((a) => {
    const isHR = highIds.has(a.asset_id);
    return isHR
      ? { asset_id: a.asset_id, feeder_id: ["F-100","F-101"][randInt(0,1)],
          downstream_customers: randInt(800, 3500),
          critical_loads: ["hospital","water_treatment","hospital","shelter"][randInt(0,3)],
          redundancy: false }
      : { asset_id: a.asset_id, feeder_id: FEEDER_IDS[randInt(0, 4)],
          downstream_customers: randInt(50, 1500),
          critical_loads: CRITICAL_LOADS[randInt(0, 3)],
          redundancy: rng() > 0.5 };
  });
}

// ── 6. Incidents ─────────────────────────────────────────────────────────────
function buildIncidents(assets) {
  const rows = [];
  for (let i = 1; i <= N_HIGH_RISK; i++) {
    const aid = assetId(i);
    const n = randInt(2, 3);
    for (let k = 0; k < n; k++) {
      rows.push({ asset_id: aid, incident_date: addDays(randInt(0, 4 * 365)),
        cause: ["wind","flood","vegetation_contact","corrosion"][randInt(0,3)],
        downtime_hours: randFloat(4, 72) });
    }
  }
  const normalIds = assets.slice(N_HIGH_RISK).map((a) => a.asset_id);
  // shuffle
  for (let i = normalIds.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [normalIds[i], normalIds[j]] = [normalIds[j], normalIds[i]];
  }
  normalIds.slice(0, 8).forEach((aid) => {
    rows.push({ asset_id: aid, incident_date: addDays(randInt(0, 5 * 365)),
      cause: CAUSES[randInt(0, 5)], downtime_hours: randFloat(1, 24) });
  });
  return rows;
}

// ── Public API ────────────────────────────────────────────────────────────────
function generateAll() {
  const assets     = buildAssets();
  const weather    = buildWeather(assets);
  const terrain    = buildTerrain(assets);
  const vegetation = buildVegetation(assets);
  const topology   = buildTopology(assets);
  const incidents  = buildIncidents(assets);
  return { assets, weather, terrain, vegetation, topology, incidents };
}

module.exports = { generateAll };
