import { API_CONFIG } from '../config/api';

// Fired on window whenever the session starts or ends, so components like Navbar can re-check auth
export const AUTH_CHANGED_EVENT = 'fitguard-auth-changed';

// The access token lives only in memory, never in localStorage, so injected scripts can't
// lift it from storage. On page load it is recovered from the httpOnly refresh cookie.
let accessToken = null;
let currentUser = null;
let refreshPromise = null;
let restorePromise = null;

const notify = () => window.dispatchEvent(new Event(AUTH_CHANGED_EVENT));

async function requestRefresh() {
  try {
    const response = await fetch(`${API_CONFIG.BASE_URL}/api/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
    });
    if (!response.ok) {
      session.clear();
      return null;
    }
    session.start(await response.json());
    return accessToken;
  } catch {
    return null; // network error: keep the current state, the caller sees the refresh failed
  }
}

export const session = {
  getToken: () => accessToken,
  getUser: () => currentUser,
  isAuthenticated: () => !!accessToken,

  start({ access_token, user }) {
    accessToken = access_token;
    currentUser = user ?? currentUser;
    notify();
  },

  clear() {
    const wasAuthenticated = !!accessToken;
    accessToken = null;
    currentUser = null;
    if (wasAuthenticated) notify();
  },

  /**
   * Get a fresh access token from the refresh cookie; resolves to the token or null.
   * Each refresh rotates the cookie and the server treats a reused one as stolen, so concurrent
   * refreshes are merged within this tab and serialised across tabs with the Web Locks API.
   */
  refresh() {
    if (!refreshPromise) {
      const run = navigator.locks
        ? () => navigator.locks.request('fitguard-refresh', requestRefresh)
        : requestRefresh;
      refreshPromise = run().finally(() => {
        refreshPromise = null;
      });
    }
    return refreshPromise;
  },

  /** Restore the session once per page load; later calls reuse the same result. */
  restore() {
    if (!restorePromise) {
      try {
        localStorage.removeItem('fitguard_token'); // drop tokens stored by older versions
      } catch {
        // storage unavailable (e.g. blocked); nothing to clean up
      }
      restorePromise = session.refresh();
    }
    return restorePromise;
  },
};
