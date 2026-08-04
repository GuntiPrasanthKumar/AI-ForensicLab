const express = require("express");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const crypto = require("crypto");
const User = require("../models/User");
const AuditLog = require("../models/AuditLog");
const { authLimiter, otpLimiter } = require("../middleware/security");
const authMiddleware = require("../middleware/authMiddleware");
const sendEmail = require("../utils/email");
const { isEmailConfigured, buildOtpEmailHtml, buildResetOtpEmailHtml } = require("../utils/email");
const {
  generateOtp,
  setEmailOtpFields,
  clearEmailOtpFields,
  isOtpValid,
  setResetOtpFields,
  clearResetOtpFields,
  isResetOtpValid,
} = require("../utils/otp");
const verifyTurnstile = require("../utils/turnstile");

const router = express.Router();
const JWT_SECRET = process.env.JWT_SECRET || "ai_detector_secret_123";

// Helper to set cookie safely
const sendTokenCookie = (res, user) => {
  const payload = { 
    userId: user.id || user._id, 
    role: user.role || "user", 
    tokenVersion: user.tokenVersion || 0 
  };
  const token = jwt.sign(payload, JWT_SECRET, { expiresIn: "7d" });
  
  res.cookie("token", token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production", // Requires HTTPS in production
    sameSite: process.env.NODE_ENV === "production" ? "none" : "lax",
    maxAge: 7 * 24 * 60 * 60 * 1000 // 7 days
  });
};

// Safe audit logging helper — never crashes authentication flow if audit log fails
const safeAuditLog = async (data) => {
  try {
    await AuditLog.create(data);
  } catch (err) {
    console.error("[AUDIT LOG ERROR] Non-fatal audit log failure:", err.message);
  }
};

// ─── Helper: send registration verification OTP email ────────────────────────

async function sendVerificationOtp(user, otp) {
  const message = `Your AI Forensic Lab verification code is: ${otp}\n\nThis code expires in 10 minutes.`;
  const html = buildOtpEmailHtml(otp, user.name);
  console.log("[AUTH] Sending registration OTP email to:", user.email);
  await sendEmail({
    email: user.email,
    subject: "Your verification code — AI Forensic Lab",
    message,
    html,
  });
  console.log("[AUTH] Registration OTP email sent to:", user.email);
}

// ─── Helper: send password reset OTP email ───────────────────────────────────

async function sendResetOtpEmail(user, otp) {
  const message = `Your AI Forensic Lab password reset code is: ${otp}\n\nThis code expires in 10 minutes. If you did not request this, ignore this email.`;
  const html = buildResetOtpEmailHtml(otp, user.name);
  console.log("[AUTH] Sending reset OTP email to:", user.email);
  await sendEmail({
    email: user.email,
    subject: "Password reset code — AI Forensic Lab",
    message,
    html,
  });
  console.log("[AUTH] Reset OTP email sent to:", user.email);
}

// ═══════════════════════════════════════════════════════════════════════════════
// @route   POST /api/auth/register
// @desc    Register user & send email OTP
// ═══════════════════════════════════════════════════════════════════════════════
router.post("/register", authLimiter, async (req, res) => {
  const { name, email, password, turnstileToken } = req.body;
  try {
    console.log("[AUTH] Registration attempt for:", email);

    // 1. Validate input
    if (!name || !email || !password) {
      return res.status(400).json({ message: "Name, email, and password are required." });
    }

    // 2. Verify CAPTCHA
    if (!turnstileToken) {
      return res.status(400).json({ message: "Please wait for CAPTCHA to verify before submitting." });
    }
    const captchaResult = await verifyTurnstile(turnstileToken);
    if (!captchaResult.success && process.env.NODE_ENV === "production") {
      const maskedSecret = process.env.TURNSTILE_SECRET_KEY 
        ? `${process.env.TURNSTILE_SECRET_KEY.substring(0, 10)}... (len: ${process.env.TURNSTILE_SECRET_KEY.length})` 
        : "NOT_SET";
      const codes = (captchaResult.errorCodes || []).join(", ") || "invalid-token";
      return res.status(400).json({ message: `CAPTCHA verification failed [${codes}]. (Backend Secret: ${maskedSecret})` });
    }

    // 3. Check email service BEFORE creating user (fix: prevents orphaned users)
    if (!isEmailConfigured()) {
      console.error("[AUTH] Email service not configured — cannot register");
      return res.status(503).json({
        message: "Email service is not configured on the server. Please add RESEND_API_KEY (or EMAIL_USER + EMAIL_PASS) to environment variables.",
      });
    }

    // 4. Check for existing account
    const existing = await User.findOne({ email });
    if (existing) {
      // If unverified and older than 30 min, allow re-registration by deleting the stale entry
      if (!existing.isVerified && existing.createdAt < new Date(Date.now() - 30 * 60 * 1000)) {
        console.log("[AUTH] Removing stale unverified account for:", email);
        await User.findByIdAndDelete(existing._id);
      } else {
        return res.status(400).json({ message: "An account with this email already exists." });
      }
    }

    // 5. Create user and generate OTP
    const otp = generateOtp();
    const user = new User({ name, email, password, isVerified: false });
    setEmailOtpFields(user, otp);
    await user.save();
    console.log("[AUTH] User created:", email, "| ID:", user._id);

    // 6. Send OTP email
    try {
      await sendVerificationOtp(user, otp);
      await safeAuditLog({ userId: user.id, action: "REGISTER_ATTEMPT", ipAddress: req.ip });
      return res.status(201).json({
        message: "Verification code sent to your email.",
        requiresEmailVerification: true,
        email: user.email,
      });
    } catch (error) {
      // Clean up user if email fails
      await User.findByIdAndDelete(user._id);
      console.error("[AUTH] REGISTER EMAIL FAILED — user cleaned up:", error.stack || error.message);
      return res.status(503).json({
        message: `Could not send verification email. Please try again. (${error.message})`,
      });
    }
  } catch (err) {
    console.error("[AUTH] REGISTER ERROR Stack:", err.stack || err);
    res.status(500).json({ message: "Server error: Unable to process registration" });
  }
});

// ═══════════════════════════════════════════════════════════════════════════════
// @route   POST /api/auth/verify-otp
// @desc    Verify email with 6-digit OTP (registration)
// ═══════════════════════════════════════════════════════════════════════════════
router.post("/verify-otp", otpLimiter, async (req, res) => {
  const { email, otp } = req.body;
  try {
    console.log("[AUTH] Verify registration OTP for:", email);

    if (!email || !otp) {
      return res.status(400).json({ message: "Email and verification code are required." });
    }

    const cleanEmail = String(email).toLowerCase().trim();
    const user = await User.findOne({ email: cleanEmail });
    if (!user) {
      console.log("[AUTH] Verify OTP — user not found:", cleanEmail);
      return res.status(400).json({ message: "Invalid verification code." });
    }

    if (user.isVerified) {
      console.log("[AUTH] Already verified:", cleanEmail);
      sendTokenCookie(res, user);
      return res.json({
        message: "Email already verified.",
        user: { id: user.id, name: user.name, email: user.email, role: user.role },
      });
    }

    if (!isOtpValid(user, String(otp).trim())) {
      return res.status(400).json({ message: "Invalid or expired verification code." });
    }

    user.isVerified = true;
    clearEmailOtpFields(user);
    user.verificationToken = undefined;
    await user.save();

    console.log("[AUTH] Email verified successfully:", cleanEmail);
    await safeAuditLog({ userId: user.id, action: "EMAIL_VERIFIED", ipAddress: req.ip });
    sendTokenCookie(res, user);
    res.json({
      message: "Email verified successfully.",
      user: { id: user.id, name: user.name, email: user.email, role: user.role },
    });
  } catch (err) {
    console.error("[AUTH] VERIFY OTP ERROR Stack:", err.stack || err);
    res.status(500).json({ message: "Server error: Unable to verify OTP" });
  }
});

// ═══════════════════════════════════════════════════════════════════════════════
// @route   POST /api/auth/resend-otp
// @desc    Resend email verification OTP (registration)
// ═══════════════════════════════════════════════════════════════════════════════
router.post("/resend-otp", otpLimiter, async (req, res) => {
  const { email } = req.body;
  try {
    console.log("[AUTH] Resend registration OTP for:", email);

    if (!isEmailConfigured()) {
      return res.status(503).json({ message: "Email service is not configured on the server." });
    }

    const cleanEmail = String(email).toLowerCase().trim();
    const user = await User.findOne({ email: cleanEmail });
    const genericMsg = "If an unverified account exists, a new code has been sent.";
    if (!user || user.isVerified) {
      return res.json({ message: genericMsg });
    }

    // Server-side cooldown: refuse if last OTP was sent < 30s ago
    if (user.emailOtpExpire && new Date(user.emailOtpExpire) > new Date(Date.now() + 9.5 * 60 * 1000)) {
      console.log("[AUTH] Resend too soon for:", cleanEmail);
      return res.status(429).json({ message: "Please wait before requesting another code." });
    }

    const otp = generateOtp();
    setEmailOtpFields(user, otp);
    await user.save();

    try {
      await sendVerificationOtp(user, otp);
      await safeAuditLog({ userId: user.id, action: "OTP_RESENT", ipAddress: req.ip });
    } catch (error) {
      console.error("[AUTH] RESEND OTP EMAIL ERROR:", error.stack || error.message);
      return res.status(503).json({
        message: "Could not send verification email. Please try again later.",
        details: process.env.NODE_ENV === "development" ? error.message : undefined,
      });
    }

    res.json({ message: genericMsg, email: user.email });
  } catch (err) {
    console.error("[AUTH] RESEND OTP ERROR Stack:", err.stack || err);
    res.status(500).json({ message: "Server error: Unable to resend code" });
  }
});

// ═══════════════════════════════════════════════════════════════════════════════
// @route   POST /api/auth/login
// @desc    Authenticate user & get token
// ═══════════════════════════════════════════════════════════════════════════════
router.post("/login", authLimiter, async (req, res) => {
  const { email, password, turnstileToken } = req.body;
  try {
    console.log("[AUTH] Login attempt for:", email);

    // 1. Verify CAPTCHA
    if (!turnstileToken) {
      return res.status(400).json({ message: "Please wait for CAPTCHA to verify before submitting." });
    }
    const captchaResult = await verifyTurnstile(turnstileToken);
    if (!captchaResult.success && process.env.NODE_ENV === "production") {
      const maskedSecret = process.env.TURNSTILE_SECRET_KEY 
        ? `${process.env.TURNSTILE_SECRET_KEY.substring(0, 10)}... (len: ${process.env.TURNSTILE_SECRET_KEY.length})` 
        : "NOT_SET";
      const codes = (captchaResult.errorCodes || []).join(", ") || "invalid-token";
      return res.status(400).json({ message: `CAPTCHA verification failed [${codes}]. (Backend Secret: ${maskedSecret})` });
    }

    const cleanEmail = email ? String(email).toLowerCase().trim() : "";
    const user = await User.findOne({ email: cleanEmail });
    
    // Generic error
    const invalidCredentialsMsg = "Invalid credentials";
    
    if (!user) {
      await safeAuditLog({ email: cleanEmail, action: 'LOGIN_FAILED', ipAddress: req.ip });
      return res.status(400).json({ message: invalidCredentialsMsg });
    }

    // Check Lockout
    if (user.lockUntil && user.lockUntil > Date.now()) {
      await safeAuditLog({ userId: user.id, action: 'ACCOUNT_LOCKED', ipAddress: req.ip });
      return res.status(403).json({ message: "Account locked. Please try again later or reset password." });
    }

    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      user.loginAttempts = (user.loginAttempts || 0) + 1;
      if (user.loginAttempts >= 5) {
        user.lockUntil = Date.now() + 15 * 60 * 1000; // Lock for 15 mins
      }
      await user.save();
      await safeAuditLog({ userId: user.id, action: 'LOGIN_FAILED', ipAddress: req.ip });
      return res.status(400).json({ message: invalidCredentialsMsg });
    }

    if (!user.isVerified) {
      return res.status(403).json({
        message: "Please verify your email with the 6-digit code we sent you.",
        requiresEmailVerification: true,
        email: user.email,
      });
    }

    // Reset attempts on success
    user.loginAttempts = 0;
    user.lockUntil = undefined;
    await user.save();

    console.log("[AUTH] Login successful:", cleanEmail);
    await safeAuditLog({ userId: user.id, action: 'LOGIN_SUCCESS', ipAddress: req.ip });
    sendTokenCookie(res, user);
    res.json({ user: { id: user.id, name: user.name, email: user.email, role: user.role } });
  } catch (err) {
    console.error("[AUTH] LOGIN ERROR Stack:", err.stack || err);
    res.status(500).json({ message: "Server error: Unable to log in" });
  }
});

// ═══════════════════════════════════════════════════════════════════════════════
// @route   POST /api/auth/forgot-password
// @desc    Send password reset OTP (converted from link-based to OTP-based)
// ═══════════════════════════════════════════════════════════════════════════════
router.post("/forgot-password", authLimiter, async (req, res) => {
  try {
    const { email } = req.body;
    console.log("[AUTH] Forgot password for:", email);

    if (!email) {
      return res.status(400).json({ message: "Email is required." });
    }

    if (!isEmailConfigured()) {
      return res.status(503).json({ message: "Email service is not configured on the server." });
    }

    const cleanEmail = String(email).toLowerCase().trim();
    let user;
    try {
      user = await User.findOne({ email: cleanEmail });
    } catch (findErr) {
      console.error("[AUTH] Forgot password findOne error:", findErr.stack || findErr.message);
      return res.status(500).json({ message: "Database query error: " + findErr.message });
    }
    
    // Always return success to prevent email enumeration
    if (!user) {
      console.log("[AUTH] Forgot password — no account for:", cleanEmail);
      return res.json({ message: "If an account with that email exists, a reset code has been sent.", sent: true });
    }

    // Server-side cooldown: refuse if last reset OTP was sent < 30s ago
    if (user.resetOtpExpire && new Date(user.resetOtpExpire) > new Date(Date.now() + 9.5 * 60 * 1000)) {
      console.log("[AUTH] Forgot password cooldown for:", cleanEmail);
      return res.json({ message: "If an account with that email exists, a reset code has been sent.", sent: true });
    }

    const otp = generateOtp();
    setResetOtpFields(user, otp);
    
    try {
      await user.save();
    } catch (saveErr) {
      console.error("[AUTH] Forgot password user.save() error:", saveErr.stack || saveErr.message);
      return res.status(500).json({ message: "Database save error: " + saveErr.message });
    }

    try {
      await sendResetOtpEmail(user, otp);
      console.log("[AUTH] Reset OTP sent for:", cleanEmail);
    } catch (error) {
      console.error("[AUTH] FORGOT PASSWORD EMAIL FAILED:", error.stack || error.message);
      try {
        clearResetOtpFields(user);
        await user.save();
      } catch (saveErr) {
        console.error("[AUTH] Safe cleanup error:", saveErr.message);
      }
      return res.status(503).json({
        message: `Could not send reset email. Please try again later. (${error.message})`,
      });
    }

    res.json({ message: "If an account with that email exists, a reset code has been sent.", sent: true });
  } catch (err) {
    console.error("[AUTH] FORGOT PASSWORD ERROR Stack:", err.stack || err);
    res.status(500).json({ message: "Server error: " + (err.message || "Unable to process reset request") });
  }
});

// ═══════════════════════════════════════════════════════════════════════════════
// @route   POST /api/auth/verify-reset-otp
// @desc    Verify password reset OTP (step 1 of reset flow)
// ═══════════════════════════════════════════════════════════════════════════════
router.post("/verify-reset-otp", otpLimiter, async (req, res) => {
  const { email, otp } = req.body;
  try {
    console.log("[AUTH] Verify reset OTP for:", email);

    if (!email || !otp) {
      return res.status(400).json({ message: "Email and reset code are required." });
    }

    const cleanEmail = String(email).toLowerCase().trim();
    const user = await User.findOne({ email: cleanEmail });
    if (!user) {
      return res.status(400).json({ message: "Invalid or expired reset code." });
    }

    if (!isResetOtpValid(user, String(otp).trim())) {
      return res.status(400).json({ message: "Invalid or expired reset code." });
    }

    console.log("[AUTH] Reset OTP verified for:", cleanEmail);
    res.json({ message: "Reset code verified. You can now set a new password.", verified: true });
  } catch (err) {
    console.error("[AUTH] VERIFY RESET OTP ERROR Stack:", err.stack || err);
    res.status(500).json({ message: "Server error: Unable to verify reset code" });
  }
});

// ═══════════════════════════════════════════════════════════════════════════════
// @route   POST /api/auth/reset-password
// @desc    Reset password using OTP verification
// ═══════════════════════════════════════════════════════════════════════════════
router.post("/reset-password", otpLimiter, async (req, res) => {
  try {
    const { email, otp, password } = req.body;
    console.log("[AUTH] Reset password for:", email);

    if (!email || !otp || !password) {
      return res.status(400).json({ message: "Email, reset code, and new password are required." });
    }

    if (password.length < 6) {
      return res.status(400).json({ message: "Password must be at least 6 characters." });
    }

    const cleanEmail = String(email).toLowerCase().trim();
    const user = await User.findOne({ email: cleanEmail });
    if (!user) {
      return res.status(400).json({ message: "Invalid or expired reset code." });
    }

    if (!isResetOtpValid(user, String(otp).trim())) {
      return res.status(400).json({ message: "Invalid or expired reset code." });
    }

    // Update password
    user.password = password;
    clearResetOtpFields(user);
    user.tokenVersion = (user.tokenVersion || 0) + 1; // Invalidate all existing sessions
    // Reset lockout on password change
    user.loginAttempts = 0;
    user.lockUntil = undefined;
    await user.save();
    
    console.log("[AUTH] Password reset successful for:", cleanEmail);
    await safeAuditLog({ userId: user.id, action: 'PASSWORD_RESET', ipAddress: req.ip });

    res.json({ message: "Password updated successfully. Please log in with your new password." });
  } catch (err) {
    console.error("[AUTH] RESET PASSWORD ERROR Stack:", err.stack || err);
    res.status(500).json({ message: "Server error: Unable to reset password" });
  }
});

// ═══════════════════════════════════════════════════════════════════════════════
// @route   POST /api/auth/resend-reset-otp
// @desc    Resend password reset OTP
// ═══════════════════════════════════════════════════════════════════════════════
router.post("/resend-reset-otp", otpLimiter, async (req, res) => {
  const { email } = req.body;
  try {
    console.log("[AUTH] Resend reset OTP for:", email);

    if (!isEmailConfigured()) {
      return res.status(503).json({ message: "Email service is not configured on the server." });
    }

    if (!email) {
      return res.status(400).json({ message: "Email is required." });
    }

    const cleanEmail = String(email).toLowerCase().trim();
    const user = await User.findOne({ email: cleanEmail });
    const genericMsg = "If an account with that email exists, a new reset code has been sent.";
    if (!user) {
      return res.json({ message: genericMsg });
    }

    // Server-side cooldown: refuse if last reset OTP was sent < 30s ago
    if (user.resetOtpExpire && new Date(user.resetOtpExpire) > new Date(Date.now() + 9.5 * 60 * 1000)) {
      console.log("[AUTH] Resend reset OTP too soon for:", cleanEmail);
      return res.status(429).json({ message: "Please wait before requesting another code." });
    }

    const otp = generateOtp();
    setResetOtpFields(user, otp);
    await user.save();

    try {
      await sendResetOtpEmail(user, otp);
    } catch (error) {
      console.error("[AUTH] RESEND RESET OTP EMAIL ERROR:", error.stack || error.message);
      return res.status(503).json({ message: "Could not send reset email. Please try again later." });
    }

    res.json({ message: genericMsg });
  } catch (err) {
    console.error("[AUTH] RESEND RESET OTP ERROR Stack:", err.stack || err);
    res.status(500).json({ message: "Server error: Unable to resend reset code" });
  }
});

// ═══════════════════════════════════════════════════════════════════════════════
// @route   POST /api/auth/logout
// @desc    Clear cookie
// ═══════════════════════════════════════════════════════════════════════════════
router.post("/logout", (req, res) => {
  res.cookie("token", "", {
    httpOnly: true,
    expires: new Date(0),
    secure: process.env.NODE_ENV === "production",
    sameSite: process.env.NODE_ENV === "production" ? "none" : "lax",
  });
  res.json({ message: "Logged out successfully" });
});

// ═══════════════════════════════════════════════════════════════════════════════
// @route   GET /api/auth/me
// @desc    Get user by cookie token
// ═══════════════════════════════════════════════════════════════════════════════
router.get("/me", authMiddleware, async (req, res) => {
  try {
    const user = await User.findById(req.user.userId).select("-password -mfaSecret");
    if (!user) return res.status(404).json({ message: "User not found" });
    res.json(user);
  } catch (err) {
    console.error("[AUTH] GET ME ERROR Stack:", err.stack || err);
    res.status(500).json({ message: "Server error" });
  }
});

// ═══════════════════════════════════════════════════════════════════════════════
// @route   DELETE /api/auth/delete
// @desc    Delete user account
// ═══════════════════════════════════════════════════════════════════════════════
router.delete("/delete", authMiddleware, async (req, res) => {
  try {
    const user = await User.findById(req.user.userId);
    if (!user) return res.status(404).json({ message: "User not found" });

    await User.findByIdAndDelete(req.user.userId);
    // Result model may not be imported — safe delete
    try {
      const Result = require("../models/Result");
      await Result.deleteMany({ user: req.user.userId });
    } catch (_) { /* Result model not available */ }
    await safeAuditLog({ email: user.email, action: 'PASSWORD_RESET', ipAddress: req.ip });

    res.clearCookie("token", { httpOnly: true, secure: true, sameSite: "none" });
    res.json({ message: "User deleted" });
  } catch (err) {
    console.error("[AUTH] DELETE USER ERROR Stack:", err.stack || err);
    res.status(500).json({ message: "Server error" });
  }
});

module.exports = router;
