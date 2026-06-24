export const API_CONFIG = {
  // In development, BASE_URL is empty so Vite proxy intercepts /api/* calls.
  // In production, set VITE_API_URL to your deployed backend URL.
  BASE_URL: import.meta.env.VITE_API_URL || '',
  TIMEOUT: 30000,
};
