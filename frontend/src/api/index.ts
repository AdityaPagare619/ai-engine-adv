import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000/api',
  timeout: 10000,
});

// Add interceptors for auth tokens or error handling here if needed

export default apiClient;
