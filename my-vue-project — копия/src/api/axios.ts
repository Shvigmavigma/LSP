// src/api/axios.ts
import axios from 'axios'

// Настройка базового URL
axios.defaults.baseURL = 'http://localhost:8000'

let isRefreshing = false
let failedQueue: { resolve: (value: any) => void; reject: (reason?: any) => void }[] = []

function processQueue(error: any, token: string | null = null) {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

// Перехватчик для обработки 401 ошибок и автоматического обновления токена
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Логирование для отладки (можно убрать позже)
    console.log('Axios interceptor error:', {
      url: originalRequest?.url,
      status: error.response?.status,
      retry: originalRequest?._retry
    })

    // Если нет ответа или статус не 401 – просто пробрасываем ошибку
    if (!error.response || error.response.status !== 40) {
      return Promise.reject(error)
    }

    // Никогда не пытаемся обновить токен для запросов на /auth/login и /auth/refresh
    if (
      originalRequest.url.includes('/auth/login') ||
      originalRequest.url.includes('/auth/refresh')
    ) {
      return Promise.reject(error)
    }

    // Если уже пробовали обновить – больше не пробуем
    if (originalRequest._retry) {
      return Promise.reject(error)
    }

    // Проверяем наличие refresh токена
    const refreshToken = localStorage.getItem('refresh_token')
    if (!refreshToken) {
      // Если нет refresh токена, перенаправляем на страницу входа
      window.location.href = '/login'
      return Promise.reject(error)
    }

    // Если уже идёт обновление, ставим запрос в очередь
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject })
      })
        .then(token => {
          originalRequest.headers['Authorization'] = `Bearer ${token}`
          return axios(originalRequest)
        })
        .catch(err => Promise.reject(err))
    }

    originalRequest._retry = true
    isRefreshing = true

    try {
      const response = await axios.post('/auth/refresh', {
        refresh_token: refreshToken
      })

      const { access_token, refresh_token: newRefreshToken } = response.data

      // Сохраняем новые токены
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('refresh_token', newRefreshToken)

      // Обновляем заголовок для всех последующих запросов
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`

      // Обрабатываем очередь успешно
      processQueue(null, access_token)

      // Повторяем исходный запрос
      originalRequest.headers['Authorization'] = `Bearer ${access_token}`
      return axios(originalRequest)
    } catch (refreshError) {
      // Обрабатываем очередь с ошибкой
      processQueue(refreshError, null)

      // Очищаем токены
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      delete axios.defaults.headers.common['Authorization']

      // Перенаправляем на страницу входа
      window.location.href = '/login'
      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  }
)

export default axios