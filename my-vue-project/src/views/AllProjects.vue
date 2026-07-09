<template>
  <div class="all-projects-page">
    <header class="projects-header">
      <h1>{{ $t('allProjects.title') }}</h1>
      <div class="header-actions">
        <ThemeToggle />
        <HomeButton/>
      </div>
    </header>

    <!-- Вкладки -->
    <div class="filter-tabs">
      <button
        class="tab-button"
        :class="{ active: filterType === 'all' }"
        @click="filterType = 'all'"
      >
        {{ $t('allProjects.filterAll') }}
      </button>
      <button
        class="tab-button"
        :class="{ active: filterType === 'free' }"
        @click="filterType = 'free'"
      >
        {{ $t('allProjects.filterFree') }}
      </button>
      <button
        class="tab-button"
        :class="{ active: filterType === 'taken' }"
        @click="filterType = 'taken'"
      >
        {{ $t('allProjects.filterTaken') }}
      </button>
    </div>

    <div class="search-container">
      <input
        v-model="search"
        :placeholder="$t('allProjects.searchPlaceholder')"
        @input="searchProjects"
      />
      <select v-model="classFilter" class="class-filter" @change="fetchAll">
        <option value="">{{ $t('allProjects.allClasses') }}</option>
        <option value="8">8</option>
        <option value="9">9</option>
        <option value="10">10</option>
        <option value="11">11</option>
      </select>
    </div>

    <div v-if="loading" class="loading">{{ $t('common.loading') }}</div>
    <div v-else-if="filteredProjects.length === 0" class="no-projects">
      {{ $t('allProjects.noProjects') }}
    </div>
    <div v-else class="projects-grid">
      <div
        v-for="project in filteredProjects"
        :key="project.id"
        class="project-card"
        @click="goToProject(project.id)"
      >
        <!-- Бейдж статуса одобрения -->
        <div class="approval-badge" :class="getBadgeClass(project)">
          {{ getStatusText(project) }}
        </div>

        <h3 class="card-title">{{ project.title }}</h3>
        <div v-if="project.class_key" class="class-badge">{{ $t('allProjects.classLabel') }}: {{ project.class_key }}</div>
        <p class="card-description">{{ project.body?.slice(0, 150) || '' }}...</p>
        
        <!-- Вакансии проекта -->
        <div v-if="getProjectVacancies(project).length > 0" class="project-vacancies">
          <div class="vacancies-title">{{ $t('allProjects.vacancies') }}:</div>
          <div class="vacancies-list">
            <span 
              v-for="vacancy in getProjectVacancies(project)" 
              :key="vacancy.role" 
              class="vacancy-badge"
            >
              {{ getRoleDisplay(vacancy.role) }}: {{ vacancy.deficit }}
            </span>
          </div>
        </div>
        
        <div class="card-footer">
          <span class="participants-label">{{ $t('allProjects.participantsLabel') }}:</span>
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
                  :alt="getUserFullName(participant.user_id)"
                  @error="avatarError[participant.user_id] = true"
                />
                <span v-else>{{ getUserInitials(participant.user_id) }}</span>
                <span
                  class="role-badge"
                  :title="$t('roles.' + participant.role)"
                >
                  {{ getRoleIcon(participant.role) }}
                </span>
              </div>
              <span 
                class="participant-name" 
                :title="getUserFullName(participant.user_id)"
              >
                {{ getUserShortName(participant.user_id) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { getUserDisplayName as displayUserName, getUserInitial as displayUserInitial } from '@/utils/userDisplay';
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useUsersStore } from '@/stores/users';
import { useI18n } from 'vue-i18n';
import ThemeToggle from '@/components/ThemeToggle.vue';
import type { Project, ProjectRole } from '@/types';
import HomeButton from '@/components/HomeButton.vue';
import api from '@/utils/api';

const router = useRouter();
const usersStore = useUsersStore();
const { t } = useI18n();
const projects = ref<Project[]>([]);
const search = ref('');
const classFilter = ref('');
const loading = ref(true);
const avatarError = ref<Record<number, boolean>>({});
const filterType = ref<'all' | 'free' | 'taken'>('all');

// Кэш статусов проектов
const projectStatuses = ref<Map<number, { status: string; text: string; badgeClass: string }>>(new Map());

const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Функция для получения статуса проекта через эндпоинт
async function fetchProjectStatus(projectId: number): Promise<{ status: string; text: string; badgeClass: string } | null> {
  // Проверяем кэш
  if (projectStatuses.value.has(projectId)) {
    return projectStatuses.value.get(projectId)!;
  }
  
  try {
    const response = await api.get(`/projects/${projectId}/is-approved`);
    const isApproved = response.data.is_approved;
    const status = response.data.status;
    
    let text = '';
    let badgeClass = '';
    
    if (status === 'approved') {
      text = t('allProjects.approved');
      badgeClass = 'badge-approved';
    } else if (status === 'pending') {
      text = t('allProjects.pending');
      badgeClass = 'badge-pending';
    } else if (status === 'rejected') {
      text = t('allProjects.rejected');
      badgeClass = 'badge-rejected';
    } else {
      text = t('allProjects.draft');
      badgeClass = 'badge-draft';
    }
    
    const result = { status, text, badgeClass };
    projectStatuses.value.set(projectId, result);
    return result;
  } catch (error) {
    console.error(`Failed to fetch status for project ${projectId}:`, error);
    const fallback = { status: 'unknown', text: t('allProjects.statusUnknown'), badgeClass: 'badge-unknown' };
    projectStatuses.value.set(projectId, fallback);
    return fallback;
  }
}

// Функция для загрузки статусов всех проектов
async function loadAllProjectStatuses(projectsList: Project[]) {
  const promises = projectsList.map(project => fetchProjectStatus(project.id));
  await Promise.all(promises);
}

// Получение текста статуса для отображения (синхронная обертка)
function getStatusText(project: Project): string {
  const cached = projectStatuses.value.get(project.id);
  return cached?.text || t('allProjects.loading');
}

// Получение класса бейджа
function getBadgeClass(project: Project): string {
  const cached = projectStatuses.value.get(project.id);
  return cached?.badgeClass || 'badge-loading';
}

// Функция для получения вакансий проекта
function getProjectVacancies(project: Project): Array<{ role: ProjectRole; deficit: number }> {
  const required = project.required_roles || {};
  const vacancies: Array<{ role: ProjectRole; deficit: number }> = [];
  
  for (const [role, target] of Object.entries(required)) {
    const current = project.participants?.filter(p => p.role === role).length || 0;
    const deficit = Math.max(0, (target as number) - current);
    if (deficit > 0) {
      vacancies.push({ role: role as ProjectRole, deficit });
    }
  }
  
  return vacancies;
}

// Функция для получения отображаемого названия роли
function getRoleDisplay(role: ProjectRole): string {
  return t(`roles.${role}`);
}

// Проверка, есть ли в проекте вакансии
function hasVacancies(project: Project): boolean {
  return getProjectVacancies(project).length > 0;
}

const filteredProjects = computed(() => {
  let result = projects.value;
  
  // Применяем фильтр типа
  if (filterType.value === 'free') {
    result = projects.value.filter(p => hasVacancies(p));
  } else if (filterType.value === 'taken') {
    result = projects.value.filter(p => !hasVacancies(p));
  }
  
  return result;
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
    const res = await api.get<Project[]>('/projects/', {
      params: { class_key: classFilter.value || undefined }
    });
    projects.value = res.data;
    avatarError.value = {};
    // Загружаем статусы для всех проектов
    await loadAllProjectStatuses(projects.value);
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
    const res = await api.get<Project[]>('/search', {
      params: { q: search.value }
    });
    projects.value = classFilter.value ? res.data.filter(project => project.class_key === classFilter.value) : res.data;
    avatarError.value = {};
    // Загружаем статусы для найденных проектов
    await loadAllProjectStatuses(projects.value);
  } catch (error) {
    console.error('Error searching projects:', error);
  } finally {
    loading.value = false;
  }
}

function getUserFullName(id: number): string {
  const user = usersStore.users.find(u => u.id === id);
  return user ? user.fullname : `ID: ${id}`;
}

function getUserShortName(id: number): string {
  const user = usersStore.users.find(u => u.id === id);
  if (!user) return `ID: ${id}`;
  const fullname = user.fullname.trim();
  const parts = fullname.split(/\s+/);
  if (parts.length === 0) return displayUserName(user);
  const lastName = parts[0];
  const firstNameInitial = parts[1] ? parts[1].charAt(0).toUpperCase() + '.' : '';
  const patronymicInitial = parts[2] ? parts[2].charAt(0).toUpperCase() + '.' : '';
  let shortName = lastName;
  if (firstNameInitial) shortName += ' ' + firstNameInitial;
  if (patronymicInitial) shortName += ' ' + patronymicInitial;
  return shortName;
}

function getUserDisplayNameById(id: number): string {
  const user = usersStore.users.find(u => u.id === id);
  return user ? displayUserName(user) : `ID: ${id}`;
}

function getUserAvatar(id: number): string | undefined {
  const user = usersStore.users.find(u => u.id === id);
  return user?.avatar ? `${baseUrl}/avatars/${user.avatar}` : undefined;
}

function getUserInitials(id: number): string {
  const user = usersStore.users.find(u => u.id === id);
  if (!user) return '?';
  const parts = user.fullname.trim().split(/\s+/);
  if (parts.length === 0) return displayUserInitial(user);
  const lastName = parts[0];
  const firstName = parts[1] || '';
  const patronymic = parts[2] || '';
  let initials = lastName.charAt(0).toUpperCase();
  if (firstName) initials += firstName.charAt(0).toUpperCase();
  if (patronymic) initials += patronymic.charAt(0).toUpperCase();
  return initials;
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

.search-container {
  max-width: 600px;
  margin: 0 auto 30px;
  display: flex;
  gap: 10px;
}
.search-container input {
  flex: 1;
  padding: 12px 20px;
  border: 1px solid var(--input-border);
  border-radius: 50px;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
  background: var(--input-bg);
  color: var(--text-primary);
}
.class-filter {
  min-width: 120px;
  padding: 12px 14px;
  border: 1px solid var(--input-border);
  border-radius: 18px;
  background: var(--input-bg);
  color: var(--text-primary);
}
.class-badge {
  display: inline-flex;
  width: fit-content;
  padding: 4px 10px;
  border-radius: 12px;
  background: var(--accent-color);
  color: var(--button-text);
  font-size: 0.82rem;
  font-weight: 700;
  margin-bottom: 8px;
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
  transition: all 0.2s;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border-color);
  position: relative;
}
.project-card:hover {
  outline: 1px solid var(--accent-color);
  outline-offset: 1px;
  border-color: var(--accent-color);
}

/* Бейдж статуса одобрения */
.approval-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.7rem;
  font-weight: 500;
  z-index: 1;
  white-space: nowrap;
}

.badge-approved {
  background: rgba(76, 175, 80, 0.15);
  border: 1px solid #4caf50;
  color: #4caf50;
}
.badge-pending {
  background: rgba(255, 152, 0, 0.15);
  border: 1px solid #ff9800;
  color: #ff9800;
}
.badge-rejected {
  background: rgba(244, 67, 54, 0.15);
  border: 1px solid #f44336;
  color: #f44336;
}
.badge-draft {
  background: rgba(158, 158, 158, 0.15);
  border: 1px solid #9e9e9e;
  color: #9e9e9e;
}
.badge-unknown, .badge-loading {
  background: rgba(128, 128, 128, 0.15);
  border: 1px solid #808080;
  color: #808080;
}

.card-title {
  color: var(--heading-color);
  margin-bottom: 12px;
  font-size: 1.3rem;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 8px;
  overflow-wrap: break-word;
  word-wrap: break-word;
  padding-right: 100px;
}
.card-description {
  color: var(--text-primary);
  line-height: 1.5;
  flex: 1;
  margin-bottom: 16px;
  overflow-wrap: break-word;
}

/* Стили для вакансий */
.project-vacancies {
  margin-bottom: 16px;
  padding: 12px;
  background: rgba(66, 185, 131, 0.05);
  border-radius: 12px;
  border: 1px solid rgba(66, 185, 131, 0.1);
}
.vacancies-title {
  font-weight: 600;
  color: var(--accent-color);
  margin-bottom: 8px;
  font-size: 0.9rem;
}
.vacancies-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.vacancy-badge {
  background: var(--accent-color);
  color: white;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 500;
  white-space: nowrap;
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
  flex-wrap: nowrap;
  overflow-x: auto;
  gap: 8px;
  white-space: nowrap;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
  max-width: 100%;
  padding-bottom: 4px;
}
.participant-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 4px;
  transition: background-color 0.2s;
  position: relative;
  white-space: nowrap;
  flex-shrink: 0;
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
  max-width: 120px;
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
  box-shadow: 0 4px 12px rgba(66, 185, 131, 0.2);
}
.tab-button:hover {
  background: rgba(66, 185, 131, 0.15);
  color: var(--accent-color);
  border-color: rgba(66, 185, 131, 0.3);
}
.tab-button.active:hover {
  background: rgba(66, 185, 131, 0.2);
  box-shadow: 0 4px 12px rgba(66, 185, 131, 0.3);
}
</style>
