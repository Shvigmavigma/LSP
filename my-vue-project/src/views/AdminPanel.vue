<template>
  <div class="admin-panel">
    <header class="page-header">
      <div>
        <p class="page-eyebrow">{{ $t('adminPanel.workspace') }}</p>
        <h1>{{ $t('adminPanel.title') }}</h1>
      </div>
      <div class="header-actions">
        <ThemeToggle />
        <LanguageSwitcher />
        <HomeButton />
      </div>
    </header>

    <main class="admin-menu">
      <section
        v-for="section in sections"
        :key="section.key"
        class="admin-section"
        :class="[`section-${section.tone}`, { open: openSections.includes(section.key) }]"
      >
        <button class="section-toggle" type="button" @click="toggleSection(section.key)">
          <span class="section-number">{{ section.number }}</span>
          <span class="section-heading">
            <strong>{{ $t(section.titleKey) }}</strong>
            <small>{{ $t(section.descriptionKey) }}</small>
          </span>
          <span class="section-count">{{ section.items.length }}</span>
          <span class="section-chevron" aria-hidden="true"></span>
        </button>

        <Transition name="section-content">
          <div v-if="openSections.includes(section.key)" class="section-content">
            <div class="menu-grid">
              <router-link
                v-for="item in section.items"
                :key="item.route"
                :to="item.route"
                class="menu-card"
                :class="{ 'notification-card': item.notification }"
              >
                <span
                  v-if="item.notification && pendingProfileRequests > 0"
                  class="notification-dot"
                  :title="String(pendingProfileRequests)"
                >
                  {{ pendingProfileRequests > 99 ? '99+' : pendingProfileRequests }}
                </span>
                <span class="card-marker"></span>
                <span class="card-copy">
                  <strong class="card-title">{{ $t(item.titleKey) }}</strong>
                  <small class="card-desc">{{ $t(item.descriptionKey) }}</small>
                </span>
                <span class="card-arrow" aria-hidden="true"></span>
              </router-link>
            </div>
          </div>
        </Transition>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import ThemeToggle from '@/components/ThemeToggle.vue';
import HomeButton from '@/components/HomeButton.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';
import api from '@/utils/api';

type SectionKey = 'access' | 'projects' | 'creation';

type AdminItem = {
  route: string;
  titleKey: string;
  descriptionKey: string;
  notification?: boolean;
};

type AdminSection = {
  key: SectionKey;
  number: string;
  tone: 'green' | 'blue' | 'orange';
  titleKey: string;
  descriptionKey: string;
  items: AdminItem[];
};

const pendingProfileRequests = ref(0);
const openSections = ref<SectionKey[]>([]);

const sections: AdminSection[] = [
  {
    key: 'access',
    number: '01',
    tone: 'green',
    titleKey: 'adminPanel.sections.access.title',
    descriptionKey: 'adminPanel.sections.access.desc',
    items: [
      {
        route: '/admin/users',
        titleKey: 'adminPanel.userManagement.title',
        descriptionKey: 'adminPanel.userManagement.desc',
      },
      {
        route: '/admin/emails',
        titleKey: 'adminPanel.allowedEmails.title',
        descriptionKey: 'adminPanel.allowedEmails.desc',
      },
      {
        route: '/admin/account-classes',
        titleKey: 'adminPanel.accountClasses.title',
        descriptionKey: 'adminPanel.accountClasses.desc',
      },
      {
        route: '/admin/user-directions',
        titleKey: 'adminDirections.title',
        descriptionKey: 'adminDirections.desc',
      },
      {
        route: '/admin/profile-change-requests',
        titleKey: 'adminPanel.profileRequests.title',
        descriptionKey: 'adminPanel.profileRequests.desc',
        notification: true,
      },
    ],
  },
  {
    key: 'projects',
    number: '02',
    tone: 'blue',
    titleKey: 'adminPanel.sections.projects.title',
    descriptionKey: 'adminPanel.sections.projects.desc',
    items: [
      {
        route: '/admin/projects',
        titleKey: 'adminPanel.projectManagement.title',
        descriptionKey: 'adminPanel.projectManagement.desc',
      },
      {
        route: '/admin/default-tasks',
        titleKey: 'adminPanel.defaultTasks.title',
        descriptionKey: 'adminPanel.defaultTasks.desc',
      },
      {
        route: '/admin/project-lifecycle',
        titleKey: 'adminPanel.projectLifecycle.title',
        descriptionKey: 'adminPanel.projectLifecycle.desc',
      },
      {
        route: '/admin/file-limits',
        titleKey: 'adminPanel.fileLimits.title',
        descriptionKey: 'adminPanel.fileLimits.desc',
      },
      {
        route: '/admin/quota-limits',
        titleKey: 'adminPanel.quotaLimits.title',
        descriptionKey: 'adminPanel.quotaLimits.desc',
      },
    ],
  },
  {
    key: 'creation',
    number: '03',
    tone: 'orange',
    titleKey: 'adminPanel.sections.creation.title',
    descriptionKey: 'adminPanel.sections.creation.desc',
    items: [
      {
        route: '/admin/create-users',
        titleKey: 'adminPanel.createUsers.title',
        descriptionKey: 'adminPanel.createUsers.desc',
      },
      {
        route: '/admin/create-admin',
        titleKey: 'adminPanel.createAdmin.title',
        descriptionKey: 'adminPanel.createAdmin.desc',
      },
      {
        route: '/admin/create-project',
        titleKey: 'adminPanel.createProject.title',
        descriptionKey: 'adminPanel.createProject.desc',
      },
    ],
  },
];

const toggleSection = (key: SectionKey) => {
  const index = openSections.value.indexOf(key);
  if (index === -1) {
    openSections.value.push(key);
  } else {
    openSections.value.splice(index, 1);
  }
};

onMounted(async () => {
  // Все секции закрыты по умолчанию
  openSections.value = [];
  
  try {
    const response = await api.get('/admin/profile-change-requests', { params: { status: 'pending' } });
    pendingProfileRequests.value = response.data.length;
  } catch (error) {
    console.error('Failed to load pending profile requests', error);
  }
});
</script>

<style scoped>
.admin-panel {
  min-height: 100vh;
  padding: 30px 34px 70px;
  background: var(--bg-page);
  color: var(--text-primary);
}

.page-header {
  max-width: 1320px;
  margin: 0 auto 26px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  position: relative;
  z-index: 1000000;
}

.page-eyebrow {
  margin: 0 0 5px;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.page-header h1 {
  margin: 0;
  color: var(--heading-color);
  font-size: 38px;
  line-height: 1.05;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
  z-index: 1000001;
}

.admin-menu {
  max-width: 1320px;
  margin: 0 auto;
  display: grid;
  gap: 16px;
}

.admin-section {
  --section-color: var(--accent-color);
  --section-soft: color-mix(in srgb, var(--section-color) 12%, var(--bg-card));
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--section-color) 24%, var(--border-color));
  border-radius: 18px;
  background: var(--bg-card);
  box-shadow: var(--shadow);
}

.section-green {
  --section-color: #2f9e67;
}

.section-blue {
  --section-color: #3279d8;
}

.section-orange {
  --section-color: #db7c27;
}

.section-toggle {
  width: 100%;
  min-height: 94px;
  padding: 18px 22px;
  border: none;
  background: var(--section-soft);
  color: var(--text-primary);
  cursor: pointer;
  display: grid;
  grid-template-columns: 54px minmax(0, 1fr) auto 34px;
  align-items: center;
  gap: 16px;
  text-align: left;
  transition: background 0.2s ease;
}

.section-toggle:hover {
  background: color-mix(in srgb, var(--section-color) 18%, var(--bg-card));
}

.section-number {
  width: 46px;
  height: 46px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  background: var(--section-color);
  color: white;
  font-size: 14px;
  font-weight: 800;
}

.section-heading {
  min-width: 0;
}

.section-heading strong,
.section-heading small {
  display: block;
}

.section-heading strong {
  margin-bottom: 5px;
  color: var(--text-primary);
  font-size: 20px;
}

.section-heading small {
  color: var(--text-secondary);
  font-size: 14px;
}

.section-count {
  min-width: 32px;
  height: 28px;
  padding: 0 9px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--section-color) 15%, transparent);
  color: var(--section-color);
  font-size: 13px;
  font-weight: 800;
}

.section-chevron {
  width: 12px;
  height: 12px;
  border-right: 2px solid var(--section-color);
  border-bottom: 2px solid var(--section-color);
  transform: rotate(45deg) translate(-2px, -2px);
  transition: transform 0.3s ease;
}

.admin-section.open .section-chevron {
  transform: rotate(225deg) translate(-2px, -2px);
}

.section-content {
  padding: 18px;
  border-top: 1px solid color-mix(in srgb, var(--section-color) 18%, var(--border-color));
}

.menu-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.menu-card {
  min-height: 132px;
  padding: 18px 50px 18px 18px;
  border: 1px solid var(--border-color);
  border-radius: 14px;
  background: var(--bg-card);
  color: inherit;
  text-decoration: none;
  position: relative;
  display: flex;
  align-items: center;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.15s ease;
}

.menu-card:hover {
  border-color: var(--section-color);
  box-shadow: 0 8px 24px color-mix(in srgb, var(--section-color) 12%, transparent);
  transform: translateY(-2px);
}

.card-marker {
  position: absolute;
  top: 0;
  left: 0;
  width: 5px;
  height: 100%;
  background: var(--section-color);
  border-radius: 14px 0 0 14px;
}

.card-copy {
  min-width: 0;
}

.card-title,
.card-desc {
  display: block;
}

.card-title {
  margin-bottom: 7px;
  color: var(--heading-color);
  font-size: 17px;
  line-height: 1.2;
}

.card-desc {
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.35;
}

.card-arrow {
  position: absolute;
  right: 18px;
  top: 50%;
  width: 9px;
  height: 9px;
  border-top: 2px solid var(--section-color);
  border-right: 2px solid var(--section-color);
  transform: translateY(-50%) rotate(45deg);
  transition: right 0.2s ease;
}

.menu-card:hover .card-arrow {
  right: 14px;
}

.notification-dot {
  position: absolute;
  top: 10px;
  right: 10px;
  min-width: 24px;
  height: 24px;
  padding: 0 6px;
  border-radius: 999px;
  background: var(--danger-color);
  color: white;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 800;
  z-index: 1;
}

.notification-card .card-arrow {
  top: auto;
  bottom: 18px;
  transform: rotate(45deg);
}

/* Плавная анимация для открытия и закрытия */
.section-content-enter-active,
.section-content-leave-active {
  transition: all 0.25s ease;
  overflow: hidden;
}

.section-content-enter-from,
.section-content-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.section-content-enter-to,
.section-content-leave-from {
  opacity: 1;
  transform: translateY(0);
}

@media (max-width: 1050px) {
  .menu-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 700px) {
  .admin-panel {
    padding: 20px 16px 40px;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .page-header h1 {
    font-size: 28px;
  }
  
  .menu-grid {
    grid-template-columns: 1fr;
  }
  
  .section-toggle {
    grid-template-columns: 40px minmax(0, 1fr) auto 30px;
    gap: 12px;
    padding: 14px 16px;
    min-height: 76px;
  }
  
  .section-number {
    width: 36px;
    height: 36px;
    font-size: 12px;
  }
  
  .section-heading strong {
    font-size: 17px;
  }
  
  .section-heading small {
    font-size: 13px;
  }
}
</style>