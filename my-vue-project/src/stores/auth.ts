// src/stores/auth.ts
import { defineStore } from 'pinia'
import axios from 'axios'
import type { User } from '@/types'

interface AuthState {
  user: User | null
  isAuthenticated: boolean
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    isAuthenticated: false
  }),
  
  getters: {
    userId: (state) => state.user?.id || null
  },
  
  actions: {
    async login(nickname: string, password: string) {
      try {
        console.log('Attempting login for:', nickname);
        
        const response = await axios.post('/auth/login', {
          nickname,
          password
        });
        
        console.log('Login response:', response.data);
        
        const { access_token, refresh_token } = response.data;
        
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);
        
        axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
        
        // Получаем данные пользователя
        const userResponse = await axios.get('/users/me');
        console.log('User data response:', userResponse.data);
        
        this.user = userResponse.data;
        this.isAuthenticated = true;
        
        return true;
      } catch (error: any) {
        console.error('Login error details:', {
          status: error.response?.status,
          statusText: error.response?.statusText,
          data: error.response?.data,
          message: error.message
        });
        
        // Очищаем токены при ошибке входа
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        delete axios.defaults.headers.common['Authorization'];
        
        return false;
      }
    },
    
    async register(userData: any) {
      try {
        const response = await axios.post('/users/', userData);
        return response.data;
      } catch (error) {
        console.error('Register error:', error);
        throw error;
      }
    },
    
    logout() {
      this.user = null;
      this.isAuthenticated = false;
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      delete axios.defaults.headers.common['Authorization'];
    },
    
    async checkAuth() {
      const token = localStorage.getItem('access_token');
      if (!token) {
        this.isAuthenticated = false;
        return false;
      }
      
      try {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        const response = await axios.get('/users/me');
        this.user = response.data;
        this.isAuthenticated = true;
        console.log('Auth check successful:', this.user);
        return true;
      } catch (error: any) {
        console.error('Check auth error:', {
          status: error.response?.status,
          data: error.response?.data,
          message: error.message
        });
        this.logout();
        return false;
      }
    }
  }
})