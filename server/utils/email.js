const nodemailer = require("nodemailer");

const sendEmail = async (options) => {
  // Create a transporter using Gmail
  const transporter = nodemailer.createTransport({
    service: "gmail",
    auth: {
      user: process.env.EMAIL_USER, // e.g. your_email@gmail.com
      pass: process.env.EMAIL_PASS, // e.g. 16-character App Password
    },
  });

  const mailOptions = {
    from: `"AI Forensic Lab" <${process.env.EMAIL_USER}>`,
    to: options.email,
    subject: options.subject,
    text: options.message,
    html: options.html,
  };

  await transporter.sendMail(mailOptions);
};

module.exports = sendEmail;
