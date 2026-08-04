function validateRegisterInput(body) {
  const { name, email, password } = body || {};
  if (!name || !email || !password) {
    return "Name, email, and password are required.";
  }
  if (typeof email !== "string" || !email.includes("@")) {
    return "Please enter a valid email address.";
  }
  if (typeof password !== "string" || password.length < 6) {
    return "Password must be at least 6 characters long.";
  }
  return null;
}

function validateLoginInput(body) {
  const { email, password } = body || {};
  if (!email || !password) {
    return "Email and password are required.";
  }
  return null;
}

module.exports = {
  validateRegisterInput,
  validateLoginInput
};
