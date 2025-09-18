import apiClient from './index';

interface LoginCredentials {
  username: string;
  password: string;
}

interface User {
  id: string;
  name: string;
  role: string;
}

interface LoginResponse {
  token: string;
  user: User;
}

export const login = async (credentials: LoginCredentials): Promise<LoginResponse> => {
  const response = await apiClient.post('/auth/login', credentials);
  return response.data;
};

export const logout = async (): Promise<void> => {
  await apiClient.post('/auth/logout');
};
