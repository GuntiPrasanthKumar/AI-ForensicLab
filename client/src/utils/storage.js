/**
 * Local Session Cache Storage Utility
 */
export const storage = {
  get: (key) => JSON.parse(sessionStorage.getItem(key) || 'null'),
  set: (key, val) => sessionStorage.setItem(key, JSON.stringify(val)),
  clear: () => sessionStorage.clear()
};
