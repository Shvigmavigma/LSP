<template>
  <div class="main-menu">
    <header class="menu-header">
      <div class="header-left"></div>
      <h1 class="welcome-message">
        {{ $t('common.welcome') }}, <span class="username">{{ greetingName }}</span>!
      </h1>
      <div class="header-actions">
        <ThemeToggle />
        <LanguageSwitcher />
        <button class="invitations-button" @click="goTo('invitations')">
          ✉️ {{ $t('navigation.invitations') }}
          <span v-if="invitationsCount > 0" class="invitations-badge">{{ invitationsCount }}</span>
        </button>
        <button class="profile-button" @click="goTo('profile')">{{ $t('navigation.profile') }}</button>
      </div>
    </header>

    <div class="menu-container">
      <div class="menu-grid">
        <template v-if="!authStore.user?.is_admin">
          <button class="menu-item" @click="goTo('my-projects')">{{ $t('navigation.my_projects') }}</button>
          <button class="menu-item" @click="goTo('users')">{{ $t('navigation.all_users') }}</button>
          <button class="menu-item" @click="goTo('old-projects')">{{ $t('navigation.old_projects') }}</button>
          <button class="menu-item" @click="goTo('projects')">{{ $t('navigation.all_projects') }}</button>
        </template>
        <template v-else>
          <button class="menu-item" @click="goTo('users')">{{ $t('navigation.all_users') }}</button>
          <button class="menu-item" @click="goTo('projects')">{{ $t('navigation.all_projects') }}</button>
          <button class="menu-item" @click="goTo('old-projects')">{{ $t('navigation.old_projects') }}</button>
          <button class="menu-item admin-button" @click="goTo('admin')">⚙️ {{ $t('navigation.admin_panel') }}</button>
        </template>
      </div>
    </div>

    <button class="logout-button" @click="logout" :title="$t('navigation.logout')">
      <i class="fas fa-sign-out-alt fa-flip-horizontal"></i>
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';
import ThemeToggle from '@/components/ThemeToggle.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';
import axios from 'axios';
import '@fortawesome/fontawesome-free/css/all.css';

const authStore = useAuthStore();
const router = useRouter();
const invitationsCount = ref(0);

const greetingName = computed(() => {
  const fullname = authStore.user?.fullname || '';
  const parts = fullname.trim().split(/\s+/);
  if (parts.length >= 2) {
    const firstName = parts[1];
    const patronymic = parts[2] || '';
    return patronymic ? `${firstName} ${patronymic}` : firstName;
  }
  return authStore.user?.nickname || 'Гость';
});

const goTo = (route: string) => {
  router.push(`/${route}`);
};

const logout = () => {
  authStore.logout();
  router.push('/login');
};

const loadInvitationsCount = async () => {
  if (!authStore.isAuthenticated) return;
  try {
    const response = await axios.get('/invitations');
    invitationsCount.value = response.data.length;
  } catch (error) {
    console.error('Failed to load invitations count:', error);
  }
};

onMounted(() => {
  loadInvitationsCount();
});
</script>

<style scoped>
/* ---- существующие стили (сохранить) ---- */
.main-menu {
  min-height: 100vh;
  background: var(--bg-page);
  padding: 2rem;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  transition: background 0.3s;
}

.menu-header {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  margin-bottom: 3rem;
  gap: 1rem;
}

.welcome-message {
  font-size: 2rem;
  font-weight: 400;
  color: var(--heading-color);
  margin: 0;
  text-align: center;
}

.username {
  font-weight: 500;
  color: var(--heading-color);
}

.header-actions {
  display: flex;
  gap: 10px;
  justify-self: end;
  align-items: center;
}

.invitations-button,
.profile-button {
  background: var(--accent-color);
  border: none;
  border-radius: 40px;
  padding: 0.8rem 1.8rem;
  font-size: 1.1rem;
  font-weight: 500;
  color: var(--button-text);
  cursor: pointer;
  box-shadow: var(--shadow);
  transition: background 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  position: relative;
}

.invitations-button:hover,
.profile-button:hover {
  background: var(--accent-hover);
}

/* Красная метка внутри кнопки (увеличенный кружок) */
.invitations-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background-color: #f44336;
  color: white;
  border-radius: 50%;
  min-width: 26px;
  height: 26px;
  font-size: 13px;
  font-weight: bold;
  padding: 0 6px;
  margin-left: 6px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  line-height: 1;
}

.menu-container {
  flex: 1;
  display: flex;
  align-items: stretch;
  min-height: 0;
}

.menu-grid {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  width: 100%;
  align-items: stretch;
}

.menu-item {
  background: var(--bg-card);
  backdrop-filter: blur(4px);
  border: 1px solid var(--border-color);
  border-radius: 32px;
  padding: 2rem 1rem;
  font-size: 1.8rem;
  font-weight: 600;
  color: var(--text-primary);
  cursor: pointer;
  box-shadow: var(--shadow);
  transition: background 0.2s ease, box-shadow 0.2s ease;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.menu-item:hover {
  background: var(--bg-card);
  box-shadow: var(--shadow-strong);
  border-color: var(--accent-color);
  color: var(--heading-color);
}

.admin-button {
  background: var(--danger-color) !important;
  color: white;
}
.admin-button:hover {
  background: var(--danger-hover) !important;
}

.logout-button {
  cursor: pointer;
  position: relative;
  display: inline-block;
  width: 60px;
  height: 60px;
  border-radius: 30px;
  overflow: hidden;
  align-self: flex-end;
  margin-top: 2rem;
  background: transparent;
  border: none;
  padding: 0;
}

.logout-button::before,
.logout-button::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  width: 100%;
  transition: all 0.25s ease;
  border-radius: 30px;
}

.logout-button::after {
  box-shadow: inset 0 0 0 1px var(--danger-color);
}

.logout-button::before {
  background: var(--danger-color);
  box-shadow: inset 0 0 0 60px var(--bg-card);
}

.logout-button:hover::before {
  box-shadow: inset 0 0 0 1px var(--bg-card);
}

.logout-button i {
  position: relative;
  color: var(--danger-color);
  font-size: 30px;
  line-height: 60px;
  transition: all 0.25s ease;
  z-index: 1;
  display: inline-block;
}

.logout-button:hover i {
  color: white;
}

.logout-button:not(:hover)::before,
.logout-button:not(:hover)::after,
.logout-button:not(:hover) i {
  transition: all 0.25s ease;
}

.logout-button:active {
  transform: scale(0.95);
  transition: transform 0.1s ease;
}
</style>