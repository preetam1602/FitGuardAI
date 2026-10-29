import { API_CONFIG } from '../config/api';
import { session } from './session';

class ApiService {
  constructor() {
    this.baseURL = API_CONFIG.BASE_URL;
    this.timeout = API_CONFIG.TIMEOUT;
  }

  async request(endpoint, options = {}, isRetry = false) {
    const url = `${this.baseURL}${endpoint}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    const token = session.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        credentials: 'include', // sends the refresh cookie to /api/auth/* when the API is on another origin
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      // Access tokens are short-lived: on expiry, refresh once from the cookie and retry
      if (response.status === 401 && token && !isRetry && (await session.refresh())) {
        return this.request(endpoint, options, true);
      }

      if (response.status === 204) {
        return null;
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        // FastAPI validation errors (422) carry a list of {loc, msg} objects rather than a string
        const detail = Array.isArray(errorData.detail)
          ? errorData.detail.map((d) => d.msg?.replace(/^Value error, /, '')).join('; ')
          : errorData.detail;
        const httpError = new Error(detail || `HTTP error! status: ${response.status}`);
        httpError.status = response.status;
        throw httpError;
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        throw new Error('Request timeout');
      }
      if (error instanceof TypeError) {
        throw new Error(
          'Unable to connect to the server. Make sure the backend is running on port 3001.'
        );
      }
      throw error;
    }
  }

  async get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  }

  async post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }
}

export const apiService = new ApiService();
