import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const uploadDocument = async (file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post('/upload/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percent);
      }
    },
  });

  return response.data;
};

export const chat = async (question, topK = 5) => {
  const response = await apiClient.post('/chat/', {
    question,
    top_k: topK,
  });
  return response.data;
};

export const getGraphData = async () => {
  const response = await apiClient.get('/graph/');
  return response.data;
};

export const searchGraph = async (keyword) => {
  const response = await apiClient.get('/graph/search', {
    params: { keyword },
  });
  return response.data;
};

export const healthCheck = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};

export default apiClient;
