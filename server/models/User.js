/**
 * User Schema & Model Definition
 * Defines user accounts, security tokens, OTP verification, and lockout fields.
 */
const mongoose = require("mongoose");
const bcrypt = require("bcryptjs");

const UserSchema = new mongoose.Schema({
  name: { type: String, required: true },
  email: { type: String, required: true, unique: true },
  password: { type: String },
  createdAt: { type: Date, default: Date.now },
  
  // Security Fields
  role: { type: String, default: 'user' },
  isVerified: { type: Boolean, default: false },
  verificationToken: { type: String },

  // Registration Email OTP
  emailOtp: { type: String },
  emailOtpExpire: { type: Date },
  
  // Password Reset OTP (independent from registration OTP)
  resetOtp: { type: String },
  resetOtpExpire: { type: Date },

  // Legacy Password Reset (token-based — kept for backward compat)
  resetPasswordToken: { type: String },
  resetPasswordExpire: { type: Date },
  
  // Login Lockout
  loginAttempts: { type: Number, default: 0 },
  lockUntil: { type: Date },
  
  // Session Invalidation
  tokenVersion: { type: Number, default: 0 }
});

// Hash password and sanitize fields before saving
UserSchema.pre("save", async function () {
  if (this.email) {
    this.email = String(this.email).toLowerCase().trim();
  }
  if (isNaN(this.loginAttempts) || this.loginAttempts == null) {
    this.loginAttempts = 0;
  }
  if (isNaN(this.tokenVersion) || this.tokenVersion == null) {
    this.tokenVersion = 0;
  }
  if (!this.role || !['user', 'admin'].includes(String(this.role).toLowerCase())) {
    this.role = 'user';
  } else {
    this.role = String(this.role).toLowerCase();
  }
  if (!this.isModified("password")) return;
  const salt = await bcrypt.genSalt(10);
  this.password = await bcrypt.hash(this.password, salt);
});

module.exports = mongoose.model("User", UserSchema);
