<!-- src/views/Login.vue -->
<template>
  <div class="login-page">
    <!-- Всплывающее уведомление об ошибке/успехе -->
    <Transition name="fade">
      <div v-if="notification.show" class="notification" :class="notification.type">
        <span class="notification-message">{{ notification.message }}</span>
        <button class="notification-close" @click="closeNotification">✕</button>
      </div>
    </Transition>

    <div class="theme-toggle-container">
      <ThemeToggle />
    </div>

    <div class="login-card">
      <h2>Вход в систему</h2>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="nickname">Никнейм или Email</label>
          <input
            id="nickname"
            v-model="nickname"
            type="text"
            placeholder="Введите никнейм или почту"
            required
            :class="{ 'error-input': hasError }"
            @input="clearError"
          />
        </div>

        <div class="form-group">
          <label for="password">Пароль</label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="Введите пароль"
            required
            :class="{ 'error-input': hasError }"
            @input="clearError"
          />
        </div>

        <!-- Текстовое сообщение об ошибке (можно оставить для совместимости) -->
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>

        <button type="submit" class="login-button" :disabled="loading">
          {{ loading ? 'Вход...' : 'Войти' }}
        </button>
      </form>

      <p class="register-link">
        Нет аккаунта? <router-link to="/register">Зарегистрироваться</router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';
import ThemeToggle from '@/components/ThemeToggle.vue';
import axios from 'axios';

const authStore = useAuthStore();
const router = useRouter();
const nickname = ref('');
const password = ref('');
const loading = ref(false);
const errorMessage = ref('');
const hasError = ref(false);

// Уведомления
const notification = ref({
  show: false,
  message: '',
  type: 'error' as 'error' | 'info' | 'success'
});

let notificationTimeout: number | null = null;

function showNotification(message: string, type: 'error' | 'info' | 'success' = 'error', duration = 5000) {
  if (notificationTimeout) {
    clearTimeout(notificationTimeout);
    notificationTimeout = null;
  }
  notification.value = { show: true, message, type };
  hasError.value = type === 'error';
  notificationTimeout = window.setTimeout(() => {
    notification.value.show = false;
    notificationTimeout = null;
  }, duration);
}

function closeNotification() {
  notification.value.show = false;
  if (notificationTimeout) {
    clearTimeout(notificationTimeout);
    notificationTimeout = null;
  }
}

function clearError() {
  hasError.value = false;
  errorMessage.value = '';
}

// При монтировании страницы логина очищаем старые токены (на всякий случай)
onMounted(() => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  delete axios.defaults.headers.common['Authorization'];
});

const handleLogin = async () => {
  if (!nickname.value || !password.value) {
    errorMessage.value = 'Заполните все поля';
    showNotification('Заполните все поля', 'info');
    return;
  }

  loading.value = true;
  errorMessage.value = '';
  hasError.value = false;

  try {
    const response = await axios.post('/auth/login', {
      nickname: nickname.value,
      password: password.value
    });

    const { access_token, refresh_token } = response.data;

    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);

    axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

    const userResponse = await axios.get('/users/me');
    authStore.user = userResponse.data;

    showNotification('Вход выполнен успешно!', 'success');
    setTimeout(() => router.push('/main'), 1000);

  } catch (error: any) {
    console.error('Login error:', error);
    hasError.value = true;

    let userMessage = 'Ошибка при входе';
    if (error.response) {
      // Используем сообщение от сервера (если оно есть)
      userMessage = error.response.data?.detail || `Ошибка ${error.response.status}`;
    } else if (error.code === 'ERR_NETWORK') {
      userMessage = 'Ошибка сети. Проверьте подключение к серверу.';
    } else {
      userMessage = error.message || 'Произошла неизвестная ошибка';
    }

    errorMessage.value = userMessage;
    showNotification(userMessage, 'error');
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-page {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: var(--bg-page);
  margin: -20px;
  padding: 20px;
  position: relative;
  transition: background 0.3s;
}

.theme-toggle-container {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 10;
}

.login-card {
  background: var(--bg-card);
  border-radius: 16px;
  box-shadow: var(--shadow-strong);
  padding: 40px 32px;
  width: 100%;
  max-width: 400px;
  transition: transform 0.2s ease, background 0.3s;
}

.login-card:hover {
  transform: translateY(-4px);
}

h2 {
  text-align: center;
  color: var(--heading-color);
  margin-bottom: 28px;
  font-weight: 500;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 6px;
  color: var(--text-secondary);
  font-size: 0.9rem;
  font-weight: 500;
}

input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s, box-shadow 0.2s;
  outline: none;
  box-sizing: border-box;
  background: var(--input-bg);
  color: var(--text-primary);
}

input:focus {
  border-color: var(--accent-color);
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.2);
}

.dark-theme input:focus {
  box-shadow: 0 0 0 3px rgba(1, 69, 172, 0.2);
}

input.error-input {
  border-color: var(--danger-color);
  background-color: rgba(244, 67, 54, 0.05);
}

.error-message {
  background: var(--error-bg);
  color: var(--danger-color);
  padding: 10px;
  border-radius: 8px;
  margin-bottom: 20px;
  text-align: center;
  border: 1px solid var(--danger-color);
  font-size: 0.9rem;
}

.login-button {
  width: 100%;
  padding: 14px;
  background-color: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.1s;
  margin-top: 8px;
}

.login-button:hover:not(:disabled) {
  background-color: var(--accent-hover);
}

.login-button:active:not(:disabled) {
  transform: scale(0.98);
}

.login-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.register-link {
  text-align: center;
  margin-top: 24px;
  color: var(--text-secondary);
  font-size: 0.95rem;
}

.register-link a {
  color: var(--link-color);
  text-decoration: none;
  font-weight: 500;
}

.register-link a:hover {
  color: var(--link-hover);
  text-decoration: underline;
}

/* Уведомления */
.notification {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 16px 24px;
  border-radius: 8px;
  color: white;
  font-weight: 500;
  box-shadow: var(--shadow-strong);
  z-index: 2000;
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 300px;
  max-width: 400px;
  backdrop-filter: blur(4px);
}

.notification.error {
  background-color: rgba(244, 67, 54, 0.9);
  border-left: 4px solid #d32f2f;
}

.notification.success {
  background-color: rgba(76, 175, 80, 0.9);
  border-left: 4px solid #388e3c;
}

.notification.info {
  background-color: rgba(33, 150, 243, 0.9);
  border-left: 4px solid #1976d2;
}

.notification-message {
  flex: 1;
}

.notification-close {
  background: none;
  border: none;
  color: white;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 4px;
  line-height: 1;
  opacity: 0.8;
  transition: opacity 0.2s;
}

.notification-close:hover {
  opacity: 1;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>