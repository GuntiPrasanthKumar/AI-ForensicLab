const crypto = require("crypto");

/**
 * Generate a cryptographically secure 6-digit OTP.
 * Uses crypto.randomInt (CSPRNG) instead of Math.random.
 */
function generateOtp() {
  const otp = String(crypto.randomInt(100000, 1000000));
  console.log("[OTP] Generated OTP (last 2 digits):", `****${otp.slice(-2)}`);
  return otp;
}

/**
 * Hash an OTP with SHA-256 for secure storage.
 */
function hashOtp(otp) {
  return crypto.createHash("sha256").update(String(otp).trim()).digest("hex");
}

// ─── Registration OTP ────────────────────────────────────────────────────────

/**
 * Set email verification OTP fields on a user document.
 * Does NOT touch isVerified — that's the caller's responsibility.
 */
function setEmailOtpFields(user, otp) {
  user.emailOtp = hashOtp(otp);
  user.emailOtpExpire = new Date(Date.now() + 10 * 60 * 1000); // 10 minutes
  console.log("[OTP] Registration OTP stored for:", user.email, "| Expires:", user.emailOtpExpire.toISOString());
}

/**
 * Clear email verification OTP fields after successful verification.
 */
function clearEmailOtpFields(user) {
  user.emailOtp = undefined;
  user.emailOtpExpire = undefined;
  console.log("[OTP] Registration OTP cleared for:", user.email);
}

/**
 * Validate a registration OTP against stored hash and expiration.
 */
function isOtpValid(user, otp) {
  if (!user.emailOtp || !user.emailOtpExpire) {
    console.log("[OTP] Validation failed — no OTP stored for:", user.email);
    return false;
  }
  if (new Date(user.emailOtpExpire) < new Date()) {
    console.log("[OTP] Validation failed — OTP expired for:", user.email, "| Expired at:", user.emailOtpExpire);
    return false;
  }
  const valid = user.emailOtp === hashOtp(otp);
  console.log("[OTP] Registration OTP validation:", valid ? "SUCCESS" : "FAILED", "for:", user.email);
  return valid;
}

// ─── Password Reset OTP ─────────────────────────────────────────────────────

/**
 * Set password-reset OTP fields on a user document.
 * Completely independent from registration OTP.
 */
function setResetOtpFields(user, otp) {
  user.resetOtp = hashOtp(otp);
  user.resetOtpExpire = new Date(Date.now() + 10 * 60 * 1000); // 10 minutes
  console.log("[OTP] Reset OTP stored for:", user.email, "| Expires:", user.resetOtpExpire.toISOString());
}

/**
 * Clear password-reset OTP fields after use or expiration.
 */
function clearResetOtpFields(user) {
  user.resetOtp = undefined;
  user.resetOtpExpire = undefined;
  // Also clear legacy token fields
  user.resetPasswordToken = undefined;
  user.resetPasswordExpire = undefined;
  console.log("[OTP] Reset OTP cleared for:", user.email);
}

/**
 * Validate a password-reset OTP.
 */
function isResetOtpValid(user, otp) {
  if (!user.resetOtp || !user.resetOtpExpire) {
    console.log("[OTP] Reset validation failed — no reset OTP stored for:", user.email);
    return false;
  }
  if (new Date(user.resetOtpExpire) < new Date()) {
    console.log("[OTP] Reset validation failed — OTP expired for:", user.email, "| Expired at:", user.resetOtpExpire);
    return false;
  }
  const valid = user.resetOtp === hashOtp(otp);
  console.log("[OTP] Reset OTP validation:", valid ? "SUCCESS" : "FAILED", "for:", user.email);
  return valid;
}

module.exports = {
  generateOtp,
  hashOtp,
  setEmailOtpFields,
  clearEmailOtpFields,
  isOtpValid,
  setResetOtpFields,
  clearResetOtpFields,
  isResetOtpValid,
};
