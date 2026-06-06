<template>
  <div class="my-projects-page">
    <header class="page-header">
      <h1>{{ $t('navigation.my_projects') }}</h1>
      <div class="header-actions">
        <ThemeToggle />
        <LanguageSwitcher />
        <HomeButton/>
      </div>
    </header>

    <!-- Кнопка создания проекта - показываем только если пользователь может создавать проекты -->
    <div v-if="canCreateProject" class="create-section">
      <button class="create-button-top" @click="createProject">
        + {{ $t('myProjects.createProjectButton') }}
      </button>
    </div>

    <div v-if="loading" class="loading">{{ $t('myProjects.loadingProjects') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="projects.length === 0" class="no-projects">
      <p>{{ $t('myProjects.noProjects') }}</p>
      <button v-if="canCreateProject" class="create-button" @click="createProject">
        {{ $t('myProjects.createProjectButton') }}
      </button>
    </div>
    <div v-else class="projects-grid">
      <div
        v-for="project in projects"
        :key="project.id"
        class="project-card"
        @click="goToProject(project.id)"
      >
        <!-- Бейдж статуса одобрения -->
        <div class="approval-badge" :class="getBadgeClass(project)">
          {{ getStatusText(project) }}
        </div>

        <h3 class="card-title">{{ project.title }}</h3>
        <p class="card-description">{{ (project.body || '').slice(0, 150) }}...</p>
        
        <!-- Вакансии проекта (только для одобренных проектов) -->
        <div v-if="isProjectApproved(project) && getProjectVacancies(project).length > 0" class="project-vacancies">
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
          <span class="participants-label">{{ $t('myProjects.participantsLabel') }}:</span>
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
import { ref, onMounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useUsersStore } from '@/stores/users';
import { useI18n } from 'vue-i18n';
import ThemeToggle from '@/components/ThemeToggle.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';

import type { Project, ProjectRole } from '@/types';
import HomeButton from '@/components/HomeButton.vue';
import api from '@/utils/api'

const { t } = useI18n();
const router = useRouter();
const authStore = useAuthStore();
const usersStore = useUsersStore();

const projects = ref<Project[]>([]);
const loading = ref(true);
const error = ref('');
const avatarError = ref<Record<number, boolean>>({});
const authChecked = ref(false);
const projectStatuses = ref<Map<number, { status: string; text: string; badgeClass: string }>>(new Map());

const currentUserId = computed(() => authStore.user?.id);
const isAuthenticated = computed(() => authStore.isAuthenticated);

const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Проверка, может ли пользователь создавать проекты
// Ученик НЕ может создавать проекты (только заказчик или куратор)
const canCreateProject = computed(() => {
  const user = authStore.user;
  if (!user) return false;
  if (user.is_outdated) return false;

  // Администратор может создавать проекты
  if (user.is_admin) return true;

  // Если пользователь НЕ учитель (обычный ученик) - НЕ может создавать проекты
  if (!user.is_teacher) {
    return false;
  }
  
  // Учитель может создавать проекты, если он заказчик или куратор
  if (user.is_teacher && user.teacher_info) {
    return user.teacher_info.roles?.includes('customer') || user.teacher_info.curator === true;
  }
  
  return false;
});

// Получение статуса проекта
async function fetchProjectStatus(projectId: number): Promise<{ status: string; text: string; badgeClass: string } | null> {
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

async function loadAllProjectStatuses(projectsList: Project[]) {
  const promises = projectsList.map(project => fetchProjectStatus(project.id));
  await Promise.all(promises);
}

function isProjectApproved(project: Project): boolean {
  const cached = projectStatuses.value.get(project.id);
  return cached?.status === 'approved';
}

function getStatusText(project: Project): string {
  const cached = projectStatuses.value.get(project.id);
  return cached?.text || t('allProjects.loading');
}

function getBadgeClass(project: Project): string {
  const cached = projectStatuses.value.get(project.id);
  return cached?.badgeClass || 'badge-loading';
}

function getRoleDisplay(role: ProjectRole): string {
  return t(`roles.${role}`);
}

function getProjectVacancies(project: Project): Array<{ role: ProjectRole; deficit: number }> {
  if (!isProjectApproved(project)) return [];
  
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

onMounted(async () => {
  console.log('MyProjects mounted - checking auth...');
  console.log('Token exists:', !!localStorage.getItem('access_token'));
  
  if (!authStore.isAuthenticated) {
    const isValid = await authStore.checkAuth();
    console.log('Auth check result:', isValid);
    
    if (!isValid) {
      console.log('Not authenticated, redirecting to login');
      router.push('/login');
      return;
    }
  }
  
  authChecked.value = true;
  await loadUserProjects();
});

watch(isAuthenticated, (newVal) => {
  console.log('isAuthenticated changed:', newVal);
  if (!newVal) {
    router.push('/login');
  }
});

async function loadUserProjects() {
  if (!authChecked.value) return;
  
  console.log('Loading projects for user:', currentUserId.value);
  
  if (!currentUserId.value) {
    error.value = t('myProjects.notAuthorized');
    loading.value = false;
    return;
  }

  loading.value = true;
  error.value = '';

  try {
    if (usersStore.users.length === 0) {
      await usersStore.fetchAllUsers();
    }

    console.log('Fetching projects for participant_id:', currentUserId.value);
    const response = await api.get(`/projects/?participant_id=${currentUserId.value}`);
    projects.value = response.data;
    console.log('Projects loaded:', projects.value.length);
    avatarError.value = {};
    
    // Загружаем статусы для всех проектов
    await loadAllProjectStatuses(projects.value);
  } catch (err: any) {
    console.error('Error loading projects:', err);
    
    if (err.response?.status === 401) {
      const isValid = await authStore.checkAuth();
      if (isValid) {
        try {
          const response = await api.get(`/projects/?participant_id=${currentUserId.value}`);
          projects.value = response.data;
          await loadAllProjectStatuses(projects.value);
        } catch (retryErr) {
          error.value = t('myProjects.errorLoad');
        }
      } else {
        router.push('/login');
      }
    } else {
      error.value = err.response?.data?.detail || t('myProjects.errorLoad');
    }
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

function getUserAvatar(id: number): string | undefined {
  if (avatarError.value[id]) return undefined;
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

function createProject() {
  // Дополнительная проверка перед созданием проекта
  if (!canCreateProject.value) {
    alert(t('myProjects.noCreatePermission'));
    return;
  }
  router.push('/project/edit/new');
}
</script>

<style scoped>
.my-projects-page {
  min-height: 100vh;
  background: var(--bg-page);
  padding: 20px;
  box-sizing: border-box;
  transition: background 0.3s;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto 20px;
}

.page-header h1 {
  color: var(--heading-color);
  font-size: 2.5rem;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.create-section {
  max-width: 1200px;
  margin: 0 auto 30px;
  display: flex;
  justify-content: flex-start;
}

.create-button-top {
  background: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 30px;
  padding: 12px 24px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: var(--shadow);
}

.create-button-top:hover {
  background: var(--accent-hover);
  box-shadow: var(--shadow-strong);
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
  box-shadow: var(--shadow-strong);
}

/* Бейдж статуса */
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
  hyphens: auto;
  padding-right: 100px;
}

.card-description {
  color: var(--text-primary);
  line-height: 1.5;
  flex: 1;
  margin-bottom: 16px;
  overflow-wrap: break-word;
  word-wrap: break-word;
  hyphens: auto;
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
  overflow-wrap: break-word;
  word-wrap: break-word;
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
  display: block;
}

.participant-avatar span {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
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

.create-button {
  margin-top: 20px;
  padding: 12px 24px;
  background-color: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 50px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}

.create-button:hover {
  background-color: var(--accent-hover);
}

.loading, .error, .no-projects {
  text-align: center;
  color: var(--text-primary);
  font-size: 1.2rem;
  padding: 40px;
}
</style>
