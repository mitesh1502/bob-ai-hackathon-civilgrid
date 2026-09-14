/**
 * server.js
 * GridShield Express server — no database required, runs entirely in memory.
 */
"use strict";

require("dotenv").config();
const express = require("express");
const cors    = require("cors");
const path    = require("path");

const { runPipeline } = require("./store/store");
const assetRoutes    = require("./routes/assets");
const pipelineRoutes = require("./routes/pipeline");
const advisorRoutes  = require("./routes/advisor");

const app  = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// API routes
app.use("/api/assets",   assetRoutes);
app.use("/api/pipeline", pipelineRoutes);
app.use("/api/advisor",  advisorRoutes);

// Health check
app.get("/api/health", (_req, res) => res.json({ status: "ok", ts: new Date() }));

// Run pipeline on startup
runPipeline();

app.listen(PORT, () => {
  console.log(`GridShield API running at http://localhost:${PORT}`);
  console.log(`Health: http://localhost:${PORT}/api/health`);
});
