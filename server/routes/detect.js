const express = require("express");
const multer = require("multer");
const axios = require("axios");
const Result = require("../models/Result");
const fs = require("fs");
const FormData = require("form-data");

const router = express.Router();
const authMiddleware = require("../middleware/authMiddleware");
const upload = multer({ dest: "uploads/" });

const AI_SERVICE_URL = `${process.env.AI_SERVICE_URL || "http://localhost:8000"}/api`;

// Health Check
router.get("/health", (req, res) => {
  res.json({ status: "ok", message: "Node server is healthy" });
});

// File Detection (Image or Text)
router.post("/detect", authMiddleware, upload.single("file"), async (req, res) => {
  let tempPath = null;
  try {
    if (!req.file) return res.status(400).json({ message: "No file uploaded" });
    tempPath = req.file.path;

    const isImage = req.file.mimetype.startsWith("image/");
    const isVideo = req.file.mimetype.startsWith("video/");
    
    let endpoint = "detect";
    if (isImage) endpoint = "detect-image";
    if (isVideo) endpoint = "detect-video";

    const form = new FormData();
    form.append("file", fs.createReadStream(tempPath), {
      filename: req.file.originalname,
      contentType: req.file.mimetype,
    });

    console.log(`Sending request to AI Service: ${AI_SERVICE_URL}/${endpoint}`);
    
    // Videos take much longer to process (frame extraction)
    const timeoutMs = isVideo ? 120000 : 60000;
    
    const response = await axios.post(`${AI_SERVICE_URL}/${endpoint}`, form, {
      headers: form.getHeaders(),
      timeout: timeoutMs, 
    });

    // Save to MongoDB
    const saved = await Result.create({
      userId: req.user.userId,
      filename: req.file.originalname,
      inputType: isVideo ? "video" : (isImage ? "image" : "file"),
      aiProbability: response.data.aiProbability || 0,
      humanProbability: response.data.humanProbability || 0,
      morphProbability: response.data.morphProbability || 0,
      confidence: response.data.confidence || "Unknown",
      explanation: response.data.explanation || "No explanation provided.",
      reasons: response.data.reasons || [],
      detectedArtifacts: response.data.detectedArtifacts || [],
      metrics: response.data.metrics || {}
    });

    // Clean up
    if (fs.existsSync(tempPath)) fs.unlinkSync(tempPath);
    res.json(saved);

  } catch (err) {
    if (tempPath && fs.existsSync(tempPath)) fs.unlinkSync(tempPath);
    
    let errorMessage = "Analysis failed";
    let errorDetails = null;

    if (err.code === "ECONNREFUSED") {
      errorMessage = "AI Service (Python) is not running or unreachable.";
    } else if (err.code === "ECONNABORTED") {
      errorMessage = "AI Service took too long to respond. Try a smaller image.";
    } else if (err.response) {
      // If Python service crashed, Render returns an HTML page for 502/504
      if (typeof err.response.data === 'string' && err.response.data.includes('<html')) {
        errorMessage = `AI Error: Render Gateway Error (Status ${err.response.status}). The AI service might be out of memory or sleeping.`;
      } else {
        errorMessage = `AI Error: ${err.response.data?.message || err.response.data?.error || "Internal Service Error"}`;
      }
      errorDetails = err.response.data;
    } else {
      errorMessage = `System Error: ${err.message}`;
    }

    console.error("DETECTION ERROR:", errorMessage, err.message);
    res.status(500).json({ message: errorMessage, details: errorDetails });
  }
});

// Text Detection
router.post("/detect-text", authMiddleware, async (req, res) => {
  try {
    const { text } = req.body;
    if (!text) return res.status(400).json({ message: "No text provided" });

    const response = await axios.post(`${AI_SERVICE_URL}/detect-text`, { text });

    // Save to MongoDB
    const saved = await Result.create({
      userId: req.user.userId,
      filename: "Pasted Text",
      inputType: "text",
      ...response.data
    });

    res.json(saved);
  } catch (err) {
    console.error(err);
    res.status(500).json({ message: "Text detection failed", error: err.message });
  }
});

module.exports = router;
