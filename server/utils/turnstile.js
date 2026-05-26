const axios = require("axios");

const CLOUDFLARE_TEST_SECRET = "1x0000000000000000000000000000000AA";

const verifyTurnstile = async (token) => {
  if (!token) return false;

  const secret = process.env.TURNSTILE_SECRET_KEY;
  if (!secret) {
    console.warn("TURNSTILE_SECRET_KEY not set — skipping CAPTCHA verification");
    return true;
  }

  // Cloudflare dummy widget (used when VITE_TURNSTILE_SITE_KEY is not set on Vercel)
  if (secret === CLOUDFLARE_TEST_SECRET) {
    return true;
  }
  
  try {
    const response = await axios.post(
      "https://challenges.cloudflare.com/turnstile/v0/siteverify",
      new URLSearchParams({
        secret,
        response: token,
      }).toString(),
      {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      }
    );
    
    return response.data.success;
  } catch (error) {
    console.error("Turnstile verification error:", error);
    return false;
  }
};

module.exports = verifyTurnstile;
