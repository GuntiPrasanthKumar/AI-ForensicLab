const mongoose = require("mongoose");
const bcrypt = require("bcryptjs");

const UserSchema = new mongoose.Schema({
  name: { type: String, required: true },
  email: { type: String, required: true, unique: true },
  password: { type: String, required: true },
  createdAt: { type: Date, default: Date.now },
  
  // Security Fields
  role: { type: String, enum: ['user', 'admin'], default: 'user' },
  isVerified: { type: Boolean, default: false },
  verificationToken: { type: String },
  emailOtp: { type: String },
  emailOtpExpire: { type: Date },
  
  // Password Reset
  resetPasswordToken: { type: String },
  resetPasswordExpire: { type: Date },
  
  // Login Lockout
  loginAttempts: { type: Number, required: true, default: 0 },
  lockUntil: { type: Date },
  
  // Session Invalidation
  tokenVersion: { type: Number, default: 0 }
});

// Hash password before saving
UserSchema.pre("save", async function () {
  if (!this.isModified("password")) return;
  const salt = await bcrypt.genSalt(10);
  this.password = await bcrypt.hash(this.password, salt);
});

module.exports = mongoose.model("User", UserSchema);
