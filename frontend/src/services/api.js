import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8086';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add any auth headers here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// API functions
export const apiService = {
  // Health check
  healthCheck: async () => {
    const response = await api.get('/health');
    return response.data;
  },

  // Upload PDF
  uploadPDF: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/upload-pdf', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Chat
  chat: async (message, conversationHistory = []) => {
    const response = await api.post('/chat', {
      message,
      conversation_history: conversationHistory,
    });
    return response.data;
  },

  // Get model info
  getModelInfo: async () => {
    const response = await api.get('/model-info');
    return response.data;
  },

  // Get PDF info
  getPDFInfo: async () => {
    const response = await api.get('/pdf-info');
    return response.data;
  },
};

export default apiService; 