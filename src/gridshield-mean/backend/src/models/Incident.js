/**
 * Incident Mongoose model
 */
const mongoose = require("mongoose");

const IncidentSchema = new mongoose.Schema({
  asset_id:       { type: String, required: true },
  incident_date:  String,
  cause:          String,
  downtime_hours: Number,
});

module.exports = mongoose.model("Incident", IncidentSchema);
