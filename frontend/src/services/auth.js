import { apiService } from './api';
import { session, AUTH_CHANGED_EVENT } from './session';

export { AUTH_CHANGED_EVENT };

export const authService = {
  async login(email, password) {
    const response = await apiService.post('/api/login', { email, password });
    session.start(response);
    return response;
  },

  async register(name, email, password) {
    const response = await apiService.post('/api/register', { name, email, password });
    session.start(response);
    return response;
  },

  async getCurrentUser() {
    return apiService.get('/api/users/me');
  },

  async logout() {
    try {
      // Revokes the refresh token server-side and clears the httpOnly cookie
      await apiService.post('/api/auth/logout', {});
    } catch {
      // Still end the local session if the server can't be reached
    }
    session.clear();
    window.location.href = '/';
  },

  isAuthenticated() {
    return session.isAuthenticated();
  },

  /** Resolves once the session from a previous visit (if any) has been restored. */
  restoreSession() {
    return session.restore();
  },

  clearSession() {
    session.clear();
  },
};
