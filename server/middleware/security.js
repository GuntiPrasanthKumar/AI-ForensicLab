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
 * Strict authentication route rate limiter to prevent brute-force login attempts.
 * Allows max 10 requests per 1-hour window per IP.
 */
const authLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 10, // Limit each IP to 10 login/register requests per hour
  message: { message: "Too many failed login attempts, please try again after an hour" },
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
  sanitizeNoSQL
};
