import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import axios from 'axios'
import i18n from './i18n'
import 'flag-icons/css/flag-icons.min.css'

axios.defaults.baseURL = import.meta.env.VITE_API_BASE_URL || '/api';

// ✅ ВАЖНО: Добавляем request interceptor для КАЖДОГО запроса
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor для обновления токена
axios.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 
        && !originalRequest._retry 
        && !originalRequest.url?.includes('/auth/refresh')) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
          throw new Error('No refresh token');
        }
        
        // Отправляем refresh токен в заголовке
        const response = await axios.post('/auth/refresh', {}, {
          headers: {
            'Authorization': `Bearer ${refreshToken}`
          }
        });
        
        const { access_token, refresh_token: newRefreshToken } = response.data;
        
        localStorage.setItem('access_token', access_token);
        if (newRefreshToken) {
          localStorage.setItem('refresh_token', newRefreshToken);
        }
        
        // Обновляем токен в оригинальном запросе
        originalRequest.headers['Authorization'] = `Bearer ${access_token}`;
        
        return axios(originalRequest);
      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError);
        
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        
        router.push('/login');
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(i18n)
app.mount('#app')