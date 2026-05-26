const nodemailer = require("nodemailer");

const sendEmail = async (options) => {
  // Create a transporter using Gmail with explicit IPv4 settings
  const transporter = nodemailer.createTransport({
    host: "smtp.gmail.com",
    port: 465,
    secure: true,
    auth: {
      user: process.env.EMAIL_USER, // e.g. your_email@gmail.com
      pass: process.env.EMAIL_PASS, // e.g. 16-character App Password
    },
    tls: {
      rejectUnauthorized: false
    }
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
