const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");
const helmet = require("helmet");
const cookieParser = require("cookie-parser");
require("dotenv").config();

const { apiLimiter, sanitizeNoSQL } = require("./middleware/security");

const app = express();

// Secure HTTP headers
app.use(helmet());

// Prevent NoSQL Injection
app.use(sanitizeNoSQL);

// Apply rate limiter to all API routes
app.use("/api", apiLimiter);

// Parse Cookies
app.use(cookieParser());

// Secure CORS configuration for HttpOnly cookies
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

app.use(express.json());

mongoose.connect(process.env.MONGO_URI)
  .then(() => console.log("MongoDB Connected"))
  .catch(err => console.log(err));

app.use("/api/auth", require("./routes/auth"));
app.use("/api", require("./routes/detect"));
app.use("/api", require("./routes/history"));

app.listen(5000, () => console.log("Server running on port 5000"));
