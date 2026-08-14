/**
 * Benchmark Routes Module
 * Exposes endpoints for running model benchmark evaluations.
 */
const express = require("express");
const axios = require("axios");
const router = express.Router();
const authMiddleware = require("../middleware/authMiddleware");

const getAiUrl = () => {
  const defaultUrl = process.env.NODE_ENV === "production" 
    ? "https://ai-forensiclab-2.onrender.com" 
    : "http://localhost:8000";
  return (process.env.AI_SERVICE_URL || defaultUrl).replace(/\/+$/, "") + "/api/benchmark";
};

// GET /api/benchmark/summary
router.get("/summary", authMiddleware, async (req, res) => {
  try {
    const aiUrl = getAiUrl();
    const response = await axios.get(`${aiUrl}/summary`, { timeout: 30000 });
    res.json(response.data);
  } catch (err) {
    console.error("[Node Gateway] Benchmark summary fetch error:", err.message);
    res.status(500).json({ error: "Failed to retrieve benchmark laboratory summary." });
  }
});

// POST /api/benchmark/run
router.post("/run", authMiddleware, async (req, res) => {
  try {
    const aiUrl = getAiUrl();
    const response = await axios.post(`${aiUrl}/run`, req.body, { timeout: 120000 });
    res.json(response.data);
  } catch (err) {
    console.error("[Node Gateway] Benchmark run trigger error:", err.message);
    res.status(500).json({ error: "Failed to execute benchmark evaluation suite." });
  }
});

module.exports = router;
