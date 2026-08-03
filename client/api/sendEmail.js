import nodemailer from "nodemailer";

export default async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,POST');
  res.setHeader(
    'Access-Control-Allow-Headers',
    'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version'
  );

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  const { to, subject, message, html, user, pass } = req.body;

  if (!to || !subject || (!message && !html) || !user || !pass) {
    return res.status(400).json({ message: 'Missing required fields' });
  }

  try {
    const transporter = nodemailer.createTransport({
      host: "smtp.gmail.com",
      port: 465,
      secure: true,
      connectionTimeout: 30000,
      greetingTimeout: 30000,
      socketTimeout: 30000,
      auth: {
        user: user,
        pass: pass,
      },
    });

    const info = await transporter.sendMail({
      from: `"AI Forensic Lab" <${user}>`,
      to,
      subject,
      text: message,
      html,
    });

    console.log("Vercel Email Proxy: sent successfully | MessageId:", info.messageId);
    return res.status(200).json({ success: true, message: 'Email sent successfully' });
  } catch (error) {
    console.error("Vercel Email Proxy Error:", error.message);
    return res.status(500).json({ success: false, message: error.message });
  }
}
