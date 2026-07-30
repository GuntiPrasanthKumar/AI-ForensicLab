/**
 * Validates uploaded file size and type before sending to the forensic backend.
 * 
 * @param {File} file - The file object to validate
 * @param {Object} options - Validation constraints
 * @param {number} [options.maxSizeMB=50] - Maximum file size in MB
 * @param {Array<string>} [options.allowedTypes=[]] - List of allowed MIME prefixes or extensions
 * @returns {{ valid: boolean, error?: string }}
 */
export const validateUploadFile = (file, options = {}) => {
  if (!file) {
    return { valid: false, error: "No file selected." };
  }

  const maxSizeMB = options.maxSizeMB || 50;
  const maxSizeBytes = maxSizeMB * 1024 * 1024;

  if (file.size > maxSizeBytes) {
    return { 
      valid: false, 
      error: `File size exceeds ${maxSizeMB}MB limit. Please upload a smaller file.` 
    };
  }

  if (options.allowedTypes && options.allowedTypes.length > 0) {
    const isAllowed = options.allowedTypes.some((type) => 
      file.type.startsWith(type) || file.name.toLowerCase().endsWith(type)
    );
    if (!isAllowed) {
      return { 
        valid: false, 
        error: `Unsupported file format (${file.type || file.name}).` 
      };
    }
  }

  return { valid: true };
};
