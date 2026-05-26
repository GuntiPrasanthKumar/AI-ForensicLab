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

// 1. Secure HTTP headers
app.use(helmet());

// 2. Parse Cookies
app.use(cookieParser());

// 3. Body Parser (MUST be before mongo sanitize)
app.use(express.json());

// 4. Secure CORS configuration for HttpOnly cookies
const allowedOrigins = [
  "http://localhost:5173", 
  "https://ai-forensic-lab.vercel.app",
  process.env.FRONTEND_URL
].filter(Boolean);

app.use(cors({
  origin: function (origin, callback) {
    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true, // Crucial for sending/receiving HttpOnly cookies
}));

// 5. Prevent NoSQL Injection (MUST be after express.json)
app.use(sanitizeNoSQL);

// 6. Apply rate limiter to all API routes
app.use("/api", apiLimiter);

mongoose.connect(process.env.MONGO_URI)
  .then(() => console.log("MongoDB Connected"))
  .catch(err => console.log(err));

app.use("/api/auth", require("./routes/auth"));
app.use("/api", require("./routes/detect"));
app.use("/api", require("./routes/history"));

app.listen(5000, () => console.log("Server running on port 5000"));
