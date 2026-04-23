<template>
  <div class="my-projects-page">
    <header class="page-header">
      <h1>{{ $t('userProjects.title') }}</h1>
      <div class="header-actions">
        <ThemeToggle />
        <LanguageSwitcher />
        <HomeButton/>
      </div>
    </header>

    <div class="action-bar">
      <button class="create-button" @click="createProject">+ {{ $t('userProjects.createProject') }}</button>
    </div>

    <div v-if="loading" class="loading">{{ $t('common.loading') }}</div>
    <div v-else-if="projects.length === 0" class="no-projects">
      {{ $t('userProjects.noProjects') }}
    </div>
    <div v-else class="projects-grid">
      <div
        v-for="project in projects"
        :key="project.id"
        class="project-card"
        @click="goToDetails(project.id)"
      >
        <h3 class="project-title">{{ project.title }}</h3>
        <p class="project-description">{{ project.body.slice(0, 120) }}...</p>
        <div class="card-footer">
          <span class="participants-label">{{ $t('userProjects.participantsLabel') }}:</span>
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
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useProjectsStore } from '@/stores/projects';
import { useUsersStore } from '@/stores/users';
import { useRouter } from 'vue-router';
import ThemeToggle from '@/components/ThemeToggle.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';
import type { Project, ProjectRole } from '@/types';
import HomeButton from '@/components/HomeButton.vue';



const { t } = useI18n();
const projectsStore = useProjectsStore();
const usersStore = useUsersStore();
const router = useRouter();

const projects = ref<Project[]>([]);
const loading = ref(true);
const avatarError = ref<Record<number, boolean>>({});
const baseUrl = 'http://localhost:8000';

onMounted(async () => {
  if (usersStore.users.length === 0) {
    await usersStore.fetchAllUsers();
  }
  projects.value = await projectsStore.fetchUserProjects();
  loading.value = false;
});

function getUserFullName(id: number): string {
  const user = usersStore.users.find(u => u.id === id);
  return user ? user.fullname : `ID: ${id}`;
}

function getUserShortName(id: number): string {
  const user = usersStore.users.find(u => u.id === id);
  if (!user) return `ID: ${id}`;
  const fullname = user.fullname.trim();
  const parts = fullname.split(/\s+/);
  if (parts.length === 0) return user.nickname || '?';
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
  if (parts.length === 0) return user.nickname?.charAt(0).toUpperCase() || '?';
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

const createProject = () => {
  router.push('/project/edit/new');
};

const goToDetails = (id: number) => {
  router.push(`/project/${id}`);
};

const goHome = () => {
  router.push('/main');
};

const goToUser = (userId: number) => {
  router.push(`/user/${userId}`);
};
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

.light-theme .home-button:hover {
  background: rgba(0, 0, 0, 0.05);
}

.action-bar {
  max-width: 1200px;
  margin: 0 auto 30px;
  display: flex;
  justify-content: flex-start;
}

.create-button {
  background: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 50px;
  padding: 12px 24px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.1s;
  box-shadow: var(--shadow);
}

.create-button:hover {
  background: var(--accent-hover);
}

.create-button:active {
  transform: scale(0.98);
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

.project-title {
  color: var(--heading-color);
  margin-bottom: 12px;
  font-size: 1.3rem;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 8px;
  overflow-wrap: break-word;
  word-wrap: break-word;
  hyphens: auto;
}

.project-description {
  color: var(--text-primary);
  line-height: 1.5;
  flex: 1;
  margin-bottom: 16px;
  font-size: 0.95rem;
  overflow-wrap: break-word;
  word-wrap: break-word;
  hyphens: auto;
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

/* Горизонтальный скролл для участников */
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

.loading, .no-projects {
  text-align: center;
  color: var(--text-primary);
  font-size: 1.2rem;
  padding: 40px;
}
</style>