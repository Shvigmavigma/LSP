<template>
  <div class="main-menu">
    <header class="menu-header">
      <div class="header-left"></div>
      <h1 class="welcome-message">
        {{ $t('common.welcome') }}, <span class="username">{{ authStore.user?.nickname }}</span>!
      </h1>
      <div class="header-actions">
        <ThemeToggle />
        <LanguageSwitcher />
        <button class="profile-button" @click="goTo('profile')">{{ $t('navigation.profile') }}</button>
      </div>
    </header>

    <div class="menu-container">
      <div class="menu-grid">
        <!-- Для обычных пользователей -->
        <template v-if="!authStore.user?.is_admin">
          <button class="menu-item" @click="goTo('my-projects')">{{ $t('navigation.my_projects') }}</button>
          <button class="menu-item" @click="goTo('users')">{{ $t('navigation.all_users') }}</button>
          <button class="menu-item" @click="goTo('old-projects')">{{ $t('navigation.old_projects') }}</button>
          <button class="menu-item" @click="goTo('projects')">{{ $t('navigation.all_projects') }}</button>
        </template>
        <!-- Для админов -->
        <template v-else>
          <button class="menu-item" @click="goTo('users')">{{ $t('navigation.all_users') }}</button>
          <button class="menu-item" @click="goTo('projects')">{{ $t('navigation.all_projects') }}</button>
          <button class="menu-item" @click="goTo('old-projects')">{{ $t('navigation.old_projects') }}</button>
          <button class="menu-item admin-button" @click="goTo('admin')">⚙️ {{ $t('navigation.admin_panel') }}</button>
        </template>
      </div>
    </div>

    <button class="logout-button" @click="logout">{{ $t('navigation.logout') }}</button>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';
import ThemeToggle from '@/components/ThemeToggle.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';

const authStore = useAuthStore();
const router = useRouter();

const goTo = (route: string) => {
  router.push(`/${route}`);
};

const logout = () => {
  authStore.logout();
  router.push('/login');
};
</script>

<style scoped>
.main-menu {
  min-height: 100vh;
  background: var(--bg-page);
  padding: 2rem;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  transition: background 0.3s;
}

/* Шапка */
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
}

.profile-button:hover {
  background: var(--accent-hover);
}

/* Контейнер для сетки — растягивается на всю оставшуюся высоту */
.menu-container {
  flex: 1;
  display: flex;
  align-items: stretch;
  min-height: 0; /* важно для корректного растяжения */
}

/* Сетка 2×2 занимает всё доступное пространство */
.menu-grid {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  width: 100%;
  align-items: stretch;
}

/* Кнопки-прямоугольники, растягиваются на всю высоту ячейки */
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
  /* Без transform: scale() */
}

.admin-button {
  background: var(--danger-color) !important;
  color: white;
}
.admin-button:hover {
  background: var(--danger-hover) !important;
}

/* Кнопка выхода */
.logout-button {
  background: var(--danger-bg);
  border: 1px solid var(--border-color);
  border-radius: 40px;
  padding: 0.8rem 2rem;
  font-size: 1rem;
  color: var(--danger-color);
  cursor: pointer;
  align-self: flex-end;
  margin-top: 2rem;
  transition: background 0.2s ease;
  width: fit-content;
}

.logout-button:hover {
  background: var(--danger-hover);
  color: var(--danger-color);
}
</style>