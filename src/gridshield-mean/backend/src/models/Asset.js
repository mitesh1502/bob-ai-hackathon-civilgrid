/**
 * Asset Mongoose model
 * Stores the fully-computed final_report row for each asset.
 */
const mongoose = require("mongoose");

const AssetSchema = new mongoose.Schema(
  {
    asset_id:   { type: String, required: true, unique: true },
    asset_type: String,
    latitude:   Number,
    longitude:  Number,
    age_years:  Number,
    material:   String,
    inspection_score: Number,
    tilt_deg:   Number,
    corrosion_score: Number,
    foundation_type: String,
    last_maintenance_date: String,

    // weather (worst-case 3-day)
    wind_gust_kmh:  Number,
    rainfall_mm:    Number,
    flood_depth_cm: Number,

    // terrain
    erosion_index:    Number,
    drainage_score:   Number,
    road_access_score: Number,

    // vegetation
    clearance_score:   Number,
    canopy_distance_m: Number,
    tree_height_m:     Number,

    // topology
    feeder_id:             String,
    downstream_customers:  Number,
    critical_loads:        String,
    redundancy:            Boolean,

    // risk engine outputs
    factor_wind:       Number,
    factor_rain:       Number,
    factor_tilt:       Number,
    factor_erosion:    Number,
    factor_corrosion:  Number,
    factor_drainage:   Number,
    factor_vegetation: Number,
    factor_age:        Number,
    risk_score:        Number,
    dominant_cause:    String,

    // priority engine outputs
    critical_load_multiplier:   Number,
    expected_loss:              Number,
    estimated_intervention_cost: Number,
    priority_score:             Number,

    // recommendation engine outputs
    recommended_action:          String,
    action_tier:                 String,
    expected_risk_reduction_pct: Number,
    recommended_crew_type:       String,
    risk_band:                   String,
    safety_note:                 String,
  },
  { timestamps: true }
);

module.exports = mongoose.model("Asset", AssetSchema);
