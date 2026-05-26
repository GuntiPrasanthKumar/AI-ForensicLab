const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");
const helmet = require("helmet");
const cookieParser = require("cookie-parser");
const dns = require("node:dns");
require("dotenv").config();

// Force IPv4 resolution to prevent Render ENETUNREACH IPv6 errors with Nodemailer
dns.setDefaultResultOrder("ipv4first");

const { apiLimiter, sanitizeNoSQL } = require("./middleware/security");

const app = express();
app.set("trust proxy", 1);

const allowedOrigins = new Set(
  [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://ai-forensic-lab.vercel.app",
    process.env.FRONTEND_URL,
  ]
    .filter(Boolean)
    .map((o) => o.replace(/\/$/, ""))
);

function isAllowedOrigin(origin) {
  if (!origin) return true;
  const normalized = origin.replace(/\/$/, "");
  if (allowedOrigins.has(normalized)) return true;
  // All Vercel production & preview deployments
  if (/^https:\/\/[a-z0-9-]+([.-][a-z0-9-]+)*\.vercel\.app$/i.test(normalized)) {
    return true;
  }
  return false;
}

function setCorsHeaders(req, res) {
  const origin = req.headers.origin;
  if (origin && isAllowedOrigin(origin)) {
    res.setHeader("Access-Control-Allow-Origin", origin);
    res.setHeader("Access-Control-Allow-Credentials", "true");
    res.setHeader("Vary", "Origin");
  }
}

// 1. Secure HTTP headers (allow cross-origin API use from Vercel)
app.use(
  helmet({
    crossOriginResourcePolicy: { policy: "cross-origin" },
  })
);

// 2. Parse Cookies
app.use(cookieParser());

// 3. Body Parser (MUST be before mongo sanitize)
app.use(express.json());

// 4. CORS — must echo the request origin (not `true`) when credentials: true
app.use(
  cors({
    origin(origin, callback) {
      if (isAllowedOrigin(origin)) {
        // Reflect exact origin for credentialed requests; allow non-browser requests
        callback(null, origin || true);
      } else {
        console.warn("CORS blocked origin:", origin);
        callback(null, false);
      }
    },
    credentials: true,
    methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allowedHeaders: ["Content-Type", "Authorization"],
  })
);

// 5. Prevent NoSQL Injection (MUST be after express.json)
app.use(sanitizeNoSQL);

// 6. Apply rate limiter to all API routes
app.use("/api", apiLimiter);

mongoose
  .connect(process.env.MONGO_URI)
  .then(() => console.log("MongoDB Connected"))
  .catch((err) => console.log(err));

app.use("/api/auth", require("./routes/auth"));
app.use("/api", require("./routes/detect"));
app.use("/api", require("./routes/history"));

// Ensure CORS headers on error responses too
app.use((err, req, res, next) => {
  setCorsHeaders(req, res);
  const status = err.status || 500;
  res.status(status).json({ message: err.message || "Server error" });
});

app.listen(5000, () => console.log("Server running on port 5000"));
