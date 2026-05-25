const mongoose = require("mongoose");
require("dotenv").config();
const User = require("../models/User");

async function migrate() {
  try {
    await mongoose.connect(process.env.MONGO_URI);
    console.log("MongoDB Connected for migration");

    const result = await User.updateMany(
      { isVerified: { $exists: false } },
      { 
        $set: { 
          isVerified: true, 
          role: "user", 
          loginAttempts: 0, 
          mfaEnabled: false, 
          tokenVersion: 0 
        } 
      }
    );

    console.log(`Migration completed. Updated ${result.modifiedCount} users.`);
    process.exit(0);
  } catch (err) {
    console.error("Migration failed:", err);
    process.exit(1);
  }
}

migrate();
