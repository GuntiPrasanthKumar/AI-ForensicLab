const express = require("express");
const Result = require("../models/Result");
const authMiddleware = require("../middleware/authMiddleware");
const router = express.Router();

// Get all history for user
router.get("/history", authMiddleware, async (req, res) => {
  try {
    const history = await Result.find({ userId: req.user.userId }).sort({ createdAt: -1 });
    res.json(history);
  } catch (err) {
    res.status(500).json({ message: "Failed to fetch history" });
  }
});

// Delete history item
router.delete("/history/:id", authMiddleware, async (req, res) => {
  try {
    // Ensure the item belongs to the user
    const item = await Result.findOne({ _id: req.params.id, userId: req.user.userId });
    if (!item) return res.status(404).json({ message: "Item not found" });

    await Result.findByIdAndDelete(req.params.id);
    res.json({ message: "Item deleted" });
  } catch (err) {
    res.status(500).json({ message: "Deletion failed" });
  }
});

module.exports = router;
