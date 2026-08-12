/**
 * File Upload Validation Helper
 */
export function validateImageFile(file) {
  const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
  const maxSizeMB = 15;
  if (!validTypes.includes(file.type)) return { valid: false, reason: 'Invalid format' };
  if (file.size > maxSizeMB * 1024 * 1024) return { valid: false, reason: 'File too large' };
  return { valid: true };
}
