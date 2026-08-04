const mongoose = require("mongoose");
const env = require("./env");

const connectDB = async () => {
  try {
    if (!env.MONGO_URI) {
      console.warn("[Database Warning] MONGO_URI missing. System running without MongoDB persistence.");
      return;
    }
    const conn = await mongoose.connect(env.MONGO_URI);
    console.log(`[Database] MongoDB Connected: ${conn.connection.host}`);
  } catch (err) {
    console.error(`[Database Error] Connection failed: ${err.message}`);
  }
};

module.exports = connectDB;
