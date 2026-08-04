require("dotenv").config();

module.exports = {
  PORT: process.env.PORT || 5000,
  NODE_ENV: process.env.NODE_ENV || "development",
  MONGO_URI: process.env.MONGO_URI,
  JWT_SECRET: process.env.JWT_SECRET || "fallback_secret",
  AI_SERVICE_URL: process.env.AI_SERVICE_URL || (process.env.NODE_ENV === "production" ? "https://ai-forensiclab-2.onrender.com" : "http://localhost:8000"),
  BREVO_API_KEY: process.env.BREVO_API_KEY,
  SENDER_EMAIL: process.env.SENDER_EMAIL || "support@aiforensiclab.com"
};
