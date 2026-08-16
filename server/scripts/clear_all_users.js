const mongoose = require("mongoose");
const path = require("path");
require("dotenv").config({ path: path.join(__dirname, "..", ".env") });

const User = require("../models/User");
const Result = require("../models/Result");
const AuditLog = require("../models/AuditLog");

async function clearAllUserAccounts() {
  const mongoUri = process.env.MONGO_URI;
  if (!mongoUri) {
    console.error("[ERROR] MONGO_URI is missing from server/.env file.");
    process.exit(1);
  }

  try {
    console.log("[CLEAR ACCOUNTS] Connecting to MongoDB database...");
    await mongoose.connect(mongoUri);
    console.log("[CLEAR ACCOUNTS] Connected successfully.");

    const initialUserCount = await User.countDocuments();
    console.log(`[CLEAR ACCOUNTS] Found ${initialUserCount} registered user account(s) in MongoDB.`);

    if (initialUserCount === 0) {
      console.log("[CLEAR ACCOUNTS] No user accounts found in database. Nothing to delete.");
    } else {
      const deleteUsersRes = await User.deleteMany({});
      console.log(`[CLEAR ACCOUNTS] Successfully deleted ${deleteUsersRes.deletedCount} user account(s).`);

      const deleteResultsRes = await Result.deleteMany({});
      console.log(`[CLEAR ACCOUNTS] Cleared ${deleteResultsRes.deletedCount} user analysis result(s).`);

      const deleteAuditRes = await AuditLog.deleteMany({});
      console.log(`[CLEAR ACCOUNTS] Cleared ${deleteAuditRes.deletedCount} user audit log record(s).`);
    }

    const remainingCount = await User.countDocuments();
    console.log(`[CLEAR ACCOUNTS] Remaining registered accounts in database: ${remainingCount}`);

    console.log("[CLEAR ACCOUNTS] Database cleanup completed successfully.");
    await mongoose.disconnect();
    process.exit(0);
  } catch (error) {
    console.error("[CLEAR ACCOUNTS ERROR] Failed to delete user accounts:", error.message || error);
    if (mongoose.connection.readyState !== 0) {
      await mongoose.disconnect();
    }
    process.exit(1);
  }
}

clearAllUserAccounts();
