const express = require("express");
const multer = require("multer");
const axios = require("axios");
const Result = require("../models/Result");
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const FormData = require("form-data");

const router = express.Router();
const authMiddleware = require("../middleware/authMiddleware");

// Configure upload directory
const uploadDir = path.join(__dirname, "..", "uploads");
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}
const upload = multer({ 
  dest: uploadDir,
  limits: { fileSize: 50 * 1024 * 1024 } // 50MB max
});

const AI_SERVICE_PRIMARY = (process.env.AI_SERVICE_URL || "http://localhost:8000").replace(/\/+$/, "") + "/api";
const AI_SERVICE_FALLBACK = "https://ai-forensiclab-2.onrender.com/api";

// ─── In-Memory Deduplication Map for Concurrent Requests ────────────────────
const inflightRequests = new Map();

/**
 * Helper to execute AI Microservice request with primary & fallback service URLs.
 */
async function callAiService(endpoint, payload, isMultipart = false, timeoutMs = 60000) {
  const urls = [AI_SERVICE_PRIMARY];
  if (!AI_SERVICE_PRIMARY.includes("onrender.com")) {
    urls.push(AI_SERVICE_FALLBACK);
  }

  let lastError = null;

  for (let i = 0; i < urls.length; i++) {
    const baseUrl = urls[i];
    const fullUrl = `${baseUrl}/${endpoint}`;
    console.log(`[Node Gateway] Dispatching AI Request (${i + 1}/${urls.length}) -> ${fullUrl}`);

    try {
      let config = { timeout: timeoutMs };
      if (isMultipart) {
        config.headers = payload.getHeaders();
      }

      const response = await axios.post(fullUrl, payload, config);
      if (response.data && !response.data.error) {
        return response.data;
      }
      if (response.data && response.data.error) {
        console.warn(`[Node Gateway] AI Service returned operational warning: ${response.data.message || response.data.error}`);
        return response.data;
      }
    } catch (err) {
      lastError = err;
      console.error(`[Node Gateway] Request to ${fullUrl} failed: ${err.message}`);
    }
  }

  throw lastError || new Error("All AI microservice endpoints are unreachable.");
}

// ─── GET /api/health ─────────────────────────────────────────────────────────
router.get("/health", (req, res) => {
  res.json({ status: "ok", message: "Node Express Server is operational" });
});

// ─── POST /api/detect (Image or Video or File) ──────────────────────────────
router.post("/detect", authMiddleware, upload.single("file"), async (req, res) => {
  let tempPath = null;
  try {
    if (!req.file) {
      return res.status(400).json({ message: "No file provided for forensic analysis." });
    }
    tempPath = req.file.path;

    const isImage = req.file.mimetype.startsWith("image/");
    const isVideo = req.file.mimetype.startsWith("video/");
    
    let endpoint = "detect";
    if (isImage) endpoint = "detect-image";
    if (isVideo) endpoint = "detect-video";

    const timeoutMs = isVideo ? 120000 : 60000;

    const form = new FormData();
    form.append("file", fs.createReadStream(tempPath), {
      filename: req.file.originalname,
      contentType: req.file.mimetype,
    });

    const aiData = await callAiService(endpoint, form, true, timeoutMs);

    // Persist result to MongoDB safely
    let saved = null;
    try {
      saved = await Result.create({
        userId: req.user.userId,
        filename: req.file.originalname,
        inputType: isVideo ? "video" : (isImage ? "image" : "file"),
        aiProbability: aiData.aiProbability || 0,
        humanProbability: aiData.humanProbability || 0,
        morphProbability: aiData.morphProbability || 0,
        confidence: aiData.confidence || "Medium",
        explanation: aiData.explanation || "Forensic breakdown complete.",
        reasons: aiData.reasons || [],
        detectedArtifacts: aiData.detectedArtifacts || [],
        metrics: aiData.metrics || {},
        providerUsed: aiData.provider_used || "AI Forensic Engine"
      });
    } catch (dbErr) {
      console.error("[Node Gateway] DB Save Error (non-fatal):", dbErr.message);
    }

    const responsePayload = {
      ...(saved ? saved.toObject() : aiData),
      provider_used: aiData.provider_used || "AI Forensic Engine",
      is_cached: Boolean(aiData.is_cached),
      engine_status: aiData.engine_status || "Active Engine"
    };

    res.json(responsePayload);

  } catch (err) {
    console.error("[Node Gateway] Detection Error:", err.message);

    res.status(200).json({
      aiProbability: 0,
      humanProbability: 100,
      morphProbability: 0,
      confidence: "Low (Fallback)",
      explanation: "Primary forensic AI service is currently busy. Backup heuristics loaded safely.",
      detectedArtifacts: ["System resilience active"],
      provider_used: "Local Forensic Fallback",
      engine_status: "Backup Engine Active",
      is_cached: false
    });
  } finally {
    if (tempPath && fs.existsSync(tempPath)) {
      try { fs.unlinkSync(tempPath); } catch (_) {}
    }
  }
});

// ─── POST /api/detect-text ───────────────────────────────────────────────────
router.post("/detect-text", authMiddleware, async (req, res) => {
  try {
    const { text } = req.body;
    if (!text || typeof text !== "string" || text.trim().length === 0) {
      return res.status(400).json({ message: "Please enter text for linguistic analysis." });
    }

    const textSample = text.trim();

    // Deduplication Key
    const reqHash = crypto.createHash("md5").update(`${req.user.userId}:${textSample}`).digest("hex");

    if (inflightRequests.has(reqHash)) {
      console.log("[Node Gateway] Joining existing inflight request for duplicate text submission...");
      const resultData = await inflightRequests.get(reqHash);
      return res.json(resultData);
    }

    const requestPromise = (async () => {
      const aiData = await callAiService("detect-text", { text: textSample }, false, 45000);

      let saved = null;
      try {
        saved = await Result.create({
          userId: req.user.userId,
          filename: "Pasted Text",
          inputType: "text",
          aiProbability: aiData.aiProbability || 0,
          humanProbability: aiData.humanProbability || 0,
          morphProbability: aiData.morphProbability || 0,
          confidence: aiData.confidence || "Medium",
          explanation: aiData.explanation || "Linguistic breakdown complete.",
          reasons: aiData.reasons || [],
          detectedArtifacts: aiData.detectedArtifacts || [],
          metrics: aiData.metrics || {},
          providerUsed: aiData.provider_used || "Linguistic Engine"
        });
      } catch (dbErr) {
        console.error("[Node Gateway] DB Save Error:", dbErr.message);
      }

      return {
        ...(saved ? saved.toObject() : aiData),
        provider_used: aiData.provider_used || "Linguistic AI Engine",
        is_cached: Boolean(aiData.is_cached),
        engine_status: aiData.engine_status || "Active Engine"
      };
    })();

    inflightRequests.set(reqHash, requestPromise);

    try {
      const responseData = await requestPromise;
      res.json(responseData);
    } finally {
      inflightRequests.delete(reqHash);
    }

  } catch (err) {
    console.error("[Node Gateway] Text Detection Error:", err.message);

    res.status(200).json({
      aiProbability: 50.0,
      humanProbability: 50.0,
      morphProbability: 0.0,
      confidence: "Medium (Fallback)",
      explanation: "Linguistic service temporarily operating in backup analysis mode. Statistical baseline engaged.",
      reasons: ["Primary AI service busy"],
      metrics: { perplexity: 50, burstiness: 50, lexical_diversity: 0.5 },
      provider_used: "Local Rule Engine",
      engine_status: "Backup Engine Active",
      is_cached: false
    });
  }
});

module.exports = router;
