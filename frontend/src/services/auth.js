import { apiService } from './api';

// Fired on window whenever the stored token changes, so components like Navbar can re-check auth
export const AUTH_CHANGED_EVENT = 'fitguard-auth-changed';

export const authService = {
  async login(email, password) {
    return apiService.post('/api/login', { email, password });
  },

  async register(name, email, password) {
    return apiService.post('/api/register', { name, email, password });
},

  async getCurrentUser() {
    return apiService.get('/api/users/me');
  },

  logout() {
    localStorage.removeItem('fitguard_token');
    window.location.href = '/';
  },

  isAuthenticated() {
    return !!localStorage.getItem('fitguard_token');
  },

  getToken() {
    return localStorage.getItem('fitguard_token');
  },

  setToken(token) {
    localStorage.setItem('fitguard_token', token);
    window.dispatchEvent(new Event(AUTH_CHANGED_EVENT));
  },

  async refreshToken() {
    const token = this.getToken();
    if (!token) return null;

    try {
      const response = await apiService.post('/api/token/refresh', {});
      this.setToken(response.access_token);
      return response.access_token;
    } catch (error) {
      this.logout();
      throw error;
    }
  },
};
