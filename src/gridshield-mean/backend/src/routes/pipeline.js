"use strict";
const express = require("express");
const router  = express.Router();
const store   = require("../store/store");

// Re-run full pipeline (refreshes in-memory data)
router.post("/run", (_req, res) => {
  try {
    store.runPipeline();
    res.json({ success: true, message: "Pipeline complete — data refreshed." });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// All incidents
router.get("/incidents", (_req, res) => {
  res.json(store.getIncidents());
});

module.exports = router;
