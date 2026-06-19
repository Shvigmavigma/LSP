<template>
  <div class="main-menu">
    <header class="menu-header">
      <div class="brand-block">
        <div class="brand-logo">
          <img src="/coc7.png" alt="LSP" />
        </div>
        <div class="brand-text">
          <p>{{ $t('navigation.system_title') }}</p>
          <h1>{{ $t('navigation.main_menu') }}</h1>
        </div>
      </div>

      <div class="header-actions">
        <LanguageSwitcher />
        <ThemeToggle />
        <button class="profile-button" type="button" @click="goTo('profile')">
          {{ greetingName }}
        </button>
      </div>
    </header>

    <main class="menu-content">
      <section class="intro-panel">
        <div>
          <p class="section-label">{{ $t('navigation.workspace') }}</p>
          <h2>{{ heroTitle }}</h2>
          <p class="intro-description">{{ heroDescription }}</p>
        </div>
      </section>

      <section v-if="quickActions.length" class="quick-actions" aria-label="Быстрые действия">
        <button
          v-for="action in quickActions"
          :key="action.route"
          class="quick-action"
          type="button"
          @click="goTo(action.route)"
        >
          <span class="quick-action-text">
            <strong>{{ action.label }}</strong>
            <small>{{ action.description }}</small>
          </span>
          <span v-if="action.badge && action.badge > 0" class="action-badge">
            {{ action.badge }}
          </span>
          <span v-else class="action-arrow">›</span>
        </button>
      </section>

      <section class="menu-grid" aria-label="Основные разделы">
        <button
          v-for="item in menuItems"
          :key="item.route"
          class="menu-card"
          :class="{ 'admin-card': item.route === 'admin' }"
          type="button"
          @click="goTo(item.route)"
        >
          <span class="card-visual">
            <img :src="item.icon" :alt="getItemLabel(item)" />
          </span>
          <span class="card-info">
            <strong>{{ getItemLabel(item) }}</strong>
            <small>{{ $t(item.descriptionKey) }}</small>
          </span>
          <span class="card-arrow">›</span>
        </button>
      </section>
    </main>

    <button class="logout-button" type="button" @click="logout" :title="$t('navigation.logout')">
      <i class="fas fa-sign-out-alt fa-flip-horizontal"></i>
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, shallowRef, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '@/stores/auth';
import { getUserDisplayName as displayUserName } from '@/utils/userDisplay';
import ThemeToggle from '@/components/ThemeToggle.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';
import usersIcon from '@/assets/imgs/users.svg';
import projectsIcon from '@/assets/imgs/projects.png';
import oldProjectsIcon from '@/assets/imgs/projectsOLD.png';
import adminPanelIcon from '@/assets/imgs/AdminPanel.png';
import myProjectsIcon from '@/assets/imgs/myProjects.svg';
import api from '@/utils/api';
import '@fortawesome/fontawesome-free/css/all.css';

type MenuItem = {
  labelKey: string;
  hoverLabelKey?: string;
  descriptionKey: string;
  route: string;
  icon: string;
};

type QuickAction = {
  label: string;
  description: string;
  route: string;
  badge?: number;
};

const authStore = useAuthStore();
const router = useRouter();
const { t } = useI18n();
const invitationsCount = ref(0);
const pendingApprovalsCount = ref(0);
const isMounted = ref(false);

const isModerator = computed(() => {
  const user = authStore.user;
  if (!user) return false;
  return user.is_admin || (user.is_teacher && user.teacher_info?.curator === true);
});

const heroTitle = computed(() =>
  authStore.user?.is_admin ? t('navigation.admin_hero_title') : t('navigation.user_hero_title')
);

const heroDescription = computed(() =>
  authStore.user?.is_admin
    ? t('navigation.admin_hero_desc')
    : t('navigation.user_hero_desc')
);

const quickActions = computed<QuickAction[]>(() => {
  const actions: QuickAction[] = [];

  if (isModerator.value) {
    actions.push(
      {
        label: t('navigation.moderation'),
        description: t('navigation.moderation_desc'),
        route: 'moderation',
        badge: pendingApprovalsCount.value,
      },
      {
        label: t('navigation.lifecycle_projects'),
        description: t('navigation.lifecycle_projects_desc'),
        route: 'lifecycle-projects',
      },
    );
  }

  actions.push({
    label: t('navigation.invitations'),
    description: t('navigation.invitations_desc'),
    route: 'invitations',
    badge: invitationsCount.value,
  });

  return actions;
});

const menuItems = computed<MenuItem[]>(() => {
  if (authStore.user?.is_admin) {
    return [
      {
        labelKey: 'navigation.all_users',
        descriptionKey: 'navigation.users_desc',
        route: 'users',
        icon: usersIcon,
      },
      {
        labelKey: 'navigation.all_projects',
        descriptionKey: 'navigation.projects_catalog_desc',
        route: 'projects',
        icon: projectsIcon,
      },
      {
        labelKey: 'navigation.old_projects',
        hoverLabelKey: 'navigation.old_projects_hover',
        descriptionKey: 'navigation.old_projects_desc',
        route: 'old-projects',
        icon: oldProjectsIcon,
      },
      {
        labelKey: 'navigation.admin_panel',
        descriptionKey: 'navigation.admin_panel_desc',
        route: 'admin',
        icon: adminPanelIcon,
      },
    ];
  }

  return [
    {
      labelKey: 'navigation.my_projects',
      descriptionKey: 'navigation.my_projects_desc',
      route: 'my-projects',
      icon: myProjectsIcon,
    },
    {
      labelKey: 'navigation.all_users',
      descriptionKey: 'navigation.users_lyceum_desc',
      route: 'users',
      icon: usersIcon,
    },
    {
      labelKey: 'navigation.old_projects',
      hoverLabelKey: 'navigation.old_projects_hover',
      descriptionKey: 'navigation.old_projects_desc',
      route: 'old-projects',
      icon: oldProjectsIcon,
    },
    {
      labelKey: 'navigation.all_projects',
      descriptionKey: 'navigation.all_projects_desc',
      route: 'projects',
      icon: projectsIcon,
    },
  ];
});

const getItemLabel = (item: MenuItem) => {
  return t(item.labelKey);
};

const greetingName = computed(() => {
  const fullname = authStore.user?.fullname || '';
  const parts = fullname.trim().split(/\s+/);
  if (parts.length >= 2) {
    const firstName = parts[1];
    const patronymic = parts[2] || '';
    return patronymic ? `${firstName} ${patronymic}` : firstName;
  }
  return authStore.user ? displayUserName(authStore.user) : 'Гость';
});

const loadCounts = async () => {
  if (!authStore.isAuthenticated || !isMounted.value) return;

  try {
    const invitationsResponse = await api.get('/invitations');
    invitationsCount.value = invitationsResponse.data.length;

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

let countInterval: ReturnType<typeof setInterval>;

onMounted(() => {
  isMounted.value = true;
  loadCounts();

  countInterval = setInterval(() => {
    if (authStore.isAuthenticated && isMounted.value) {
      loadCounts();
    }
  }, 30000);
});

onUnmounted(() => {
  isMounted.value = false;
  if (countInterval) {
    clearInterval(countInterval);
  }
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
.main-menu {
  min-height: 100vh;
  padding: 28px 32px 92px;
  background: var(--bg-page);
  color: var(--text-primary);
  position: relative;
}

:global(.dark-theme) .main-menu {
  background: var(--bg-page);
}

.menu-header {
  max-width: 1500px;
  margin: 0 auto 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 28px;
  position: relative;
  z-index: 1000000;
}

.brand-block {
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
}

.brand-logo {
  width: 58px;
  height: 58px;
  border-radius: 50%;
  overflow: hidden;
  flex: 0 0 58px;
  background: transparent;
  border: 1px solid color-mix(in srgb, var(--heading-color) 18%, transparent);
  box-shadow: 0 10px 26px rgba(0, 0, 0, 0.14);
}

.brand-logo img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}

.brand-text {
  min-width: 0;
}

.brand-text p,
.section-label {
  margin: 0 0 4px;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.brand-text h1 {
  margin: 0;
  color: var(--heading-color);
  font-size: 34px;
  line-height: 1.05;
}

.header-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  flex: 0 0 auto;
  position: relative;
  z-index: 1000000;
}

.profile-button {
  max-width: 230px;
  min-height: 44px;
  padding: 0 18px;
  border: 1px solid var(--border-color);
  border-radius: 16px;
  background: var(--bg-card);
  color: var(--text-primary);
  box-shadow: var(--shadow);
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: border-color 0.2s ease;
}

.profile-button:hover {
  border-color: var(--accent-color);
}

.menu-content {
  max-width: 1500px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 380px;
  grid-template-areas:
    "intro quick"
    "cards cards";
  gap: 22px;
  position: relative;
  z-index: 1;
}

.intro-panel {
  grid-area: intro;
  position: relative;
  overflow: hidden;
  isolation: isolate;
  min-height: 280px;
  padding: 34px;
  border-radius: 32px;
  background: linear-gradient(
    135deg,
    var(--heading-color) 0%,
    color-mix(in srgb, var(--heading-color) 85%, white 15%) 100%
  );
  border: 1px solid color-mix(in srgb, var(--heading-color) 18%, transparent);
  box-shadow: var(--shadow);
  display: flex;
  align-items: center;
}

:global(.dark-theme) .intro-panel {
  background: linear-gradient(
    135deg,
    #22344c 0%,
    #344762 100%
  );
  border-color: #2f4058;
}

.intro-panel::before {
  content: '';
  position: absolute;
  right: -140px;
  top: 50%;
  transform: translateY(-50%);
  width: 520px;
  height: 520px;
  border-radius: 50%;
  border: 36px solid rgba(255, 255, 255, 0.12);
  pointer-events: none;
}

.intro-panel::after {
  content: '';
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  width: 280px;
  height: 280px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  pointer-events: none;
}

.intro-panel > * {
  position: relative;
  z-index: 2;
}

.intro-panel h2 {
  margin: 0 0 10px;
  max-width: 780px;
  color: #fff;
  font-size: 56px;
  font-weight: 700;
  line-height: 1.05;
}

.intro-description {
  margin: 0;
  max-width: 650px;
  color: rgba(255, 255, 255, 0.82);
  font-size: 18px;
  line-height: 1.5;
}

.intro-panel .section-label {
  color: rgba(255, 255, 255, 0.78);
}

.quick-actions {
  grid-area: quick;
  display: grid;
  gap: 12px;
}

.quick-action {
  min-height: 82px;
  padding: 18px;
  border: 1px solid var(--border-color);
  border-radius: 18px;
  background: var(--bg-card);
  color: var(--text-primary);
  box-shadow: var(--shadow);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  text-align: left;
  transition: border-color 0.2s ease;
}

.quick-action:hover {
  border-color: var(--accent-color);
}

.quick-action-text {
  min-width: 0;
}

.quick-action strong {
  display: block;
  color: var(--heading-color);
  font-size: 17px;
  line-height: 1.2;
}

.quick-action small {
  display: block;
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.action-badge,
.action-arrow,
.card-arrow {
  flex: 0 0 auto;
  display: grid;
  place-items: center;
}

.action-badge {
  min-width: 32px;
  height: 32px;
  padding: 0 8px;
  border-radius: 999px;
  background: #f44336;
  color: #fff;
  font-weight: 800;
}

.action-arrow {
  width: 32px;
  height: 32px;
  border-radius: 12px;
  background: var(--completed-bg);
  color: var(--heading-color);
  font-size: 0;
  font-weight: 900;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-arrow::before {
  content: '';
  width: 8px;
  height: 8px;
  border-top: 2px solid currentColor;
  border-right: 2px solid currentColor;
  transform: rotate(45deg);
  transform-origin: center;
  margin-right: 3px;
}

.card-arrow::before {
  content: '';
  width: 9px;
  height: 9px;
  border-top: 2px solid currentColor;
  border-right: 2px solid currentColor;
  transform: rotate(45deg);
  transform-origin: center;
  margin-right: 3px;
}

.menu-grid {
  grid-area: cards;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 20px;
}

.menu-card {
  height: 260px;
  min-width: 0;
  padding: 24px 22px;
  border: 1px solid var(--border-color);
  border-radius: 18px;
  background: var(--bg-card);
  color: var(--text-primary);
  box-shadow: var(--shadow);
  cursor: pointer;
  text-align: left;
  display: flex;
  align-items: flex-end;
  position: relative;
  overflow: hidden;
  transition: border-color 0.2s ease;
}

.menu-card:hover {
  border-color: var(--accent-color);
}

.menu-card.admin-card {
  border-color: var(--danger-color);
  background: color-mix(in srgb, var(--danger-color) 8%, var(--bg-card));
}

.menu-card.admin-card::before {
  background: color-mix(in srgb, var(--danger-color) 18%, transparent);
  border-color: color-mix(in srgb, var(--danger-color) 26%, transparent);
}

.menu-card.admin-card:hover {
  border-color: var(--danger-color);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--danger-color) 30%, transparent), var(--shadow-strong);
}

.menu-card.admin-card .card-arrow {
  background: var(--danger-color);
}

.menu-card.admin-card .card-visual {
  background: color-mix(in srgb, var(--danger-color) 15%, var(--completed-bg));
}

:global(.dark-theme) .menu-card.admin-card::before {
  background: color-mix(in srgb, var(--danger-color) 20%, transparent);
  border-color: color-mix(in srgb, var(--danger-color) 30%, transparent);
}

.menu-card::before {
  content: '';
  position: absolute;
  top: -30px;
  right: -28px;
  width: 116px;
  height: 116px;
  border-radius: 28px;
  background: color-mix(in srgb, var(--accent-color) 18%, transparent);
  border: 1px solid color-mix(in srgb, var(--accent-color) 26%, transparent);
  transform: rotate(18deg);
  opacity: 0.78;
  pointer-events: none;
}

:global(.dark-theme) .menu-card::before {
  background: color-mix(in srgb, var(--accent-color) 20%, transparent);
  border-color: color-mix(in srgb, var(--accent-color) 30%, transparent);
}

.card-visual {
  position: absolute;
  top: 22px;
  left: 22px;
  width: 94px;
  height: 92px;
  border-radius: 18px;
  background: var(--completed-bg);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}

.card-visual img {
  width: 70px;
  height: 70px;
  max-width: 70px;
  max-height: 70px;
  display: block;
  object-fit: contain;
}

.card-info {
  min-width: 0;
  width: 100%;
  padding-right: 54px;
  padding-top: 112px;
}

.card-info strong {
  display: block;
  margin-bottom: 6px;
  color: var(--heading-color);
  font-size: 22px;
  line-height: 1.1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-info small {
  display: block;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.25;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-arrow {
  right: 18px;
  bottom: 18px;
  width: 38px;
  height: 38px;
  border-radius: 14px;
  background: var(--heading-color);
  color: #fff;
  font-size: 0;
  font-weight: 900;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

:global(.dark-theme) .card-arrow {
  background: var(--accent-color);
}

.logout-button {
  cursor: pointer;
  position: fixed;
  right: 31px;
  bottom: 28px;
  display: inline-block;
  width: clamp(50px, 8vw, 60px);
  height: clamp(50px, 8vw, 60px);
  border-radius: 16px;
  overflow: hidden;
  background: transparent;
  border: none;
  padding: 0;
  flex-shrink: 0;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
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
  border-radius: 16px;
}

.logout-button::after {
  box-shadow: inset 0 0 0 1px var(--danger-color);
}

.logout-button::before {
  background: var(--danger-color);
  box-shadow: inset 0 0 0 60px var(--bg-card);
}

.logout-button:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 20px rgba(244, 67, 54, 0.3);
}

.logout-button:hover::before {
  box-shadow: inset 0 0 0 1px var(--bg-card);
}

.logout-button i {
  position: absolute;
  color: var(--danger-color);
  font-size: clamp(24px, 5vw, 30px);
  line-height: 1;
  transition: all 0.25s ease;
  z-index: 1;
  display: inline-block;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.logout-button:hover i {
  color: white;
}

.logout-button:active {
  transform: scale(0.95);
}

@media (max-width: 1280px) {
  .menu-content {
    grid-template-columns: 1fr;
    grid-template-areas:
      "intro"
      "quick"
      "cards";
  }

  .quick-actions {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .menu-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>