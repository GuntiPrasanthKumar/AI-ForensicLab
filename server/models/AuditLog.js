/**
 * AuditLog Schema & Model Definition
 * Tracks security events, authentication attempts, and system actions.
 */
const mongoose = require("mongoose");

const AuditLogSchema = new mongoose.Schema({
  userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
  email: { type: String }, // Useful if login fails and no user exists
  action: { 
    type: String, 
    enum: ['LOGIN_SUCCESS', 'LOGIN_FAILED', 'ACCOUNT_LOCKED', 'PASSWORD_RESET', 'EMAIL_VERIFIED', 'REGISTER_ATTEMPT', 'OTP_RESENT'],
    required: true
  },
  ipAddress: { type: String },
  userAgent: { type: String },
  createdAt: { type: Date, default: Date.now }
});

module.exports = mongoose.model("AuditLog", AuditLogSchema);
