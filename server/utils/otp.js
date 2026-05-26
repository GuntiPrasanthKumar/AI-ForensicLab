const crypto = require("crypto");

function generateOtp() {
  return String(Math.floor(100000 + Math.random() * 900000));
}

function hashOtp(otp) {
  return crypto.createHash("sha256").update(otp).digest("hex");
}

function setEmailOtpFields(user, otp) {
  user.emailOtp = hashOtp(otp);
  user.emailOtpExpire = Date.now() + 10 * 60 * 1000;
  user.isVerified = false;
}

function clearEmailOtpFields(user) {
  user.emailOtp = undefined;
  user.emailOtpExpire = undefined;
}

function isOtpValid(user, otp) {
  if (!user.emailOtp || !user.emailOtpExpire) return false;
  if (user.emailOtpExpire < Date.now()) return false;
  return user.emailOtp === hashOtp(otp);
}

module.exports = {
  generateOtp,
  hashOtp,
  setEmailOtpFields,
  clearEmailOtpFields,
  isOtpValid,
};
