import { apiService } from './api';

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
};
