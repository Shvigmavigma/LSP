<template>
  <div class="profile-page">
    <div class="header-actions">
      <ThemeToggle />
      <LanguageSwitcher />
      <HomeButton/>
    </div>

    <div class="profile-card">
      <div class="profile-header">
        <div class="avatar" @click="openAvatarModal" :class="{ clickable: user?.avatar }">
          <img
            v-if="user?.avatar && !avatarError"
            :src="avatarUrl"
            :alt="displayUserName(user)"
            @error="avatarError = true"
          />
          <span v-else>{{ displayUserInitial(user) }}</span>
        </div>
        <h2>{{ $t('profile.title') }}</h2>
      </div>

      <div v-if="user" class="profile-info">
        <div class="info-row">
          <span class="info-label">{{ $t('profile.fullname') }}</span>
          <span class="info-value">{{ user.fullname }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">{{ $t('profile.email') }}</span>
          <span class="info-value">{{ user.email }}</span>
        </div>

        <!-- Для учителя показываем роли, для ученика – класс -->
        <template v-if="user.is_teacher">
          <div class="info-row" v-if="user.teacher_info">
            <span class="info-label">{{ $t('profile.roles') }}</span>
            <span class="info-value">{{ formatTeacherRoles(user.teacher_info) }}</span>
          </div>
        </template>
        <template v-else>
          <div class="info-row">
            <span class="info-label">{{ $t('profile.class') }}</span>
            <span class="info-value">{{ user.class ?? $t('profile.notSpecified') }}</span>
          </div>
        </template>

        <div class="info-row">
          <span class="info-label">{{ $t('profile.speciality') }}</span>
          <span class="info-value">{{ user.speciality || $t('profile.notSpecified') }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">{{ $t('adminDirections.direction') }}</span>
          <span class="info-value">{{ directionLabel(user.direction_key) }}</span>
        </div>

        <div v-if="user.is_outdated && !user.is_teacher" class="outdated-account">
          <strong>{{ $t('profile.outdatedTitle') }}</strong>
          <p>{{ $t('profile.outdatedHint') }}</p>
          <button
            v-if="restorationStatus !== 'pending'"
            class="resend-button"
            :disabled="requestingRestoration"
            @click="requestRestoration"
          >
            {{ requestingRestoration ? $t('common.sending') : $t('profile.requestRestoration') }}
          </button>
          <span v-else>{{ $t('profile.restorationPending') }}</span>
          <div v-if="restorationError" class="oauth-error">{{ restorationError }}</div>
        </div>

        <div class="notification-setting">
          <span>
            <strong>{{ $t('profile.emailNotifications') }}</strong>
            <small>{{ $t('profile.emailNotificationsHint') }}</small>
          </span>
          <label class="notification-switch">
            <input
              type="checkbox"
              :checked="user.email_notifications_enabled !== false"
              :disabled="savingNotifications"
              @change="toggleEmailNotifications"
            />
            <span class="notification-slider"></span>
          </label>
        </div>
        <div v-if="notificationError" class="oauth-error">{{ notificationError }}</div>

        <div v-if="profileChangeRequest" class="outdated-account">
          <strong>{{ $t('profile.changePendingTitle') }}</strong>
          <p>{{ $t('profile.changePendingHint') }}</p>
          <button class="resend-button" :disabled="withdrawingRequest" @click="withdrawProfileChangeRequest">
            {{ withdrawingRequest ? $t('common.sending') : $t('profile.withdrawChangeRequest') }}
          </button>
          <div v-if="profileChangeError" class="oauth-error">{{ profileChangeError }}</div>
        </div>

        <!-- Google привязка в строчку -->
        <div class="info-row">
          <span class="info-label">{{ $t('profile.connectedAccounts') }}</span>
          <span class="info-value">
            <span class="oauth-status">
              {{ googleLinked ? $t('profile.googleLinked') : $t('profile.link') }}
            </span>
            <button
              v-if="!googleLinked"
              class="mini-link-button"
              @click="handleLinkGoogle"
              :disabled="linkingGoogle"
              :title="$t('profile.link')"
            >
              {{ linkingGoogle ? '...' : '+' }}
            </button>
            <button
              v-else
              class="mini-unlink-button"
              @click="handleUnlinkGoogle"
              :disabled="unlinkingGoogle"
              :title="$t('profile.unlink')"
            >
              {{ unlinkingGoogle ? '...' : '×' }}
            </button>
          </span>
        </div>

        <div v-if="oauthError" class="oauth-error">{{ oauthError }}</div>
        <div v-if="oauthSuccess" class="oauth-success">{{ oauthSuccess }}</div>

        <!-- Статус верификации email -->
        <div class="info-row verification-status">
          <span class="info-label">{{ $t('profile.emailStatus') }}</span>
          <span class="info-value" :class="user.is_verified ? 'verified' : 'unverified'">
            <span class="status-icon">{{ user.is_verified ? '✅' : '⏳' }}</span>
            {{ user.is_verified ? $t('profile.verified') : $t('profile.unverified') }}
          </span>
        </div>

        <!-- Если email не подтвержден, показываем подсказку -->
        <div v-if="!user.is_verified" class="verification-hint">
          <p>{{ $t('profile.verificationHint') }}</p>
          <button @click="resendVerification" class="resend-button" :disabled="resending">
            {{ resending ? $t('common.sending') : $t('profile.resendCode') }}
          </button>
        </div>
      </div>

      <div v-else class="loading">
        {{ $t('common.loading') }}
      </div>

      <button class="edit-button" @click="editProfile" :disabled="!!profileChangeRequest">
        {{ profileChangeRequest ? $t('profile.editBlocked') : $t('profile.editProfile') }}
      </button>
      <button class="logout-button" @click="logout">{{ $t('navigation.logout') }}</button>
    </div>

    <!-- Кнопка удаления аккаунта в правом нижнем углу экрана -->
    <AvatarModal
      :show="showAvatarModal"
      :src="avatarUrl"
      :alt="displayUserName(user)"
      @close="showAvatarModal = false"
    />
  </div>
</template>

<script setup lang="ts">
import { getUserDisplayName as displayUserName, getUserInitial as displayUserInitial } from '@/utils/userDisplay';
import { computed, ref, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useRouter, useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import HomeButton from '@/components/HomeButton.vue';
import ThemeToggle from '@/components/ThemeToggle.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';
import AvatarModal from '@/components/AvatarModal.vue';
import api from '@/utils/api'
import type { TeacherInfo } from '@/types';

const { t } = useI18n();
const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();
const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api';
const user = computed(() => authStore.user);
const avatarError = ref(false);
const showAvatarModal = ref(false);
const deleting = ref(false);
const resending = ref(false);
const savingNotifications = ref(false);
const notificationError = ref('');
const directions = ref<Array<{ key: string; label: string }>>([]);
const restorationStatus = ref('');
const requestingRestoration = ref(false);
const restorationError = ref('');
const profileChangeRequest = ref<any>(null);
const withdrawingRequest = ref(false);
const profileChangeError = ref('');

// OAuth состояния
const googleLinked = ref(false);
const linkingGoogle = ref(false);
const unlinkingGoogle = ref(false);
const oauthError = ref('');
const oauthSuccess = ref('');

const avatarUrl = computed(() => {
  if (!user.value?.avatar) return '';
  return `${baseUrl}/avatars/${user.value.avatar}`;
});

// Функция проверки статуса привязки Google
const checkGoogleLinkStatus = async () => {
  try {
    const response = await api.get('/auth/providers');
    const providers = response.data.providers;
    const googleProvider = providers.find((p: any) => p.provider === 'google');
    googleLinked.value = googleProvider ? googleProvider.is_linked : false;
    console.log('Google link status checked:', googleLinked.value);
  } catch (error) {
    console.error('Error checking Google link status:', error);
    // Fallback: проверяем через данные пользователя
    googleLinked.value = !!user.value?.google_id;
    console.log('Google link status from user data:', googleLinked.value);
  }
};

onMounted(async () => {
  const directionResponse = await api.get('/user-directions');
  directions.value = directionResponse.data.directions || [];
  // Проверяем аутентификацию
  if (!authStore.isAuthenticated) {
    const isValid = await authStore.checkAuth();
    if (!isValid) {
      router.push('/login');
      return;
    }
  }
  
  // Проверяем статус привязки Google
  await checkGoogleLinkStatus();
  await loadProfileChangeRequest();
  if (user.value?.is_outdated && !user.value.is_teacher) {
    try {
      const response = await api.get('/account-restoration-request');
      restorationStatus.value = response.data.request?.status || '';
    } catch (error) {
      console.error('Failed to load restoration request:', error);
    }
  }
  
  // Проверяем, был ли только что привязан Google
  if (route.query.google_linked === 'true') {
    oauthSuccess.value = t('profile.googleLinked');
    // Обновляем данные пользователя
    await authStore.checkAuth();
    // Перепроверяем статус привязки
    await checkGoogleLinkStatus();
    // Очищаем query параметры
    router.replace({ query: {} });
    
    // Убираем сообщение через 5 секунд
    setTimeout(() => {
      oauthSuccess.value = '';
    }, 5000);
  }
  
  console.log('Profile mounted - user:', user.value);
  console.log('Google linked status:', googleLinked.value);
});

const directionLabel = (key?: string | null) =>
  directions.value.find(direction => direction.key === key)?.label || key || t('profile.notSpecified');

const openAvatarModal = () => {
  if (user.value?.avatar && !avatarError.value) {
    showAvatarModal.value = true;
  }
};

const editProfile = () => {
  if (profileChangeRequest.value) return;
  router.push('/profile/edit');
};

const loadProfileChangeRequest = async () => {
  try {
    const response = await api.get('/profile-change-request');
    profileChangeRequest.value = response.data.request;
  } catch (error) {
    console.error('Failed to load profile change request:', error);
  }
};

const withdrawProfileChangeRequest = async () => {
  withdrawingRequest.value = true;
  profileChangeError.value = '';
  try {
    await api.delete('/profile-change-request');
    profileChangeRequest.value = null;
  } catch (error: any) {
    profileChangeError.value = error.response?.data?.detail || t('profile.withdrawChangeError');
  } finally {
    withdrawingRequest.value = false;
  }
};

const toggleEmailNotifications = async (event: Event) => {
  if (!user.value) return;
  const input = event.target as HTMLInputElement;
  const enabled = input.checked;
  savingNotifications.value = true;
  notificationError.value = '';
  try {
    const endpoint = user.value.is_teacher
      ? `/teachers/${user.value.id}`
      : `/students/${user.value.id}`;
    const response = await api.put(endpoint, { email_notifications_enabled: enabled });
    authStore.user = response.data;
    localStorage.setItem('user', JSON.stringify(response.data));
  } catch (error: any) {
    input.checked = !enabled;
    notificationError.value = error.response?.data?.detail || t('profile.notificationSaveError');
  } finally {
    savingNotifications.value = false;
  }
};

const requestRestoration = async () => {
  requestingRestoration.value = true;
  restorationError.value = '';
  try {
    const response = await api.post('/account-restoration-requests');
    restorationStatus.value = response.data.status;
  } catch (error: any) {
    restorationError.value = error.response?.data?.detail || t('profile.restorationError');
  } finally {
    requestingRestoration.value = false;
  }
};

const goToMain = () => {
  router.push('/main');
};

const logout = () => {
  if (confirm(t('profile.confirmLogout'))) {
    authStore.logout();
    router.push('/login');
  }
};

const confirmDeleteAccount = () => {
  if (!user.value) return;
  const confirmed = confirm(t('profile.confirmDeleteAccount'));
  if (confirmed) {
    deleteAccount();
  }
};

const deleteAccount = async () => {
  if (!user.value) return;
  deleting.value = true;
  try {
    await api.delete(`/users/me`);
    authStore.logout();
    router.push('/login');
    alert(t('profile.deleteSuccess'));
  } catch (error: any) {
    console.error('Ошибка при удалении аккаунта:', error);
    if (error.response?.status === 401) {
      alert(t('profile.sessionExpired'));
      authStore.logout();
      router.push('/login');
    } else {
      alert(error.response?.data?.detail || t('profile.deleteError'));
    }
  } finally {
    deleting.value = false;
  }
};

const resendVerification = async () => {
  if (!user.value?.email) return;
  resending.value = true;
  try {
    await api.post('/auth/resend-verification-code', {
      email: user.value.email
    });
    alert(t('profile.resendSuccess'));
  } catch (error: any) {
    console.error('Error resending code:', error);
    if (error.response) {
      switch (error.response.status) {
        case 400:
          if (error.response.data?.detail === 'Email already verified') {
            alert(t('profile.emailAlreadyVerified'));
            await authStore.checkAuth();
          } else {
            alert(`${t('profile.requestError')}: ${error.response.data?.detail || ''}`);
          }
          break;
        case 404:
          alert(t('profile.userNotFound'));
          break;
        default:
          alert(`${t('profile.serverError')}: ${error.response.data?.detail || ''}`);
      }
    } else if (error.code === 'ERR_NETWORK') {
      alert(t('profile.networkError'));
    } else {
      alert(t('profile.unknownError'));
    }
  } finally {
    resending.value = false;
  }
};

// Обработчики привязки/отвязки Google
const handleLinkGoogle = async () => {
  linkingGoogle.value = true;
  oauthError.value = '';
  
  try {
    // ✅ Измените на GET запрос
    const response = await api.get('/auth/link/google');
    // Перенаправляем на Google для авторизации
    window.location.href = response.data.url;
  } catch (error: any) {
    console.error('Error linking Google:', error);
    oauthError.value = error.response?.data?.detail || t('profile.linkError');
  } finally {
    linkingGoogle.value = false;
  }
};

// В Profile.vue обновите handleUnlinkGoogle:

const handleUnlinkGoogle = async () => {
  if (!confirm(t('profile.confirmUnlink'))) return;
  
  unlinkingGoogle.value = true;
  oauthError.value = '';
  oauthSuccess.value = '';
  
  try {
    const response = await api.post('/auth/unlink/google');
    
    // Обновляем локальное состояние
    googleLinked.value = false;
    
    // Обновляем данные пользователя в сторе
    if (authStore.user) {
      authStore.user.google_id = null;
      authStore.user.oauth_providers = authStore.user.oauth_providers?.filter(
        (p: string) => p !== 'google'
      ) || [];
    }
    
    // Показываем сообщение об успехе
    oauthSuccess.value = t('profile.googleUnlinked');
    
    // Обновляем данные с сервера
    await authStore.checkAuth();
    
    // Убираем сообщение через 5 секунд
    setTimeout(() => {
      oauthSuccess.value = '';
    }, 5000);
    
    console.log('Google unlinked successfully');
  } catch (error: any) {
    console.error('Error unlinking Google:', error);
    
    if (error.response?.status === 400) {
      oauthError.value = t('profile.noGoogleAccount');
    } else if (error.response?.status === 401) {
      oauthError.value = t('profile.sessionExpired');
      // Перенаправляем на логин если сессия истекла
      setTimeout(() => {
        authStore.logout();
        router.push('/login');
      }, 2000);
    } else {
      oauthError.value = error.response?.data?.detail || t('profile.unlinkError');
    }
  } finally {
    unlinkingGoogle.value = false;
  }
};

// Вспомогательная функция для форматирования ролей учителя (с использованием переводов)
function formatTeacherRoles(teacherInfo: TeacherInfo): string {
  const roleNames: string[] = [];
  if (teacherInfo.roles.includes('supervisor')) roleNames.push(t('roles.supervisor'));
  if (teacherInfo.roles.includes('expert')) roleNames.push(t('roles.expert'));
  if (teacherInfo.roles.includes('customer')) roleNames.push(t('roles.customer'));
  if (teacherInfo.curator) roleNames.push(t('roles.curator'));
  return roleNames.join(', ') || t('profile.noRoles');
}
</script>

<style scoped>
.profile-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: var(--bg-page);
  margin: -20px;
  padding: 20px;
  position: relative;
  transition: background 0.3s;
}

.header-actions {
  position: absolute;
  top: 30px;
  right: 30px;
  display: flex;
  gap: 10px;
  z-index: 10;
}

.profile-card {
  background: var(--bg-card);
  border-radius: 32px;
  box-shadow: var(--shadow-strong);
  padding: 40px;
  width: 100%;
  max-width: 500px;
  transition: background 0.3s;
  overflow: hidden;
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
}

.avatar {
  width: 80px;
  height: 80px;
  background: var(--bg-page);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--heading-color);
  overflow: hidden;
  font-size: 48px;
  transition: opacity 0.2s;
  border: 3px solid var(--accent-color);
}

.avatar.clickable {
  cursor: pointer;
}

.avatar.clickable:hover {
  opacity: 0.8;
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.avatar span {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 36px;
}

.profile-header h2 {
  font-size: 2rem;
  color: var(--heading-color);
  margin: 0;
  font-weight: 500;
  overflow-wrap: break-word;
  word-wrap: break-word;
  hyphens: auto;
  max-width: calc(100% - 96px);
}

.profile-info {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 32px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-color);
  overflow-wrap: break-word;
  word-wrap: break-word;
  gap: 10px;
}

.notification-setting {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 14px 0;
  border-bottom: 1px solid var(--border-color);
}

.outdated-account {
  padding: 14px 16px;
  border: 1px solid var(--danger-color);
  border-radius: 8px;
  background: var(--danger-bg);
  color: var(--text-primary);
}

.outdated-account p {
  margin: 6px 0 12px;
  color: var(--text-secondary);
}

.notification-setting > span {
  display: grid;
  gap: 4px;
}

.notification-setting strong {
  color: var(--text-primary);
}

.notification-setting small {
  color: var(--text-secondary);
  line-height: 1.4;
}

.notification-switch {
  position: relative;
  width: 46px;
  height: 26px;
  flex-shrink: 0;
}

.notification-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.notification-slider {
  position: absolute;
  inset: 0;
  border-radius: 13px;
  background: var(--border-color);
  cursor: pointer;
  transition: background 0.2s;
}

.notification-slider::before {
  content: '';
  position: absolute;
  width: 20px;
  height: 20px;
  left: 3px;
  top: 3px;
  border-radius: 50%;
  background: var(--bg-card);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
  transition: transform 0.2s;
}

.notification-switch input:checked + .notification-slider {
  background: var(--accent-color);
}

.notification-switch input:checked + .notification-slider::before {
  transform: translateX(20px);
}

.notification-switch input:disabled + .notification-slider {
  cursor: wait;
  opacity: 0.6;
}

.info-label {
  font-weight: 600;
  color: var(--text-secondary);
  font-size: 1rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  min-width: 120px;
  flex-shrink: 0;
}

.info-value {
  color: var(--text-primary);
  font-size: 1.1rem;
  text-align: right;
  overflow-wrap: break-word;
  word-wrap: break-word;
  hyphens: auto;
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  font-weight: normal;
}

.oauth-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.95rem;
  color: var(--text-secondary);
}

.provider-icon {
  font-size: 1.1rem;
}

.mini-link-button,
.mini-unlink-button {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  font-size: 1.2rem;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  padding: 0;
  flex-shrink: 0;
}

.mini-link-button {
  background: var(--accent-color);
  color: var(--button-text);
}

.mini-link-button:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: scale(1.1);
}

.mini-unlink-button {
  background: var(--danger-bg);
  color: var(--danger-color);
}

.mini-unlink-button:hover:not(:disabled) {
  background: var(--danger-hover);
  color: white;
  transform: scale(1.1);
}

.mini-link-button:disabled,
.mini-unlink-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.verification-status {
  background: rgba(128, 128, 128, 0.05);
  border-radius: 8px;
  padding: 8px 12px;
  margin-top: 5px;
}

.status-icon {
  font-size: 1.2rem;
  margin-right: 4px;
}

.info-value.verified {
  color: #4caf50;
  font-weight: normal;
}

.info-value.unverified {
  color: #ff9800;
  font-weight: normal;
}

.verification-hint {
  background: rgba(255, 152, 0, 0.1);
  border-left: 4px solid #ff9800;
  padding: 12px 16px;
  border-radius: 8px;
  margin-top: 10px;
  margin-bottom: 10px;
}

.verification-hint p {
  color: var(--text-primary);
  margin-bottom: 10px;
  font-size: 0.95rem;
}

.resend-button {
  background: var(--bg-card);
  color: var(--accent-color);
  border: 1px solid var(--accent-color);
  border-radius: 20px;
  padding: 8px 16px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.resend-button:hover:not(:disabled) {
  background: var(--accent-color);
  color: var(--button-text);
}

.resend-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading {
  text-align: center;
  color: var(--text-secondary);
  padding: 20px;
  font-style: italic;
}

.edit-button {
  width: 100%;
  padding: 14px;
  background-color: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 50px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
  margin-top: 8px;
}

.edit-button:hover {
  background-color: var(--accent-hover);
}

.logout-button {
  width: 100%;
  padding: 14px;
  background-color: var(--danger-bg);
  color: var(--danger-color);
  border: none;
  border-radius: 50px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
  margin-top: 12px;
}

.logout-button:hover {
  background-color: var(--danger-hover);
}

.delete-account-button {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 100;
  padding: 14px 28px;
  background-color: #d32f2f;
  color: white;
  border: none;
  border-radius: 50px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
  box-shadow: var(--shadow-strong);
}

.delete-account-button:hover:not(:disabled) {
  background-color: #b71c1c;
  box-shadow: var(--shadow-strong);
}

.delete-account-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.oauth-error {
  color: var(--danger-color);
  font-size: 0.85rem;
  text-align: center;
  margin-top: -10px;
}

.oauth-success {
  color: #4caf50;
  font-size: 0.85rem;
  text-align: center;
  margin-top: -10px;
  font-weight: 500;
}
</style>
