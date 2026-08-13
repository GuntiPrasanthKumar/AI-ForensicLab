/**
 * Server Logging Configuration
 */
module.exports = {
  level: process.env.LOG_LEVEL || 'info',
  format: 'json'
};
