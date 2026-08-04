const mongoose = require("mongoose");

const ResultSchema = new mongoose.Schema({
  userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: false },
  filename: String,
  inputType: { type: String, enum: ["file", "text", "image", "video"], default: "file" },
  aiProbability: Number,
  humanProbability: Number,
  morphProbability: { type: Number, default: 0 },
  confidence: String,
  metrics: mongoose.Schema.Types.Mixed,
  reasons: [String],
  detectedArtifacts: [String],
  explanation: String,
  provider_used: String,
  engine_status: String,
  is_cached: Boolean,
  createdAt: { type: Date, default: Date.now }
});

module.exports = mongoose.model("Result", ResultSchema);
