const nodemailer = require("nodemailer");
const dns = require("node:dns");

// Force IPv4 DNS resolution globally — prevents 30s+ delays when IPv6 fails
dns.setDefaultResultOrder("ipv4first");

function isEmailConfigured() {
  if (process.env.RESEND_API_KEY) return true;
  return Boolean(process.env.EMAIL_USER && process.env.EMAIL_PASS);
}

function buildOtpEmailHtml(otp, name) {
  return `
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 24px; background: #0a0a0a; color: #fff; border-radius: 12px;">
      <h2 style="color: #3b82f6; margin-top: 0;">AI Forensic Lab</h2>
      <p>Hi ${name || "there"},</p>
      <p>Your email verification code is:</p>
      <p style="font-size: 32px; font-weight: bold; letter-spacing: 8px; text-align: center; color: #60a5fa; margin: 24px 0;">${otp}</p>
      <p style="color: #9ca3af; font-size: 14px;">This code expires in 10 minutes. If you did not create an account, you can ignore this email.</p>
    </div>
  `;
}

function buildResetOtpEmailHtml(otp, name) {
  return `
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 24px; background: #0a0a0a; color: #fff; border-radius: 12px;">
      <h2 style="color: #3b82f6; margin-top: 0;">AI Forensic Lab</h2>
      <p>Hi ${name || "there"},</p>
      <p>You requested a password reset. Your verification code is:</p>
      <p style="font-size: 32px; font-weight: bold; letter-spacing: 8px; text-align: center; color: #f59e0b; margin: 24px 0;">${otp}</p>
      <p style="color: #9ca3af; font-size: 14px;">This code expires in 10 minutes. If you did not request a password reset, you can safely ignore this email — your password will remain unchanged.</p>
    </div>
  `;
}

/**
 * Sleep helper for retry backoff.
 */
function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function sendViaResend({ email, subject, message, html }) {
  const from = process.env.EMAIL_FROM || "AI Forensic Lab <onboarding@resend.dev>";
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);

  console.log("[EMAIL] Resend: sending to", email, "| Subject:", subject);

  const response = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.RESEND_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from,
      to: [email],
      subject,
      text: message,
      html: html || undefined,
    }),
    signal: controller.signal,
  });
  clearTimeout(timeout);

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    console.error("[EMAIL] Resend API error:", response.status, data);
    throw new Error(data.message || `Resend API error (${response.status})`);
  }
  console.log("[EMAIL] Resend: sent successfully | ID:", data.id);
  return data;
}

async function sendViaGmail({ email, subject, message, html }) {
  // If in production on Render, SMTP is blocked. Route through Vercel serverless proxy.
  if (process.env.NODE_ENV === "production") {
    const proxyUrl = "https://ai-forensic-lab.vercel.app/api/sendEmail";
    console.log("[EMAIL] Gmail (Vercel proxy): sending to", email, "| Subject:", subject);
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 20000);
      const response = await fetch(proxyUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          to: email,
          subject,
          message,
          html,
          user: process.env.EMAIL_USER,
          pass: process.env.EMAIL_PASS
        }),
        signal: controller.signal,
      });
      clearTimeout(timeout);
      const data = await response.json();
      if (!response.ok) throw new Error(data.message || "Proxy error");
      console.log("[EMAIL] Gmail (Vercel proxy): sent successfully");
      return data;
    } catch (err) {
      console.error("[EMAIL] Gmail (Vercel proxy) failed:", err.message);
      throw new Error(`Vercel Email Proxy failed: ${err.message}`);
    }
  }

  // Local development: use standard SMTP
  console.log("[EMAIL] Gmail SMTP: sending to", email, "| Subject:", subject);
  const transporter = nodemailer.createTransport({
    host: "smtp.gmail.com",
    port: 465,
    secure: true,
    connectionTimeout: 45000,
    greetingTimeout: 30000,
    socketTimeout: 45000,
    auth: {
      user: process.env.EMAIL_USER,
      pass: process.env.EMAIL_PASS,
    },
    // Force IPv4 to prevent IPv6 connection failures causing 30s+ delays
    dnsOptions: { family: 4 },
  });

  const result = await transporter.sendMail({
    from: `"AI Forensic Lab" <${process.env.EMAIL_USER}>`,
    to: email,
    subject,
    text: message,
    html,
  });
  console.log("[EMAIL] Gmail SMTP: sent successfully | MessageId:", result.messageId);
  return result;
}

/**
 * Send an email with automatic retry (up to 2 retries with exponential backoff).
 * Tries Resend first if RESEND_API_KEY is set, otherwise falls back to Gmail.
 */
const sendEmail = async (options) => {
  if (!isEmailConfigured()) {
    const errMsg = process.env.NODE_ENV === "production"
      ? "In production, set RESEND_API_KEY (Render blocks Gmail SMTP)."
      : "Email is not configured. Set EMAIL_USER + EMAIL_PASS (Gmail app password) for local dev.";
    console.error("[EMAIL] Not configured:", errMsg);
    throw new Error(errMsg);
  }

  const provider = process.env.RESEND_API_KEY ? "Resend" : "Gmail";
  const sendFn = process.env.RESEND_API_KEY ? sendViaResend : sendViaGmail;
  const maxRetries = 2;

  for (let attempt = 1; attempt <= maxRetries + 1; attempt++) {
    try {
      console.log(`[EMAIL] Attempt ${attempt}/${maxRetries + 1} via ${provider} to ${options.email}`);
      const result = await sendFn(options);
      return result;
    } catch (err) {
      console.error(`[EMAIL] Attempt ${attempt} failed:`, err.message);
      if (attempt <= maxRetries) {
        const backoff = attempt * 2000; // 2s, 4s
        console.log(`[EMAIL] Retrying in ${backoff}ms...`);
        await sleep(backoff);
      } else {
        console.error(`[EMAIL] All ${maxRetries + 1} attempts failed for ${options.email}`);
        throw err;
      }
    }
  }
};

module.exports = sendEmail;
module.exports.isEmailConfigured = isEmailConfigured;
module.exports.buildOtpEmailHtml = buildOtpEmailHtml;
module.exports.buildResetOtpEmailHtml = buildResetOtpEmailHtml;
