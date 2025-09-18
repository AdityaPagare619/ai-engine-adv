import axios from 'axios';

interface LoginCredentials {
  username: string;
  password: string;
}

interface LoginResponse {
  token: string;
  user: {
    id: string;
    name: string;
    role: string;
  };
}

export const loginAPI = async (credentials: LoginCredentials): Promise<LoginResponse> => {
  const response = await axios.post('/api/auth/login', credentials);
  return response.data;
};

export const logoutAPI = async (): Promise<void> => {
  await axios.post('/api/auth/logout');
};
