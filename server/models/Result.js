const mongoose = require("mongoose");

const ResultSchema = new mongoose.Schema({
  userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: false }, // false for backward compatibility
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
  createdAt: { type: Date, default: Date.now }
});

module.exports = mongoose.model("Result", ResultSchema);
