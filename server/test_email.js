require("dotenv").config();
const sendEmail = require("./utils/email");
const { isEmailConfigured } = require("./utils/email");

async function testEmail() {
  const to = process.argv[2];
  if (!to) {
    console.error("Usage: node test_email.js recipient@example.com");
    process.exit(1);
  }

  if (!isEmailConfigured()) {
    console.error("Set RESEND_API_KEY or EMAIL_USER + EMAIL_PASS in server/.env");
    process.exit(1);
  }

  try {
    await sendEmail({
      email: to,
      subject: "Test Email — AI Forensic Lab",
      message: "If you received this, email delivery is working.",
    });
    console.log("Email sent successfully to", to);
  } catch (error) {
    console.error("Failed to send email:", error.message);
    process.exit(1);
  }
}

testEmail();
