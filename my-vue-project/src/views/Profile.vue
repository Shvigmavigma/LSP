<template>
  <div class="profile-page">
    <div class="header-actions">
      <ThemeToggle />
      <button class="home-button" @click="goToMain" title="Главное меню">🏠</button>
    </div>

    <div class="profile-card">
      <div class="profile-header">
        <div class="avatar" @click="openAvatarModal" :class="{ clickable: user?.avatar }">
          <img
            v-if="user?.avatar && !avatarError"
            :src="avatarUrl"
            :alt="user.nickname"
            @error="avatarError = true"
          />
          <span v-else>{{ user?.nickname?.charAt(0).toUpperCase() || '?' }}</span>
        </div>
        <h2>Личный кабинет</h2>
      </div>

      <div v-if="user" class="profile-info">
        <div class="info-row">
          <span class="info-label">Никнейм</span>
          <span class="info-value">{{ user.nickname }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Полное имя</span>
          <span class="info-value">{{ user.fullname }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Email</span>
          <span class="info-value">{{ user.email }}</span>
        </div>

        <!-- Для учителя показываем роли, для ученика – класс -->
        <template v-if="user.is_teacher">
          <div class="info-row" v-if="user.teacher_info">
            <span class="info-label">Роли</span>
            <span class="info-value">{{ formatTeacherRoles(user.teacher_info) }}</span>
          </div>
        </template>
        <template v-else>
          <div class="info-row">
            <span class="info-label">Класс</span>
            <span class="info-value">{{ user.class }}</span>
          </div>
        </template>

        <div class="info-row">
          <span class="info-label">Специальность</span>
          <span class="info-value">{{ user.speciality || 'не указана' }}</span>
        </div>

        <!-- Статус верификации email -->
        <div class="info-row verification-status">
          <span class="info-label">Статус email</span>
          <span class="info-value" :class="user.is_verified ? 'verified' : 'unverified'">
            <span class="status-icon">{{ user.is_verified ? '✅' : '⏳' }}</span>
            {{ user.is_verified ? 'Подтвержден' : 'Ожидает подтверждения' }}
          </span>
        </div>

        <!-- Если email не подтвержден, показываем подсказку -->
        <div v-if="!user.is_verified" class="verification-hint">
          <p>✉️ Для полного доступа к функциям подтвердите email</p>
          <button @click="resendVerification" class="resend-button" :disabled="resending">
            {{ resending ? 'Отправка...' : 'Отправить код повторно' }}
          </button>
        </div>
      </div>

      <div v-else class="loading">
        Загрузка данных...
      </div>

      <button class="edit-button" @click="editProfile">Редактировать профиль</button>
      <button class="logout-button" @click="logout">Выйти</button>
    </div>

    <!-- Кнопка удаления аккаунта в правом нижнем углу экрана -->
    <button class="delete-account-button" @click="confirmDeleteAccount" :disabled="deleting">
      {{ deleting ? 'Удаление...' : '🗑 Удалить аккаунт' }}
    </button>

    <AvatarModal
      :show="showAvatarModal"
      :src="avatarUrl"
      :alt="user?.nickname"
      @close="showAvatarModal = false"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';
import ThemeToggle from '@/components/ThemeToggle.vue';
import AvatarModal from '@/components/AvatarModal.vue';
import axios from 'axios';
import type { TeacherInfo } from '@/types';

const authStore = useAuthStore();
const router = useRouter();
const user = computed(() => authStore.user);
const avatarError = ref(false);
const showAvatarModal = ref(false);
const deleting = ref(false);
const resending = ref(false);

const avatarUrl = computed(() => {
  if (!user.value?.avatar) return '';
  return `http://localhost:8000/avatars/${user.value.avatar}`;
});

onMounted(async () => {
  if (!authStore.isAuthenticated) {
    const isValid = await authStore.checkAuth();
    if (!isValid) {
      router.push('/login');
    }
  }
  console.log('Profile mounted - user:', user.value);
});

const openAvatarModal = () => {
  if (user.value?.avatar && !avatarError.value) {
    showAvatarModal.value = true;
  }
};

const editProfile = () => {
  router.push('/profile/edit');
};

const goToMain = () => {
  router.push('/main');
};

const logout = () => {
  if (confirm('Вы уверены, что хотите выйти?')) {
    authStore.logout();
    router.push('/login');
  }
};

const confirmDeleteAccount = () => {
  if (!user.value) return;
  const confirmed = confirm(
    'Вы уверены, что хотите удалить свой аккаунт? Это действие необратимо. Все ваши проекты останутся, но вы будете удалены из списка авторов.'
  );
  if (confirmed) {
    deleteAccount();
  }
};

const deleteAccount = async () => {
  if (!user.value) return;
  deleting.value = true;
  try {
    await axios.delete(`/users/${user.value.id}`);
    authStore.logout();
    router.push('/login');
    alert('Аккаунт успешно удалён');
  } catch (error: any) {
    console.error('Ошибка при удалении аккаунта:', error);
    if (error.response?.status === 401) {
      alert('Сессия истекла. Пожалуйста, войдите снова.');
      authStore.logout();
      router.push('/login');
    } else {
      alert('Не удалось удалить аккаунт. Попробуйте позже.');
    }
  } finally {
    deleting.value = false;
  }
};

const resendVerification = async () => {
  if (!user.value?.email) return;
  resending.value = true;
  try {
    await axios.post('/auth/resend-verification-code', {
      email: user.value.email
    });
    alert('✅ Код подтверждения отправлен на вашу почту');
  } catch (error: any) {
    console.error('Error resending code:', error);
    if (error.response) {
      switch (error.response.status) {
        case 400:
          if (error.response.data?.detail === 'Email already verified') {
            alert('✅ Ваш email уже подтвержден');
            await authStore.checkAuth();
          } else {
            alert(`❌ ${error.response.data?.detail || 'Ошибка запроса'}`);
          }
          break;
        case 404:
          alert('❌ Пользователь не найден');
          break;
        default:
          alert(`❌ ${error.response.data?.detail || 'Ошибка сервера'}`);
      }
    } else if (error.code === 'ERR_NETWORK') {
      alert('❌ Ошибка сети. Проверьте подключение к серверу.');
    } else {
      alert('❌ Не удалось отправить код. Попробуйте позже.');
    }
  } finally {
    resending.value = false;
  }
};

// Вспомогательная функция для форматирования ролей учителя
function formatTeacherRoles(teacherInfo: TeacherInfo): string {
  const roleNames: string[] = [];
  if (teacherInfo.roles.includes('supervisor')) roleNames.push('Научный руководитель');
  if (teacherInfo.roles.includes('expert')) roleNames.push('Эксперт');
  if (teacherInfo.roles.includes('customer')) roleNames.push('Заказчик');
  if (teacherInfo.curator) roleNames.push('Куратор');
  return roleNames.join(', ') || 'Роли не назначены';
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

.home-button {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 50%;
  width: 50px;
  height: 50px;
  font-size: 28px;
  cursor: pointer;
  box-shadow: var(--shadow);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  color: var(--text-primary);
}

.home-button:hover {
  background: var(--bg-card);
  transform: scale(1.1) translateY(-2px);
  box-shadow: var(--shadow-strong);
}

.profile-card {
  background: var(--bg-card);
  border-radius: 32px;
  box-shadow: var(--shadow-strong);
  padding: 40px;
  width: 100%;
  max-width: 500px;
  transition: transform 0.2s, background 0.3s;
  overflow: hidden;
}

.profile-card:hover {
  transform: translateY(-5px);
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
  transform: scale(1.05);
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
  align-items: baseline;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-color);
  overflow-wrap: break-word;
  word-wrap: break-word;
  gap: 10px;
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
  gap: 6px;
  font-weight: normal;
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
  transition: background-color 0.2s, transform 0.1s;
  margin-top: 8px;
}

.edit-button:hover {
  background-color: var(--accent-hover);
}

.edit-button:active {
  transform: scale(0.98);
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
  transition: background-color 0.2s, transform 0.1s;
  margin-top: 12px;
}

.logout-button:hover {
  background-color: var(--danger-hover);
}

.logout-button:active {
  transform: scale(0.98);
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
  transition: background-color 0.2s, transform 0.1s;
  box-shadow: var(--shadow-strong);
}

.delete-account-button:hover:not(:disabled) {
  background-color: #b71c1c;
  transform: translateY(-2px);
  box-shadow: var(--shadow-strong);
}

.delete-account-button:active:not(:disabled) {
  transform: scale(0.98);
}

.delete-account-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>