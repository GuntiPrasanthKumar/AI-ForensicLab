const rateLimit = require("express-rate-limit");
const mongoSanitize = require("express-mongo-sanitize");

/**
 * General API rate limiter to protect public endpoints from excessive requests.
 * Allows max 100 requests per 15-minute window per IP.
 */
const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per `window`
  message: { message: "Too many requests from this IP, please try again after 15 minutes" },
  standardHeaders: true,
  legacyHeaders: false,
});

/**
 * Authentication route rate limiter for login/register.
 * Increased from 10 to 20 per hour to accommodate the full
 * registration + OTP verification + resend + reset flow.
 */
const authLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 20, // Limit each IP to 20 auth requests per hour
  message: { message: "Too many requests, please try again after an hour" },
  standardHeaders: true,
  legacyHeaders: false,
});

/**
 * OTP-specific rate limiter to prevent OTP brute-force attacks.
 * 6 requests per 15-minute window per IP — covers verify + resend cycles.
 */
const otpLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 6,
  message: { message: "Too many OTP attempts. Please try again in 15 minutes." },
  standardHeaders: true,
  legacyHeaders: false,
});

/**
 * Express middleware to sanitize incoming request parameters and prevent NoSQL injection attacks.
 */
const sanitizeNoSQL = mongoSanitize();

module.exports = {
  apiLimiter,
  authLimiter,
  otpLimiter,
  sanitizeNoSQL
};
