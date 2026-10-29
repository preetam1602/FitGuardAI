import { apiService } from './api';
import { API_CONFIG } from '../config/api';
import { session } from './session';

// Diet generation streams progress, so it gets a longer overall limit than normal API calls
const DIET_STREAM_TIMEOUT = 120000;

export const healthService = {
  async getPrediction(data) {
    return apiService.post('/api/predict', data);
  },

  async submitHealthAssessment(data) {
    return apiService.post('/api/health-assessment', data);
  },

  async getDietByRecord(recordId) {
    return apiService.get(`/api/records/${recordId}/diet`);
  },

  async getDietsByUser(userId) {
    return apiService.get(`/api/users/${userId}/diets`);
  },

  /**
   * Generate the diet blueprint for a saved record, calling onEvent(event, data) for each
   * Server-Sent Event: status / draft / final / error. Resolves when the stream ends.
   * EventSource can't POST or send an Authorization header, so the stream is read via fetch.
   */
  async streamDietForRecord(recordId, onEvent) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), DIET_STREAM_TIMEOUT);
    const open = () => {
      const token = session.getToken();
      return fetch(`${API_CONFIG.BASE_URL}/api/records/${recordId}/diet/stream`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        signal: controller.signal,
      });
    };

    try {
      let response = await open();
      // Expired access token: refresh once from the cookie and reopen the stream
      if (response.status === 401 && (await session.refresh())) {
        response = await open();
      }
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const httpError = new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        httpError.status = response.status;
        throw httpError;
      }

      const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
      let buffer = '';
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += value;
        // Events are separated by a blank line; keep any trailing partial event in the buffer
        const parts = buffer.split('\n\n');
        buffer = parts.pop();
        for (const part of parts) {
          let event = 'message';
          let data = '';
          for (const line of part.split('\n')) {
            if (line.startsWith('event:')) event = line.slice(6).trim();
            else if (line.startsWith('data:')) data += line.slice(5).trim();
          }
          if (data) onEvent(event, JSON.parse(data)); // comment-only keepalives carry no data
        }
      }
    } catch (error) {
      if (error.name === 'AbortError') throw new Error('Diet generation timed out');
      throw error;
    } finally {
      clearTimeout(timeoutId);
    }
  },
};
