export const API_CONFIG = {
  BASE_URL: import.meta.env.REACT_APP_BACKEND_URL || 'http://localhost:8000/api',
  AUTH: {
    username: import.meta.env.VITE_AUTH_USERNAME || '',
    password: import.meta.env.VITE_AUTH_PASSWORD || ''
  }
};

// Add validation to warn if credentials are missing
if (!import.meta.env.VITE_AUTH_USERNAME || !import.meta.env.VITE_AUTH_PASSWORD) {
  console.warn('Authentication credentials not provided in environment variables. Some API calls may fail.');
}
