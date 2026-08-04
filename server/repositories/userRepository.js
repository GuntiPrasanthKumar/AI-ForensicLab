const User = require("../models/User");

class UserRepository {
  async findByEmail(email) {
    if (!email) return null;
    return await User.findOne({ email: email.toLowerCase().trim() });
  }

  async findById(id) {
    return await User.findById(id);
  }

  async create(userData) {
    return await User.create(userData);
  }

  async save(userInstance) {
    return await userInstance.save();
  }
}

module.exports = new UserRepository();
