import axios from 'axios';

// Create axios instance
const client = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
client.interceptors.response.use(
  (response) => response,
  (error) => {
    // global error handling
    if (error.response?.status === 401) {
      // handle unauthorized, e.g. redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default client;
