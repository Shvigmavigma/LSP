<template>
  <div class="login-page">
    <Transition name="fade">
      <div v-if="notification.show" class="notification" :class="notification.type">
        <span class="notification-message">{{ notification.message }}</span>
        <button class="notification-close" @click="closeNotification">✕</button>
      </div>
    </Transition>

    <div class="theme-toggle-left">
      <ThemeToggle />
    </div>
    <div class="language-switcher-right">
      <LanguageSwitcher />
    </div>

    <div class="login-card">
      <h2>{{ $t('login.title') }}</h2>
      
      <!-- Форма логина (теперь первая) -->
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="email">{{ $t('login.email') }}</label>
          <input
            id="email"
            v-model="email"
            type="email"
            :placeholder="$t('login.emailPlaceholder')"
            required
            :class="{ 'error-input': hasError }"
            @input="clearError"
          />
        </div>

        <div class="form-group">
          <label for="password">{{ $t('login.password') }}</label>
          <input
            id="password"
            v-model="password"
            type="password"
            :placeholder="$t('login.passwordPlaceholder')"
            required
            :class="{ 'error-input': hasError }"
            @input="clearError"
          />
        </div>

        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>

        <button type="submit" class="login-button" :disabled="loading || oauthLoading">
          {{ loading ? $t('common.loading') : $t('login.loginButton') }}
        </button>
      </form>

      <div class="divider">
        <span>{{ $t('login.or') }}</span>
      </div>

      <!-- Google OAuth кнопка (теперь вторая) -->
      <div class="oauth-section">
        <button 
          type="button" 
          class="oauth-btn google-btn" 
          @click="loginWithGoogle"
          :disabled="oauthLoading"
        >
          <svg class="oauth-icon" viewBox="0 0 24 24" width="20" height="20">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          <span>{{ $t('login.loginWithGoogle') }}</span>
        </button>
      </div>

      <p class="register-link">
        {{ $t('login.noAccount') }} <router-link to="/register">{{ $t('login.registerLink') }}</router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import ThemeToggle from '@/components/ThemeToggle.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';

import api from '@/utils/api'

const { t } = useI18n();
const router = useRouter();
const route = useRoute();
const email = ref('');
const password = ref('');
const loading = ref(false);
const oauthLoading = ref(false);
const errorMessage = ref('');
const hasError = ref(false);

const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

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

// 🔥 Обработка OAuth callback при загрузке
onMounted(async () => {
  const oauthToken = route.query.oauth_token as string;
  const oauthError = route.query.oauth_error as string;
  
  // 🔥 Обработка ошибки OAuth
  if (oauthError) {
    showNotification(decodeURIComponent(oauthError), 'error', 8000);
    router.replace({ path: '/login' });
    return;
  }
  
  if (oauthToken) {
    try {
      localStorage.setItem('access_token', oauthToken);
      api.defaults.headers.common['Authorization'] = `Bearer ${oauthToken}`;
      
      const userResponse = await api.get('/users/me');
      const authStore = (await import('@/stores/auth')).useAuthStore();
      authStore.user = userResponse.data;
      authStore.isAuthenticated = true;
      
      showNotification(t('login.successMessage'), 'success');
      
      const returnUrl = localStorage.getItem('oauth_return_url') || '/main';
      localStorage.removeItem('oauth_return_url');
      
      setTimeout(() => router.push(returnUrl), 1000);
    } catch (error) {
      console.error('OAuth login error:', error);
      showNotification(t('login.oauthError'), 'error');
      router.replace({ path: '/login' });
    }
    return;
  }
  
  // Очищаем старые токены
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  delete api.defaults.headers.common['Authorization'];
});

// Google OAuth логин
const loginWithGoogle = async () => {
  oauthLoading.value = true;
  try {
    const response = await api.get(`${baseUrl}/auth/google/login`);
    const { url } = response.data;
    
    localStorage.setItem('oauth_return_url', '/main');
    window.location.href = url;
  } catch (error: any) {
    console.error('Google login error:', error);
    showNotification(t('login.oauthError'), 'error');
    oauthLoading.value = false;
  }
};

const handleLogin = async () => {
  if (!email.value || !password.value) {
    errorMessage.value = t('login.fillAllFields');
    showNotification(t('login.fillAllFields'), 'info');
    return;
  }

  const normalizedEmail = email.value.trim().toLowerCase();
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailPattern.test(normalizedEmail)) {
    errorMessage.value = t('login.invalidEmail');
    hasError.value = true;
    showNotification(t('login.invalidEmail'), 'info');
    return;
  }

  loading.value = true;
  errorMessage.value = '';
  hasError.value = false;

  try {
    const response = await api.post('/auth/login', {
      email: normalizedEmail,
      password: password.value
    });

    const { access_token, refresh_token } = response.data;

    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);

    api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

    const userResponse = await api.get('/users/me');
    const authStore = (await import('@/stores/auth')).useAuthStore();
    authStore.user = userResponse.data;
    authStore.isAuthenticated = true;

    showNotification(t('login.successMessage'), 'success');
    setTimeout(() => router.push('/main'), 1000);

  } catch (error: any) {
    console.error('Login error:', error);
    hasError.value = true;

    let userMessage = t('login.genericError');
    if (error.response) {
      userMessage = error.response.data?.detail || `${t('login.errorPrefix')} ${error.response.status}`;
    } else if (error.code === 'ERR_NETWORK') {
      userMessage = t('login.networkError');
    } else {
      userMessage = error.message || t('login.unknownError');
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

.theme-toggle-left {
  position: absolute;
  top: 30px;
  left: 30px;
  z-index: 10;
}

.language-switcher-right {
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
  transition: background 0.3s;
}

h2 {
  text-align: center;
  color: var(--heading-color);
  margin-bottom: 28px;
  font-weight: 500;
}

/* OAuth секция */
.oauth-section {
  margin-bottom: 20px;
}

.oauth-btn {
  width: 100%;
  padding: 12px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  background: white;
  color: #333;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.oauth-btn:hover:not(:disabled) {
  border-color: #4285F4;
  box-shadow: 0 2px 8px rgba(66, 133, 244, 0.2);
}

.oauth-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.google-btn {
  border-color: #4285F4;
  background: white;
}

.google-btn:hover:not(:disabled) {
  background: #f8fbff;
}

.oauth-icon {
  flex-shrink: 0;
}

.divider {
  display: flex;
  align-items: center;
  text-align: center;
  margin: 20px 0;
  color: var(--text-secondary);
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px solid var(--border-color);
}

.divider span {
  padding: 0 10px;
  font-size: 0.9rem;
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
  transition: background-color 0.2s;
  margin-top: 8px;
}

.login-button:hover:not(:disabled) {
  background-color: var(--accent-hover);
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
