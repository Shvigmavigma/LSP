<template>
  <div class="all-users-page">
    <header class="users-header">
      <h1>Пользователи</h1>
      <div class="header-actions">
        <ThemeToggle />
        <button class="home-button" @click="goHome" title="На главную">🏠</button>
      </div>
    </header>

    <div class="filter-tabs">
      <button
        class="tab-button"
        :class="{ active: filterType === 'all' }"
        @click="setFilter('all')"
      >
        Все
      </button>
      <button
        class="tab-button"
        :class="{ active: filterType === 'students' }"
        @click="setFilter('students')"
      >
        Ученики
      </button>
      <button
        class="tab-button"
        :class="{ active: filterType === 'teachers' }"
        @click="setFilter('teachers')"
      >
        Учителя
      </button>
    </div>

    <div class="search-container">
      <input
        v-model="search"
        :placeholder="searchPlaceholder"
        @input="onSearchInput"
      />
    </div>

    <div v-if="loading" class="loading">Загрузка...</div>
    <div v-else-if="users.length === 0" class="no-users">Пользователи не найдены</div>
    <div v-else class="users-grid">
      <div
        v-for="user in users"
        :key="user.id"
        class="user-card"
        @click="goToUser(user.id)"
      >
        <div class="user-avatar">
          <img
            v-if="user.avatar && !imageError[user.id]"
            :src="avatarUrl(user.avatar)"
            :alt="user.nickname"
            @error="imageError[user.id] = true"
          />
          <span v-else>{{ user.nickname.charAt(0).toUpperCase() }}</span>
        </div>
        <h3 class="user-nickname">{{ user.nickname }}</h3>
        <p class="user-fullname">{{ user.fullname }}</p>
        <p class="user-email">{{ user.email }}</p>

        <template v-if="!user.is_teacher">
          <div class="user-class">Класс: {{ user.class }}</div>
          <div v-if="user.speciality" class="user-speciality">{{ user.speciality }}</div>
        </template>

        <template v-else>
          <div v-if="user.teacher_info" class="user-roles">
            {{ getRolesText(user) }}
          </div>
          <div v-if="user.speciality" class="user-speciality">Предмет: {{ user.speciality }}</div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useUsersStore } from '@/stores/users';
import ThemeToggle from '@/components/ThemeToggle.vue';
import type { User } from '@/types';

const router = useRouter();
const usersStore = useUsersStore();
const users = ref<User[]>([]);
const search = ref('');
const loading = ref(true);
const imageError = ref<Record<number, boolean>>({});
const filterType = ref<'all' | 'students' | 'teachers'>('all');

let searchTimer: ReturnType<typeof setTimeout> | null = null;

const baseUrl = 'http://localhost:8000';

const avatarUrl = (avatar: string) => `${baseUrl}/avatars/${avatar}`;

const searchPlaceholder = computed(() => {
  switch (filterType.value) {
    case 'students': return 'Поиск по ученикам...';
    case 'teachers': return 'Поиск по учителям...';
    default: return 'Поиск по всем пользователям...';
  }
});

async function loadUsers() {
  loading.value = true;
  try {
    if (filterType.value === 'students') {
      await usersStore.fetchStudents(search.value || undefined);
    } else if (filterType.value === 'teachers') {
      await usersStore.fetchTeachers(search.value || undefined);
    } else {
      await usersStore.fetchUsers(undefined, search.value || undefined);
    }
    users.value = usersStore.users;
    imageError.value = {};
  } catch (error) {
    console.error('Ошибка загрузки пользователей:', error);
  } finally {
    loading.value = false;
  }
}

watch([filterType, search], () => {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    loadUsers();
  }, 300);
});

onMounted(() => {
  loadUsers();
});

function onSearchInput() {
  imageError.value = {};
}

function setFilter(type: 'all' | 'students' | 'teachers') {
  filterType.value = type;
  imageError.value = {};
}

function goToUser(id: number) {
  router.push(`/user/${id}`);
}

function goHome() {
  router.push('/main');
}

function getRoleName(role: string): string {
  switch (role) {
    case 'supervisor': return 'Научный руководитель';
    case 'expert': return 'Эксперт';
    case 'customer': return 'Заказчик';
    default: return role;
  }
}

function getRolesText(user: User): string {
  if (!user.is_teacher || !user.teacher_info) return '';
  const roles = user.teacher_info.roles.map(role => getRoleName(role));
  if (user.teacher_info.curator) roles.push('Куратор');
  return roles.join(', ');
}
</script>

<style scoped>
.all-users-page {
  min-height: 100vh;
  background: var(--bg-page);
  padding: 20px;
  box-sizing: border-box;
  transition: background 0.3s;
}

.users-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto 20px;
}

.users-header h1 {
  color: var(--heading-color);
  font-size: 2.5rem;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.home-button {
  background: none;
  border: none;
  font-size: 2rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
  color: var(--text-primary);
}

.home-button:hover {
  background: rgba(255, 255, 255, 0.1);
}

.dark-theme .home-button:hover {
  background: rgba(255, 255, 255, 0.1);
}

.light-theme .home-button:hover {
  background: rgba(0, 0, 0, 0.05);
}

.filter-tabs {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-bottom: 30px;
}

.tab-button {
  padding: 10px 30px;
  border: 2px solid var(--border-color);
  border-radius: 50px;
  background: var(--bg-card);
  color: var(--text-secondary);
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tab-button.active {
  border-color: var(--accent-color);
  background: rgba(66, 185, 131, 0.1);
  color: var(--accent-color);
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(66, 185, 131, 0.2);
}

.search-container {
  max-width: 600px;
  margin: 0 auto 30px;
}

.search-container input {
  width: 100%;
  padding: 12px 20px;
  border: 1px solid var(--input-border);
  border-radius: 50px;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
  background: var(--input-bg);
  color: var(--text-primary);
}

.search-container input::placeholder {
  color: var(--text-secondary);
}

.search-container input:focus {
  border-color: var(--accent-color);
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.2);
}

.dark-theme .search-container input:focus {
  box-shadow: 0 0 0 3px rgba(1, 69, 172, 0.2);
}

.users-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.user-card {
  background: var(--bg-card);
  border-radius: 16px;
  padding: 20px;
  box-shadow: var(--shadow);
  transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  border: 1px solid var(--border-color);
  animation: fadeIn 0.3s ease;
}

.user-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-strong);
  border-color: var(--accent-color);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-avatar {
  position: relative;
  width: 60px;
  height: 60px;
  background: var(--accent-color);
  color: var(--button-text);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 12px;
  overflow: hidden;
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.user-avatar span {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.user-nickname {
  color: var(--heading-color);
  margin-bottom: 4px;
  font-size: 1.2rem;
  font-weight: 600;
}

.user-fullname {
  color: var(--text-primary);
  font-size: 0.95rem;
  margin-bottom: 6px;
}

.user-email {
  color: var(--text-secondary);
  font-size: 0.85rem;
  margin-bottom: 8px;
}

.user-class, .user-speciality {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-top: 4px;
}

.user-roles {
  margin-top: 6px;
  font-size: 0.9rem;
  color: var(--text-secondary);
  max-width: 100%;
  word-break: break-word;
}

.loading, .no-users {
  text-align: center;
  color: var(--text-primary);
  font-size: 1.2rem;
  padding: 40px;
}
</style>