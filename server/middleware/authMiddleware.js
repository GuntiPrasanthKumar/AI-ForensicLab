const jwt = require("jsonwebtoken");
const User = require("../models/User");

const authMiddleware = async (req, res, next) => {
  // Extract token from HttpOnly cookie
  const token = req.cookies.token;
  
  if (!token) {
    return res.status(401).json({ message: "No token, authorization denied" });
  }

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET || "ai_detector_secret_123");
    
    // Verify user exists and token version matches (for invalidating sessions on password reset)
    const user = await User.findById(decoded.userId);
    if (!user) {
       return res.status(401).json({ message: "User no longer exists" });
    }
    
    if (user.tokenVersion !== decoded.tokenVersion) {
       return res.status(401).json({ message: "Session expired. Please log in again." });
    }

    req.user = decoded; // { userId, role, tokenVersion }
    next();
  } catch (err) {
    res.status(401).json({ message: "Token is not valid" });
  }
};

module.exports = authMiddleware;
