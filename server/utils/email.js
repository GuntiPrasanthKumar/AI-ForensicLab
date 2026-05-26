const nodemailer = require("nodemailer");

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

async function sendViaResend({ email, subject, message, html }) {
  const from = process.env.EMAIL_FROM || "AI Forensic Lab <onboarding@resend.dev>";
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
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
    throw new Error(data.message || `Resend API error (${response.status})`);
  }
  return data;
}

async function sendViaGmail({ email, subject, message, html }) {
  // If in production on Render, SMTP is blocked. Route through Vercel serverless proxy.
  if (process.env.NODE_ENV === "production") {
    const proxyUrl = "https://ai-forensic-lab.vercel.app/api/sendEmail";
    try {
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
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message || "Proxy error");
      return data;
    } catch (err) {
      throw new Error(`Vercel Email Proxy failed: ${err.message}`);
    }
  }

  // Local development: use standard SMTP
  const transporter = nodemailer.createTransport({
    host: "smtp.gmail.com",
    port: 465,
    secure: true,
    connectionTimeout: 10000,
    greetingTimeout: 10000,
    socketTimeout: 10000,
    auth: {
      user: process.env.EMAIL_USER,
      pass: process.env.EMAIL_PASS,
    },
  });

  return transporter.sendMail({
    from: `"AI Forensic Lab" <${process.env.EMAIL_USER}>`,
    to: email,
    subject,
    text: message,
    html,
    timeout: 12000,
  });
}

const sendEmail = async (options) => {
  if (!isEmailConfigured()) {
    throw new Error(
      process.env.NODE_ENV === "production"
        ? "In production, set RESEND_API_KEY (Render blocks Gmail SMTP)."
        : "Email is not configured. Set EMAIL_USER + EMAIL_PASS (Gmail app password) for local dev."
    );
  }

  if (process.env.RESEND_API_KEY) {
    return sendViaResend(options);
  }

  return sendViaGmail(options);
};

module.exports = sendEmail;
module.exports.isEmailConfigured = isEmailConfigured;
module.exports.buildOtpEmailHtml = buildOtpEmailHtml;
