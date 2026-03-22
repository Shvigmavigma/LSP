<template>
  <div class="all-projects-page">
    <header class="projects-header">
      <h1>Все проекты</h1>
      <div class="header-actions">
        <ThemeToggle />
        <button class="home-button" @click="goHome" title="На главную">🏠</button>
      </div>
    </header>

    <!-- Вкладки -->
    <div class="filter-tabs">
      <button
        class="tab-button"
        :class="{ active: filterType === 'all' }"
        @click="filterType = 'all'"
      >
        Все проекты
      </button>
      <button
        class="tab-button"
        :class="{ active: filterType === 'free' }"
        @click="filterType = 'free'"
      >
        Свободные
      </button>
      <button
        class="tab-button"
        :class="{ active: filterType === 'taken' }"
        @click="filterType = 'taken'"
      >
        Занятые
      </button>
    </div>

    <div class="search-container">
      <input
        v-model="search"
        placeholder="Поиск по названию..."
        @input="searchProjects"
      />
    </div>

    <div v-if="loading" class="loading">Загрузка...</div>
    <div v-else-if="filteredProjects.length === 0" class="no-projects">Проекты не найдены</div>
    <div v-else class="projects-grid">
      <div
        v-for="project in filteredProjects"
        :key="project.id"
        class="project-card"
        @click="goToProject(project.id)"
      >
        <h3 class="card-title">{{ project.title }}</h3>
        <p class="card-description">{{ project.body.slice(0, 150) }}...</p>
        <div class="card-footer">
          <span class="participants-label">Участники:</span>
          <div class="participants-list">
            <div
              v-for="participant in project.participants"
              :key="participant.user_id"
              class="participant-item"
              @click.stop="goToUser(participant.user_id)"
            >
              <div class="participant-avatar">
                <img
                  v-if="getUserAvatar(participant.user_id) && !avatarError[participant.user_id]"
                  :src="getUserAvatar(participant.user_id)"
                  :alt="getUserNickname(participant.user_id)"
                  @error="avatarError[participant.user_id] = true"
                />
                <span v-else>{{ getUserInitials(participant.user_id) }}</span>
                <span class="role-badge" :title="getRoleDisplay(participant.role)">
                  {{ getRoleIcon(participant.role) }}
                </span>
              </div>
              <span class="participant-name">{{ getUserNickname(participant.user_id) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useUsersStore } from '@/stores/users';
import ThemeToggle from '@/components/ThemeToggle.vue';
import axios from 'axios';
import type { Project, ProjectRole } from '@/types';

const router = useRouter();
const usersStore = useUsersStore();
const projects = ref<Project[]>([]);
const search = ref('');
const loading = ref(true);
const avatarError = ref<Record<number, boolean>>({});
const filterType = ref<'all' | 'free' | 'taken'>('all');

const baseUrl = 'http://localhost:8000';

const filteredProjects = computed(() => {
  if (filterType.value === 'all') return projects.value;
  if (filterType.value === 'free') {
    // Проекты без исполнителей (нет участников с ролью executor)
    return projects.value.filter(p => !p.participants.some(part => part.role === 'executor'));
  }
  // taken – проекты, у которых есть хотя бы один исполнитель
  return projects.value.filter(p => p.participants.some(part => part.role === 'executor'));
});

onMounted(async () => {
  if (usersStore.users.length === 0) {
    await usersStore.fetchAllUsers();
  }
  await fetchAll();
});

async function fetchAll() {
  loading.value = true;
  try {
    const res = await axios.get<Project[]>(`${baseUrl}/projects/`);
    projects.value = res.data;
    avatarError.value = {};
  } catch (error) {
    console.error('Error fetching projects:', error);
  } finally {
    loading.value = false;
  }
}

async function searchProjects() {
  if (!search.value) {
    await fetchAll();
    return;
  }
  loading.value = true;
  try {
    const res = await axios.get<Project[]>(`${baseUrl}/search`, {
      params: { q: search.value }
    });
    projects.value = res.data;
    avatarError.value = {};
  } catch (error) {
    console.error('Error searching projects:', error);
  } finally {
    loading.value = false;
  }
}

function getUserNickname(id: number): string {
  const user = usersStore.users.find(u => u.id === id);
  return user ? user.nickname : `ID: ${id}`;
}

function getUserAvatar(id: number): string | undefined {
  const user = usersStore.users.find(u => u.id === id);
  return user?.avatar ? `${baseUrl}/avatars/${user.avatar}` : undefined;
}

function getUserInitials(id: number): string {
  const user = usersStore.users.find(u => u.id === id);
  return user?.nickname?.charAt(0).toUpperCase() || '?';
}

function getRoleIcon(role: ProjectRole): string {
  const icons: Record<ProjectRole, string> = {
    customer: '📋',
    supervisor: '🎓',
    expert: '🔍',
    executor: '👤',
    curator: '👑',
  };
  return icons[role] || '';
}

function getRoleDisplay(role: ProjectRole): string {
  const map: Record<ProjectRole, string> = {
    customer: 'Заказчик',
    supervisor: 'Научный руководитель',
    expert: 'Эксперт',
    executor: 'Исполнитель',
    curator: 'Куратор',
  };
  return map[role];
}

function goToProject(id: number) {
  router.push(`/project/${id}`);
}

function goToUser(id: number) {
  router.push(`/user/${id}`);
}

function goHome() {
  router.push('/main');
}
</script>

<style scoped>
.all-projects-page {
  min-height: 100vh;
  background: var(--bg-page);
  padding: 20px;
  box-sizing: border-box;
  transition: background 0.3s;
}
.projects-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto 20px;
}
.projects-header h1 {
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
.search-container input:focus {
  border-color: var(--accent-color);
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.2);
}
.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
}
.project-card {
  background: var(--bg-card);
  border-radius: 16px;
  padding: 20px;
  box-shadow: var(--shadow);
  transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border-color);
}
.project-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-strong);
  border-color: var(--accent-color);
}
.card-title {
  color: var(--heading-color);
  margin-bottom: 12px;
  font-size: 1.3rem;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 8px;
  overflow-wrap: break-word;
  word-wrap: break-word;
}
.card-description {
  color: var(--text-primary);
  line-height: 1.5;
  flex: 1;
  margin-bottom: 16px;
  overflow-wrap: break-word;
}
.card-footer {
  border-top: 1px solid var(--border-color);
  padding-top: 12px;
  color: var(--text-secondary);
  font-size: 0.9rem;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.participants-label {
  font-weight: 500;
  color: var(--text-secondary);
  margin-right: 4px;
  flex-shrink: 0;
}
.participants-list {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.participant-item {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 4px;
  transition: background-color 0.2s;
  position: relative;
}
.participant-item:hover {
  background: rgba(128, 128, 128, 0.1);
}
.participant-avatar {
  position: relative;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--accent-color);
  color: var(--button-text);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
  overflow: hidden;
  flex-shrink: 0;
}
.participant-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.role-badge {
  position: absolute;
  bottom: -4px;
  right: -6px;
  font-size: 10px;
  background: var(--bg-card);
  border-radius: 50%;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  border: 1px solid var(--border-color);
}
.participant-name {
  color: var(--link-color);
  text-decoration: underline;
  font-size: 0.9rem;
  max-width: 80px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.participant-item:hover .participant-name {
  color: var(--link-hover);
}
.loading, .no-projects {
  text-align: center;
  color: var(--text-primary);
  font-size: 1.2rem;
  padding: 40px;
}

/* Стили для вкладок */
.filter-tabs {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-bottom: 30px;
  flex-wrap: wrap;
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
</style>