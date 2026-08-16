/**
 * Health Check Utility
 */
function getHealthStatus() {
  return {
    status: 'UP',
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  };
}

module.exports = { getHealthStatus };
