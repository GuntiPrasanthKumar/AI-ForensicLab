const Result = require("../models/Result");

class ResultRepository {
  async create(resultData) {
    return await Result.create(resultData);
  }

  async findByUserId(userId, limit = 50) {
    return await Result.find({ userId }).sort({ createdAt: -1 }).limit(limit);
  }
}

module.exports = new ResultRepository();
