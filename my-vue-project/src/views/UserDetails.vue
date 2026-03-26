<template>
  <div class="user-details-page">
    <header class="details-header">
      <h1>{{ $t('userDetails.title') }}</h1>
      <div class="header-actions">
        <ThemeToggle />
        <LanguageSwitcher />
        <button class="home-button" @click="goHome" :title="$t('common.home')">🏠</button>
      </div>
    </header>

    <div v-if="loadingUser" class="loading">{{ $t('common.loading') }}</div>
    <div v-else-if="errorUser" class="error">{{ errorUser }}</div>
    <div v-else-if="user" class="user-info-card">
      <div class="user-avatar" @click="openAvatarModal" :class="{ clickable: user.avatar }">
        <img
          v-if="user.avatar && !avatarError"
          :src="avatarUrl"
          :alt="user.nickname"
          @error="avatarError = true"
        />
        <span v-else>{{ user.nickname.charAt(0).toUpperCase() }}</span>
      </div>
      <h2 class="user-nickname">{{ user.nickname }}</h2>
      <p class="user-fullname">{{ user.fullname }}</p>
      <p class="user-email">{{ user.email }}</p>
      <p class="user-class">
        <template v-if="user.is_teacher">{{ $t('userDetails.teacher') }}</template>
        <template v-else>{{ $t('userDetails.classLabel') }} {{ user.class }}</template>
      </p>
      <p v-if="user.speciality" class="user-speciality">
        {{ $t('userDetails.specialityLabel') }} {{ user.speciality }}
      </p>
      <div v-if="user.is_teacher && user.teacher_info" class="user-roles">
        {{ $t('userDetails.rolesLabel') }} {{ formatTeacherRoles(user.teacher_info) }}
      </div>
    </div>

    <div class="projects-section">
      <h2>{{ $t('userDetails.projectsTitle') }}</h2>
      <div v-if="loadingProjects" class="loading">{{ $t('common.loading') }}</div>
      <div v-else-if="projects.length === 0" class="no-projects">{{ $t('userDetails.noProjects') }}</div>
      <div v-else class="projects-grid">
        <div
          v-for="project in projects"
          :key="project.id"
          class="project-card"
          @click="goToProject(project.id)"
        >
          <h3 class="card-title">{{ project.title }}</h3>
          <p class="card-description">{{ project.body.slice(0, 100) }}...</p>
          <div class="card-footer">
            <span class="participants-label">{{ $t('userDetails.participantsLabel') }}:</span>
            <div class="participants-list">
              <div
                v-for="participant in project.participants"
                :key="participant.user_id"
                class="participant-item"
                @click.stop="goToUser(participant.user_id)"
              >
                <div class="participant-avatar">
                  <img
                    v-if="getUserAvatar(participant.user_id) && !avatarErrorMap[participant.user_id]"
                    :src="getUserAvatar(participant.user_id)"
                    :alt="getUserNickname(participant.user_id)"
                    @error="avatarErrorMap[participant.user_id] = true"
                  />
                  <span v-else>{{ getUserInitials(participant.user_id) }}</span>
                  <span class="role-badge" :title="$t(`roles.${participant.role}`)">
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

    <AvatarModal
      :show="showAvatarModal"
      :src="avatarUrl"
      :alt="user?.nickname"
      @close="showAvatarModal = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useUsersStore } from '@/stores/users';
import ThemeToggle from '@/components/ThemeToggle.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';
import AvatarModal from '@/components/AvatarModal.vue';
import type { User, Project, TeacherInfo, ProjectRole } from '@/types';
import axios from 'axios';

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const usersStore = useUsersStore();

const user = ref<User | null>(null);
const projects = ref<Project[]>([]);
const loadingUser = ref(true);
const loadingProjects = ref(true);
const errorUser = ref('');
const avatarError = ref(false);
const showAvatarModal = ref(false);
const avatarErrorMap = ref<Record<number, boolean>>({});

const baseUrl = 'http://localhost:8000';

const avatarUrl = computed(() => {
  if (!user.value?.avatar) return '';
  return `${baseUrl}/avatars/${user.value.avatar}`;
});

const openAvatarModal = () => {
  if (user.value?.avatar && !avatarError.value) {
    showAvatarModal.value = true;
  }
};

// Загрузка данных пользователя и его проектов
const loadUserData = async (id: number) => {
  loadingUser.value = true;
  loadingProjects.value = true;
  errorUser.value = '';
  avatarError.value = false;
  avatarErrorMap.value = {};

  if (usersStore.users.length === 0) {
    await usersStore.fetchAllUsers();
  }

  const foundUser = usersStore.users.find(u => u.id === id);
  if (foundUser) {
    user.value = foundUser;
    loadingUser.value = false;
  } else {
    try {
      const response = await axios.get(`/users/${id}`);
      user.value = response.data;
      usersStore.users.push(response.data);
      loadingUser.value = false;
    } catch (err) {
      errorUser.value = t('userDetails.userNotFound');
      loadingUser.value = false;
      loadingProjects.value = false;
      return;
    }
  }

  try {
    const response = await axios.get(`/projects/?participant_id=${id}`);
    projects.value = response.data;
  } catch (err) {
    console.error('Ошибка загрузки проектов:', err);
  } finally {
    loadingProjects.value = false;
  }
};

onMounted(async () => {
  const id = Number(route.params.id);
  if (!isNaN(id)) {
    await loadUserData(id);
  } else {
    errorUser.value = t('userDetails.invalidId');
    loadingUser.value = false;
  }
});

watch(() => route.params.id, async (newId) => {
  const id = Number(newId);
  if (!isNaN(id)) {
    await loadUserData(id);
  } else {
    errorUser.value = t('userDetails.invalidId');
    loadingUser.value = false;
  }
});

function getUserNickname(id: number): string {
  const u = usersStore.users.find(u => u.id === id);
  return u ? u.nickname : `ID: ${id}`;
}

function getUserAvatar(id: number): string | undefined {
  const u = usersStore.users.find(u => u.id === id);
  return u?.avatar ? `${baseUrl}/avatars/${u.avatar}` : undefined;
}

function getUserInitials(id: number): string {
  const u = usersStore.users.find(u => u.id === id);
  return u?.nickname?.charAt(0).toUpperCase() || '?';
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

function formatTeacherRoles(info: TeacherInfo): string {
  const roles: string[] = [];
  if (info.roles.includes('supervisor')) roles.push(t('roles.supervisor'));
  if (info.roles.includes('expert')) roles.push(t('roles.expert'));
  if (info.roles.includes('customer')) roles.push(t('roles.customer'));
  if (info.curator) roles.push(t('roles.curator'));
  return roles.join(', ') || t('userDetails.noRoles');
}

const goToProject = (projectId: number) => {
  router.push(`/project/${projectId}`);
};

const goToUser = (userId: number) => {
  router.push(`/user/${userId}`);
};

const goHome = () => {
  router.push('/main');
};
</script>

<style scoped>
.user-details-page {
  min-height: 100vh;
  background: var(--bg-page);
  padding: 20px;
  box-sizing: border-box;
  transition: background 0.3s;
}
.details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto 20px;
}
.details-header h1 {
  color: var(--heading-color);
  font-size: 2rem;
  margin: 0;
  overflow-wrap: break-word;
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
.user-info-card {
  background: var(--bg-card);
  border-radius: 24px;
  box-shadow: var(--shadow-strong);
  padding: 30px;
  max-width: 600px;
  margin: 0 auto 40px;
  text-align: center;
  transition: background 0.3s;
}
.user-avatar {
  width: 80px;
  height: 80px;
  background: var(--accent-color);
  color: var(--button-text);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  font-weight: bold;
  margin: 0 auto 16px;
  overflow: hidden;
  transition: opacity 0.2s;
}
.user-avatar.clickable {
  cursor: pointer;
}
.user-avatar.clickable:hover {
  opacity: 0.8;
}
.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.user-nickname {
  color: var(--heading-color);
  margin-bottom: 8px;
  font-size: 1.8rem;
  overflow-wrap: break-word;
}
.user-fullname {
  color: var(--text-primary);
  font-size: 1.2rem;
  margin-bottom: 8px;
}
.user-email {
  color: var(--text-secondary);
  font-size: 1rem;
  margin-bottom: 8px;
}
.user-class, .user-speciality, .user-roles {
  color: var(--text-secondary);
  font-size: 1rem;
  margin-top: 4px;
}
.projects-section {
  max-width: 1000px;
  margin: 0 auto;
}
.projects-section h2 {
  color: var(--heading-color);
  font-size: 1.8rem;
  margin-bottom: 24px;
  text-align: center;
}
.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}
.project-card {
  background: var(--bg-card);
  border-radius: 16px;
  padding: 20px;
  box-shadow: var(--shadow);
  transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
  cursor: pointer;
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
}
.project-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-strong);
  border-color: var(--accent-color);
}
.card-title {
  color: var(--heading-color);
  margin-bottom: 10px;
  font-size: 1.2rem;
  overflow-wrap: break-word;
}
.card-description {
  color: var(--text-primary);
  line-height: 1.5;
  margin-bottom: 12px;
  font-size: 0.95rem;
  flex: 1;
  overflow-wrap: break-word;
}
.card-footer {
  border-top: 1px solid var(--border-color);
  padding-top: 8px;
  color: var(--text-secondary);
  font-size: 0.9rem;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.participants-label {
  font-weight: 500;
  margin-right: 4px;
  color: var(--text-secondary);
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
.loading, .error, .no-projects {
  text-align: center;
  color: var(--text-primary);
  font-size: 1.2rem;
  padding: 40px;
}
</style>