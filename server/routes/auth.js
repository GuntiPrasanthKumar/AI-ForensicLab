const express = require("express");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const crypto = require("crypto");
const speakeasy = require("speakeasy");
const qrcode = require("qrcode");
const User = require("../models/User");
const AuditLog = require("../models/AuditLog");
const { authLimiter } = require("../middleware/security");
const authMiddleware = require("../middleware/authMiddleware");
const sendEmail = require("../utils/email");
const { isEmailConfigured, buildOtpEmailHtml } = require("../utils/email");
const { generateOtp, setEmailOtpFields, clearEmailOtpFields, isOtpValid } = require("../utils/otp");
const verifyTurnstile = require("../utils/turnstile");

const router = express.Router();
const JWT_SECRET = process.env.JWT_SECRET || "ai_detector_secret_123";

// Helper to set cookie
const sendTokenCookie = (res, user) => {
  const payload = { userId: user.id, role: user.role, tokenVersion: user.tokenVersion };
  const token = jwt.sign(payload, JWT_SECRET, { expiresIn: "7d" });
  
  res.cookie("token", token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production", // Requires HTTPS in production
    sameSite: process.env.NODE_ENV === "production" ? "none" : "lax",
    maxAge: 7 * 24 * 60 * 60 * 1000 // 7 days
  });
};

async function sendVerificationOtp(user, otp) {
  const message = `Your AI Forensic Lab verification code is: ${otp}\n\nThis code expires in 10 minutes.`;
  const html = buildOtpEmailHtml(otp, user.name);
  await sendEmail({
    email: user.email,
    subject: "Your verification code — AI Forensic Lab",
    message,
    html,
  });
}

// @route   POST /api/auth/register
// @desc    Register user & send email OTP
router.post("/register", authLimiter, async (req, res) => {
  const { name, email, password, turnstileToken } = req.body;
  try {
    if (!isEmailConfigured()) {
      return res.status(503).json({
        message: "Email service is not configured on the server. Contact the administrator.",
      });
    }

    const isValidCaptcha = await verifyTurnstile(turnstileToken);
    if (!isValidCaptcha && process.env.NODE_ENV === "production") {
      return res.status(400).json({ message: "CAPTCHA verification failed" });
    }

    const existing = await User.findOne({ email });
    if (existing) {
      return res.status(400).json({ message: "An account with this email already exists." });
    }

    const otp = generateOtp();
    const user = new User({ name, email, password, isVerified: false });
    setEmailOtpFields(user, otp);
    await user.save();

    try {
      await sendVerificationOtp(user, otp);
    } catch (error) {
      await User.findByIdAndDelete(user._id);
      console.error("REGISTER EMAIL ERROR:", error.message);
      return res.status(503).json({
        message: "Could not send verification email. Check your email address or try again later.",
        details: process.env.NODE_ENV === "development" ? error.message : undefined,
      });
    }

    res.status(201).json({
      message: "Verification code sent to your email.",
      requiresEmailVerification: true,
      email: user.email,
    });
  } catch (err) {
    console.error("REGISTER ERROR:", err);
    res.status(500).json({ message: "Server error" });
  }
});

// @route   POST /api/auth/verify-otp
// @desc    Verify email with 6-digit OTP
router.post("/verify-otp", authLimiter, async (req, res) => {
  const { email, otp } = req.body;
  try {
    if (!email || !otp) {
      return res.status(400).json({ message: "Email and verification code are required." });
    }

    const user = await User.findOne({ email });
    if (!user) {
      return res.status(400).json({ message: "Invalid verification code." });
    }

    if (user.isVerified) {
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

    await AuditLog.create({ userId: user.id, action: "EMAIL_VERIFIED", ipAddress: req.ip });
    sendTokenCookie(res, user);
    res.json({
      message: "Email verified successfully.",
      user: { id: user.id, name: user.name, email: user.email, role: user.role },
    });
  } catch (err) {
    console.error("VERIFY OTP ERROR:", err);
    res.status(500).json({ message: "Server error" });
  }
});

// @route   POST /api/auth/resend-otp
// @desc    Resend email verification OTP
router.post("/resend-otp", authLimiter, async (req, res) => {
  const { email } = req.body;
  try {
    if (!isEmailConfigured()) {
      return res.status(503).json({ message: "Email service is not configured on the server." });
    }

    const user = await User.findOne({ email });
    const genericMsg = "If an unverified account exists, a new code has been sent.";
    if (!user || user.isVerified) {
      return res.json({ message: genericMsg });
    }

    const otp = generateOtp();
    setEmailOtpFields(user, otp);
    await user.save();

    try {
      await sendVerificationOtp(user, otp);
    } catch (error) {
      console.error("RESEND OTP EMAIL ERROR:", error.message);
      return res.status(503).json({
        message: "Could not send verification email. Please try again later.",
        details: process.env.NODE_ENV === "development" ? error.message : undefined,
      });
    }

    res.json({ message: genericMsg, email: user.email });
  } catch (err) {
    res.status(500).json({ message: "Server error" });
  }
});

// @route   GET /api/auth/test-email
// @desc    Test email delivery directly from Render
router.get("/test-email", async (req, res) => {
  try {
    if (!isEmailConfigured()) {
      return res.status(503).json({
        message: "Email not configured. Set RESEND_API_KEY or EMAIL_USER + EMAIL_PASS.",
      });
    }

    const { email } = req.query;
    if (!email) return res.status(400).json({ message: "Provide ?email=your_email@gmail.com" });
    
    await sendEmail({ 
      email: email, 
      subject: "Render Email Test", 
      message: "If you get this, Render is successfully sending emails!" 
    });
    
    res.json({ message: "Email sent successfully from Render!" });
  } catch (error) {
    res.status(500).json({ 
      message: "Failed to send email from Render", 
      error: error.message,
      stack: error.stack
    });
  }
});

// @route   POST /api/auth/verify-email/:token
// @desc    Verify user email
router.post("/verify-email/:token", async (req, res) => {
  try {
    const user = await User.findOne({ verificationToken: req.params.token });
    if (!user) return res.status(400).json({ message: "Invalid or expired verification token" });

    user.isVerified = true;
    user.verificationToken = undefined;
    await user.save();

    sendTokenCookie(res, user);
    res.json({ message: "Email verified successfully", user: { id: user.id, name: user.name, email: user.email, role: user.role } });
  } catch (err) {
    res.status(500).json({ message: "Server error" });
  }
});

// @route   POST /api/auth/login
// @desc    Authenticate user & get token
router.post("/login", authLimiter, async (req, res) => {
  const { email, password, turnstileToken } = req.body;
  try {
    // 1. Verify CAPTCHA (Bypassed temporarily)
    /*
    const isValidCaptcha = await verifyTurnstile(turnstileToken);
    if (!isValidCaptcha && process.env.NODE_ENV === "production") {
      return res.status(400).json({ message: "CAPTCHA verification failed" });
    }
    */

    const user = await User.findOne({ email });
    
    // Generic error
    const invalidCredentialsMsg = "Invalid credentials";
    
    if (!user) {
      await AuditLog.create({ email, action: 'LOGIN_FAILED', ipAddress: req.ip });
      return res.status(400).json({ message: invalidCredentialsMsg });
    }

    // Check Lockout
    if (user.lockUntil && user.lockUntil > Date.now()) {
      await AuditLog.create({ userId: user.id, action: 'ACCOUNT_LOCKED', ipAddress: req.ip });
      return res.status(403).json({ message: "Account locked. Please try again later or reset password." });
    }

    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      user.loginAttempts += 1;
      if (user.loginAttempts >= 5) {
        user.lockUntil = Date.now() + 15 * 60 * 1000; // Lock for 15 mins
      }
      await user.save();
      await AuditLog.create({ userId: user.id, action: 'LOGIN_FAILED', ipAddress: req.ip });
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

    // Check MFA
    if (user.mfaEnabled) {
      // Require OTP - send a temporary token that only allows hitting /mfa/verify
      const tempToken = jwt.sign({ tempUserId: user.id }, JWT_SECRET, { expiresIn: "5m" });
      return res.json({ requiresMfa: true, tempToken });
    }

    await AuditLog.create({ userId: user.id, action: 'LOGIN_SUCCESS', ipAddress: req.ip });
    sendTokenCookie(res, user);
    res.json({ user: { id: user.id, name: user.name, email: user.email, role: user.role } });
  } catch (err) {
    console.error(err);
    res.status(500).json({ message: "Server error" });
  }
});

// @route   POST /api/auth/logout
// @desc    Clear cookie
router.post("/logout", (req, res) => {
  res.clearCookie("token", { httpOnly: true, secure: process.env.NODE_ENV === "production", sameSite: process.env.NODE_ENV === "production" ? "none" : "lax" });
  res.json({ message: "Logged out successfully" });
});

// @route   GET /api/auth/me
// @desc    Get user by cookie token
router.get("/me", authMiddleware, async (req, res) => {
  try {
    const user = await User.findById(req.user.userId).select("-password -mfaSecret");
    if (!user) return res.status(404).json({ message: "User not found" });
    res.json(user);
  } catch (err) {
    res.status(500).json({ message: "Server error" });
  }
});

// @route   POST /api/auth/forgot-password
// @desc    Send reset password email
router.post("/forgot-password", authLimiter, async (req, res) => {
  try {
    const user = await User.findOne({ email: req.body.email });
    const genericMsg = "If an account with that email exists, a password reset link has been sent.";
    
    if (!user) return res.json({ message: genericMsg });

    const resetToken = crypto.randomBytes(20).toString("hex");
    user.resetPasswordToken = crypto.createHash("sha256").update(resetToken).digest("hex");
    user.resetPasswordExpire = Date.now() + 10 * 60 * 1000; // 10 mins
    await user.save();

    const resetUrl = `${process.env.FRONTEND_URL}/reset-password/${resetToken}`;
    const message = `You are receiving this email because you (or someone else) has requested the reset of a password.\n\nPlease make a PUT request to: \n\n ${resetUrl}`;
    
    try {
      await sendEmail({ email: user.email, subject: "Password Reset Token", message });
    } catch (error) {
      user.resetPasswordToken = undefined;
      user.resetPasswordExpire = undefined;
      await user.save();
    }

    res.json({ message: genericMsg });
  } catch (err) {
    res.status(500).json({ message: "Server error" });
  }
});

// @route   POST /api/auth/reset-password/:token
// @desc    Reset password
router.post("/reset-password/:token", async (req, res) => {
  try {
    const resetPasswordToken = crypto.createHash("sha256").update(req.params.token).digest("hex");
    
    const user = await User.findOne({
      resetPasswordToken,
      resetPasswordExpire: { $gt: Date.now() }
    });

    if (!user) return res.status(400).json({ message: "Invalid or expired token" });

    user.password = req.body.password;
    user.resetPasswordToken = undefined;
    user.resetPasswordExpire = undefined;
    user.tokenVersion += 1; // Invalidate all existing sessions
    await user.save();
    
    await AuditLog.create({ userId: user.id, action: 'PASSWORD_RESET', ipAddress: req.ip });

    res.json({ message: "Password updated successfully. Please log in with your new password." });
  } catch (err) {
    res.status(500).json({ message: "Server error" });
  }
});

// @route   POST /api/auth/mfa/setup
// @desc    Generate MFA QR Code
router.post("/mfa/setup", authMiddleware, async (req, res) => {
  try {
    const secret = speakeasy.generateSecret({ name: `AI Forensic Lab (${req.user.email})` });
    
    const user = await User.findById(req.user.userId);
    user.mfaSecret = secret.base32;
    await user.save();

    qrcode.toDataURL(secret.otpauth_url, (err, data_url) => {
      if (err) return res.status(500).json({ message: "Error generating QR code" });
      res.json({ qrCodeUrl: data_url, secret: secret.base32 });
    });
  } catch (err) {
    res.status(500).json({ message: "Server error" });
  }
});

// @route   POST /api/auth/mfa/verify
// @desc    Verify MFA token (either during setup or login)
router.post("/mfa/verify", async (req, res) => {
  const { token, isSetup, tempToken } = req.body; // isSetup = true if verifying during setup from Dashboard
  
  try {
    let user;
    if (isSetup) {
      // Setup phase - user must be fully logged in (needs authMiddleware, but let's handle manually or via token param)
      // Since it's easier, we'll extract from HttpCookie
      const cookieToken = req.cookies.token;
      if (!cookieToken) return res.status(401).json({ message: "Unauthorized" });
      const decoded = jwt.verify(cookieToken, JWT_SECRET);
      user = await User.findById(decoded.userId);
    } else {
      // Login phase - user has a tempToken
      if (!tempToken) return res.status(401).json({ message: "Unauthorized" });
      const decoded = jwt.verify(tempToken, JWT_SECRET);
      user = await User.findById(decoded.tempUserId);
    }

    if (!user) return res.status(400).json({ message: "User not found" });

    const verified = speakeasy.totp.verify({
      secret: user.mfaSecret,
      encoding: 'base32',
      token: token
    });

    if (!verified) return res.status(400).json({ message: "Invalid MFA token" });

    if (isSetup) {
      user.mfaEnabled = true;
      await user.save();
      await AuditLog.create({ userId: user.id, action: 'MFA_ENABLED', ipAddress: req.ip });
      res.json({ message: "MFA Setup successful" });
    } else {
      // Complete login
      sendTokenCookie(res, user);
      res.json({ user: { id: user.id, name: user.name, email: user.email, role: user.role } });
    }
  } catch (err) {
    res.status(500).json({ message: "Server error" });
  }
});

// @route   POST /api/auth/logout
// @desc    Logout user and clear cookie
router.post("/logout", (req, res) => {
  res.cookie("token", "", {
    httpOnly: true,
    expires: new Date(0),
    secure: process.env.NODE_ENV === "production",
    sameSite: process.env.NODE_ENV === "production" ? "none" : "lax",
  });
  res.json({ message: "Logged out successfully" });
});

module.exports = router;
