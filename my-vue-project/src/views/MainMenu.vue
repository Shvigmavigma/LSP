<template>
  <div class="main-menu">
    <header class="menu-header">
      <div class="header-left"></div>
      <div class="header-actions">
        <ThemeToggle />
        <LanguageSwitcher />
        <!-- Кнопка модерации - только для кураторов и админов -->
        <button 
          v-if="isModerator" 
          class="moderation-button" 
          @click="goTo('moderation')"
        >
           {{ $t('navigation.moderation') }}
          <span v-if="pendingApprovalsCount > 0" class="invitations-badge">{{ pendingApprovalsCount }}</span>
        </button>
        <button 
          v-if="isModerator" 
          class="moderation-button" 
          @click="goTo('lifecycle-projects')"
        >
          {{ $t('navigation.lifecycle_projects') }}
        </button>
        <button class="invitations-button" @click="goTo('invitations')">
           {{ $t('navigation.invitations') }}
          <span v-if="invitationsCount > 0" class="invitations-badge">{{ invitationsCount }}</span>
        </button>
        <button class="profile-button" @click="goTo('profile')">
           {{ greetingName }}
        </button>
      </div>
    </header>

    <div class="menu-container">
      <div class="menu-grid">
        <template v-if="!authStore.user?.is_admin">
          <button class="menu-item" @click="goTo('my-projects')">
            <img class="menu-item-image" :src="myProjectsIcon" alt="My Projects" />
            <span class="menu-item-text">{{ $t('navigation.my_projects') }}</span>
          </button>
          <button class="menu-item" @click="goTo('users')">
            <img class="menu-item-image" :src="usersIcon" alt="Users" />
            <span class="menu-item-text">{{ $t('navigation.all_users') }}</span>
          </button>
          <button 
            class="menu-item" 
            @click="goTo('old-projects')"
            @mouseenter="oldProjectsText = $t('navigation.old_projects_hover')"
            @mouseleave="oldProjectsText = $t('navigation.old_projects')"
          >
            <img class="menu-item-image" :src="oldProjectsIcon" alt="Old Projects" />
            <span class="menu-item-text">{{ oldProjectsText }}</span>
          </button>
          <button class="menu-item" @click="goTo('projects')">
            <img class="menu-item-image" :src="projectsIcon" alt="All Projects" />
            <span class="menu-item-text">{{ $t('navigation.all_projects') }}</span>
          </button>
          <!-- Кнопка модерации в меню для кураторов (не админов) -->
        </template>
        <template v-else>
          <button class="menu-item" @click="goTo('users')">
            <img class="menu-item-image" :src="usersIcon" alt="Users" />
            <span class="menu-item-text">{{ $t('navigation.all_users') }}</span>
          </button>
          <button class="menu-item" @click="goTo('projects')">
            <img class="menu-item-image" :src="projectsIcon" alt="All Projects"  />
            <span class="menu-item-text">{{ $t('navigation.all_projects') }}</span>
          </button>
          <button 
            class="menu-item" 
            @click="goTo('old-projects')"
            
            @mouseenter="oldProjectsText = $t('navigation.old_projects_hover')"
            @mouseout="oldProjectsText = $t('navigation.old_projects')"
          >
            <img class="menu-item-image" :src="oldProjectsIcon" alt="Old Projects" />
            <span class="menu-item-text">{{ oldProjectsText }}</span>
          </button>
          <!-- Кнопка модерации в меню для админов -->
          <button class="menu-item admin-button" @click="goTo('admin')">
            <img class="menu-item-image" :src="adminPanelIcon" alt="Admin Panel" />
            <span class="menu-item-text"> {{ $t('navigation.admin_panel') }}</span>
          </button>
        </template>
      </div>
    </div>

    <button class="logout-button" @click="logout" :title="$t('navigation.logout')">
      <i class="fas fa-sign-out-alt fa-flip-horizontal"></i>
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';
import ThemeToggle from '@/components/ThemeToggle.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';
import usersIcon from '@/assets/imgs/users.svg';
import projectsIcon from '@/assets/imgs/projects.png';
import oldProjectsIcon from '@/assets/imgs/projectsOLD.png';
import adminPanelIcon from '@/assets/imgs/AdminPanel.png';
import myProjectsIcon from '@/assets/imgs/myProjects.svg';
import '@fortawesome/fontawesome-free/css/all.css';
import api from '@/utils/api'

const authStore = useAuthStore();
const router = useRouter();
const invitationsCount = ref(0);
const pendingApprovalsCount = ref(0);
const oldProjectsText = ref('');

// Проверка: админ или куратор
const isModerator = computed(() => {
  const user = authStore.user;
  if (!user) return false;
  return user.is_admin || (user.is_teacher && user.teacher_info?.curator === true);
});

// Только куратор (не админ)
const isCurator = computed(() => {
  const user = authStore.user;
  if (!user) return false;
  return !user.is_admin && user.is_teacher && user.teacher_info?.curator === true;
});

// Загрузка счетчиков
const loadCounts = async () => {
  if (!authStore.isAuthenticated) return;
  
  try {
    // Загружаем приглашения
    const invitationsResponse = await api.get('/invitations');
    invitationsCount.value = invitationsResponse.data.length;
    
    // Загружаем ожидающие заявки (только для модераторов)
    if (isModerator.value) {
      try {
        const approvalsResponse = await api.get('/admin/approval-requests?status_filter=pending');
        pendingApprovalsCount.value = approvalsResponse.data.pending?.length || 0;
      } catch (error) {
        console.error('Failed to load approvals count:', error);
        pendingApprovalsCount.value = 0;
      }
    }
  } catch (error) {
    console.error('Failed to load counts:', error);
  }
};

// Периодическое обновление счетчиков
let countInterval: ReturnType<typeof setInterval>;

onMounted(() => {
  loadCounts();
  oldProjectsText.value = 'Старые проекты';
  
  countInterval = setInterval(() => {
    if (authStore.isAuthenticated) {
      loadCounts();
    }
  }, 30000); // Каждые 30 секунд
});

onUnmounted(() => {
  if (countInterval) {
    clearInterval(countInterval);
  }
});

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
</script>

<style scoped>
/* Все стили остаются без изменений */
.main-menu {
  min-height: 100vh;
  background: var(--bg-page);
  padding: clamp(1rem, 4vw, 2rem);
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  transition: background 0.3s;
}

.menu-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: clamp(1.5rem, 5vw, 3rem);
  gap: 1rem;
  flex-wrap: wrap;
}

.header-left {
  flex: 1;
}

.header-actions {
  display: flex;
  gap: clamp(0.5rem, 2vw, 1rem);
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
}

/* Кнопка модерации в хедере - такой же размер как у приглашений */
.moderation-button {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: clamp(0.5rem, 1.5vw, 0.8rem) clamp(1rem, 2.5vw, 1.8rem);
  font-size: clamp(0.9rem, 2vw, 1.1rem);
  font-weight: 500;
  color: var(--accent-color);
  cursor: pointer;
  box-shadow: var(--shadow);
  transition: background 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  position: relative;
  white-space: nowrap;
  margin-right: 20px; /* Отступ справа 20px от кнопки приглашений */
}

.moderation-button:hover {
  background: var(--accent-color);
  color: white;
  box-shadow: var(--shadow-strong);
  border-color: var(--accent-color);
}

.moderation-button:active {
  transform: none;
}

.invitations-button,
.profile-button {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: clamp(0.5rem, 1.5vw, 0.8rem) clamp(1rem, 2.5vw, 1.8rem);
  font-size: clamp(0.9rem, 2vw, 1.1rem);
  font-weight: 500;
  color: var(--text-primary);
  cursor: pointer;
  box-shadow: var(--shadow);
  transition: background 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  position: relative;
  white-space: nowrap;
}

.invitations-button:hover,
.profile-button:hover {
  background: var(--bg-card);
  box-shadow: var(--shadow-strong);
  border-color: var(--accent-color);
  color: var(--heading-color);
}

.invitations-button:active,
.profile-button:active {
  transform: none;
}

.invitations-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background-color: #f44336;
  color: white;
  border-radius: 50%;
  min-width: 20px;
  height: 20px;
  font-size: 11px;
  font-weight: bold;
  padding: 0 4px;
  margin-left: 6px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  line-height: 1;
}

@media (max-width: 768px) {
  .moderation-button,
  .invitations-button,
  .profile-button {
    white-space: normal;
    word-break: keep-all;
  }
}

@media (max-width: 480px) {
  .invitations-badge {
    min-width: 18px;
    height: 18px;
    font-size: 10px;
  }
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
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: clamp(1rem, 3vw, 2rem);
  width: 100%;
  align-items: stretch;
}

@media (max-width: 600px) {
  .menu-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
}

.menu-item {
  background: var(--bg-card);
  backdrop-filter: blur(4px);
  border: 1px solid var(--border-color);
  border-radius: 24px;
  padding: clamp(1rem, 4vw, 2rem);
  cursor: pointer;
  box-shadow: var(--shadow);
  transition: all 0.2s ease;
  text-align: left;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: flex-end;
  width: 100%;
  min-height: 200px;
  word-break: break-word;
  position: relative;
  gap: 0.5rem;
  overflow: hidden;
}

/* Карточка модерации в меню */
.moderation-menu-item {
  background: var(--bg-card);
  border: 2px solid var(--accent-color);
  display: flex;
  align-items: center;
  justify-content: center;
}

.moderation-menu-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, 
    color-mix(in srgb, var(--accent-color) 8%, transparent),
    color-mix(in srgb, var(--accent-color) 3%, transparent)
  );
  z-index: 0;
  border-radius: 24px;
}

.moderation-card-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.moderation-icon {
  font-size: 3rem;
  line-height: 1;
}

.moderation-text {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(0, 0, 0, 0.5) !important;
}

.menu-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background-color: #f44336;
  color: white;
  border-radius: 50%;
  min-width: 24px;
  height: 24px;
  font-size: 14px;
  font-weight: bold;
  padding: 0 6px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.menu-item-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.3;
  transition: opacity 0.2s ease, transform 0.2s ease;
  z-index: 0;
}

.menu-item-text {
  font-size: clamp(1rem, 4vw, 1.8rem);
  font-weight: 600;
  color: white;
  display: block;
  margin: 0;
  line-height: 1.3;
  text-align: left;
  position: relative;
  z-index: 1;
  background: rgba(0, 0, 0, 0.6);
  padding: 0.5rem 1rem;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.menu-item:hover {
  background: var(--bg-card);
  box-shadow: var(--shadow-strong);
  border-color: var(--accent-color);
}

.menu-item:hover .menu-item-text {
  color: white;
  background: rgba(0, 0, 0, 0.75);
}

.menu-item:hover .menu-item-image {
  opacity: 0.5;
  transform: scale(1.05);
}

.menu-item:active {
  transform: none;
}

.admin-button {
  background: var(--danger-color) !important;
}

.admin-button .menu-item-text {
  color: white;
  background: rgba(0, 0, 0, 0.7);
}

.admin-button:hover {
  background: var(--danger-hover) !important;
}

.logout-button {
  cursor: pointer;
  position: relative;
  display: inline-block;
  width: clamp(50px, 8vw, 60px);
  height: clamp(50px, 8vw, 60px);
  border-radius: 20px;
  overflow: hidden;
  align-self: flex-end;
  margin-top: clamp(1rem, 3vw, 2rem);
  background: transparent;
  border: none;
  padding: 0;
  flex-shrink: 0;
  transition: opacity 0.2s ease;
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
  border-radius: 20px;
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
  font-size: clamp(24px, 5vw, 30px);
  line-height: 1;
  transition: all 0.25s ease;
  z-index: 1;
  display: inline-block;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.logout-button:hover i {
  color: white;
}

.logout-button:active {
  transform: none;
}
</style>
