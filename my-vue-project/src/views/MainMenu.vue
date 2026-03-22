<template>
  <div class="main-menu">
    <header class="menu-header">
      <div class="header-left"></div>
      <h1 class="welcome-message">
        Добро пожаловать, <span class="username">{{ authStore.user?.nickname }}</span>!
      </h1>
      <div class="header-actions">
        <ThemeToggle />
        <button class="profile-button" @click="goTo('profile')">Личный кабинет</button>
      </div>
    </header>

    <div class="menu-container">
      <nav class="menu-list">
        <button class="menu-item" @click="goTo('my-projects')">Ваши проекты</button>
        <button class="menu-item" @click="goTo('users')">Список пользователей</button>
        <button class="menu-item" @click="goTo('projects')">Все проекты</button>
        <!-- Кнопка админ-панели, видимая только админу -->
        <button v-if="authStore.user?.is_admin" class="menu-item admin-button" @click="goTo('admin')">
          ⚙️ Админ панель
        </button>
      </nav>
    </div>

    <button class="logout-button" @click="logout">Выйти</button>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';
import ThemeToggle from '@/components/ThemeToggle.vue';

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
/* предыдущие стили + для admin-button */
.admin-button {
  background: var(--danger-color) !important; /* или другой цвет для отличия */
  color: white;
}
.admin-button:hover {
  background: var(--danger-hover) !important;
}
</style>

<style scoped>
.main-menu {
  min-height: 100vh;
  background: var(--bg-page);
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  padding: 2rem;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  transition: background 0.3s;
}

/* Шапка: сетка для центрирования приветствия */
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
  text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
  text-align: center;
}

.light-theme .welcome-message {
  text-shadow: 1px 1px 2px rgba(255,255,255,0.8);
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

/* Кнопка личного кабинета */
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
  transition: all 0.2s ease;
  border: 1px solid var(--border-color);
}

.profile-button:hover {
  background: var(--accent-hover);
  box-shadow: var(--shadow-strong);
  transform: translateY(-2px);
}

/* Контейнер для списка кнопок */
.menu-container {
  flex: 1;
  display: flex;
  justify-content: flex-start;
  align-items: center;
  padding-left: 2rem;
}

.menu-list {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
  max-width: 400px;
  width: 100%;
}

/* Кнопки меню */
.menu-item {
  background: var(--bg-card);
  backdrop-filter: blur(4px);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 1.2rem 2rem;
  font-size: 1.4rem;
  font-weight: 500;
  color: var(--text-primary);
  cursor: pointer;
  box-shadow: var(--shadow);
  transition: all 0.2s ease;
  text-align: left;
}

.menu-item:hover {
  background: var(--bg-card);
  box-shadow: var(--shadow-strong);
  transform: translateX(10px) scale(1.02);
  border-color: var(--accent-color);
  color: var(--heading-color);
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
  transition: all 0.2s;
  width: fit-content;
}

.logout-button:hover {
  background: var(--danger-hover);
  color: var(--danger-color);
}
</style>