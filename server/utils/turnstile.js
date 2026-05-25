const axios = require("axios");

const verifyTurnstile = async (token) => {
  if (!token) return false;
  
  try {
    const response = await axios.post(
      "https://challenges.cloudflare.com/turnstile/v0/siteverify",
      new URLSearchParams({
        secret: process.env.TURNSTILE_SECRET_KEY,
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
