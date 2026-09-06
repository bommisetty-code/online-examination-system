import apiClient from './apiClient';

export const authService = {
  login: async (username, password) => {
    const response = await apiClient.post('/auth/login', { username, password });
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  },

  getProfile: async () => {
    const response = await apiClient.get('/auth/profile');
    return response.data;
  },

  isAuthenticated: () => {
    return !!localStorage.getItem('access_token');
  },

  getCurrentUser: () => {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },

  getCurrentRole: () => {
    const user = authService.getCurrentUser();
    return user?.role || null;
  },
};

export default authService;
