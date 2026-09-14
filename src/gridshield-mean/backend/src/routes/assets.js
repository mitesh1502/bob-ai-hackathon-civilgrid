"use strict";
const express = require("express");
const router  = express.Router();
const store   = require("../store/store");

// All assets sorted by priority_score
router.get("/", (_req, res) => {
  res.json(store.getAssets());
});

// Dashboard stats
router.get("/stats", (_req, res) => {
  res.json(store.getStats());
});

// Single asset — must come AFTER /stats to avoid route conflict
router.get("/:id", (req, res) => {
  const asset = store.getAsset(req.params.id);
  if (!asset) return res.status(404).json({ error: "Asset not found" });
  res.json(asset);
});

module.exports = router;
