import axios from 'axios';
import toast from 'react-hot-toast';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - attach token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('docsetu_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.message || 'Something went wrong';

    if (error.response?.status === 401) {
      localStorage.removeItem('docsetu_token');
      localStorage.removeItem('docsetu_user');
      window.location.href = '/login';
      toast.error('Session expired. Please login again.');
    } else if (error.response?.status === 403) {
      toast.error('You do not have permission to perform this action.');
    } else if (error.response?.status >= 500) {
      toast.error('Server error. Please try again later.');
    }

    return Promise.reject(error);
  }
);

// Auth APIs
export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
  register: (data) => api.post('/auth/register', data),
  getProfile: () => api.get('/auth/profile'),
  updateProfile: (data) => api.put('/auth/profile', data),
};

// Document APIs
export const documentAPI = {
  getAll: (params) => api.get('/documents', { params }),
  getById: (id) => api.get(`/documents/${id}`),
  upload: (formData, onProgress) =>
    api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress?.(percent);
      },
    }),
  delete: (id) => api.delete(`/documents/${id}`),
  reanalyze: (id) => api.post(`/documents/${id}/reanalyze`),
  getReport: (id) => api.get(`/documents/${id}/report`, { responseType: 'blob' }),
  askQuestion: (id, question) => api.post(`/documents/${id}/ask`, { question }),
};

// Compliance APIs
export const complianceAPI = {
  getOverview: () => api.get('/compliance/overview'),
  getRules: () => api.get('/compliance/rules'),
  getDocumentCompliance: (docId) => api.get(`/compliance/documents/${docId}`),
  getRecommendations: () => api.get('/compliance/recommendations'),
};

// Analytics APIs
export const analyticsAPI = {
  getDashboard: () => api.get('/analytics/dashboard'),
  getDocumentStats: (params) => api.get('/analytics/documents', { params }),
  getComplianceTrend: (params) => api.get('/analytics/compliance-trend', { params }),
  getTopIssues: () => api.get('/analytics/top-issues'),
};

export default api;
