"use strict";
const express = require("express");
const router  = express.Router();
const store   = require("../store/store");
const { answerQuestion } = require("../services/advisor");

router.post("/ask", (req, res) => {
  const { question } = req.body;
  if (!question || !question.trim()) {
    return res.status(400).json({ error: "question is required" });
  }
  const assets = store.getAssets();
  if (!assets.length) {
    return res.status(503).json({ error: "No asset data. Try POST /api/pipeline/run" });
  }
  const answer = answerQuestion(question, assets);
  res.json({ answer });
});

module.exports = router;
