const axios = require("axios");

const CLOUDFLARE_TEST_SECRET = "1x0000000000000000000000000000000AA";

const verifyTurnstile = async (token) => {
  if (!token) return { success: false, errorCodes: ["missing-token"] };

  const secret = process.env.TURNSTILE_SECRET_KEY;
  if (!secret) {
    console.warn("TURNSTILE_SECRET_KEY not set — skipping CAPTCHA verification");
    return { success: true };
  }

  // Cloudflare dummy widget (used when VITE_TURNSTILE_SITE_KEY is not set on Vercel)
  if (secret.trim() === CLOUDFLARE_TEST_SECRET) {
    return { success: true };
  }
  
  try {
    const response = await axios.post(
      "https://challenges.cloudflare.com/turnstile/v0/siteverify",
      new URLSearchParams({
        secret: secret.trim(),
        response: token.trim(),
      }).toString(),
      {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      }
    );
    
    console.log("Turnstile response:", response.data);
    return {
      success: !!response.data.success,
      errorCodes: response.data["error-codes"] || [],
    };
  } catch (error) {
    console.error("Turnstile verification exception:", error.message);
    return { success: false, errorCodes: [error.message] };
  }
};

module.exports = verifyTurnstile;
