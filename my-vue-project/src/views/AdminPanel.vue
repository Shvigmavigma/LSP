<template>
  <div class="admin-panel">
    <header class="page-header">
      <h1>{{ $t('adminPanel.title') }}</h1>
      <div class="header-actions">
        <ThemeToggle />
        <LanguageSwitcher />
        <HomeButton/>
      </div>
    </header>

    <div class="admin-menu">
      <div class="menu-grid">
        <router-link to="/admin/users" class="menu-card">
          <span class="card-title">{{ $t('adminPanel.userManagement.title') }}</span>
          <span class="card-desc">{{ $t('adminPanel.userManagement.desc') }}</span>
        </router-link>

        <router-link to="/admin/projects" class="menu-card">
          <span class="card-title">{{ $t('adminPanel.projectManagement.title') }}</span>
          <span class="card-desc">{{ $t('adminPanel.projectManagement.desc') }}</span>
        </router-link>

        <router-link to="/admin/emails" class="menu-card">
          <span class="card-title">{{ $t('adminPanel.allowedEmails.title') }}</span>
          <span class="card-desc">{{ $t('adminPanel.allowedEmails.desc') }}</span>
        </router-link>

        <router-link to="/admin/default-tasks" class="menu-card">
          <span class="card-title"> {{ $t('adminPanel.defaultTasks.title') }}</span>
          <span class="card-desc">{{ $t('adminPanel.defaultTasks.desc') }}</span>
        </router-link>

        <router-link to="/admin/project-lifecycle" class="menu-card">
          <span class="card-title">{{ $t('adminPanel.projectLifecycle.title') }}</span>
          <span class="card-desc">{{ $t('adminPanel.projectLifecycle.desc') }}</span>
        </router-link>

        <!-- Лимиты файлов -->
        <router-link to="/admin/file-limits" class="menu-card">
          <span class="card-title">{{ $t('adminPanel.fileLimits.title') }}</span>
          <span class="card-desc">{{ $t('adminPanel.fileLimits.desc') }}</span>
        </router-link>

        <!-- Квоты -->
        <router-link to="/admin/quota-limits" class="menu-card">
          <span class="card-title">{{ $t('adminPanel.quotaLimits.title') }}</span>
          <span class="card-desc">{{ $t('adminPanel.quotaLimits.desc') }}</span>
        </router-link>

        <!-- НОВАЯ КАРТОЧКА: Создание пользователей админом -->
        <router-link to="/admin/create-users" class="menu-card">
          <span class="card-title">{{ $t('adminPanel.createUsers.title') }}</span>
          <span class="card-desc">{{ $t('adminPanel.createUsers.desc') }}</span>
        </router-link>

        <!-- НОВАЯ КАРТОЧКА: Создание проекта админом -->
        <router-link to="/admin/create-project" class="menu-card">
          <span class="card-title">{{ $t('adminPanel.createProject.title') }}</span>
          <span class="card-desc">{{ $t('adminPanel.createProject.desc') }}</span>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import ThemeToggle from '@/components/ThemeToggle.vue';
import HomeButton from '@/components/HomeButton.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';
</script>

<style scoped>
.admin-panel {
  min-height: 100vh;
  background: var(--bg-page);
  padding: 20px;
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
  font-size: 2rem;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.admin-menu {
  max-width: 1200px;
  margin: 0 auto;
}

.menu-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.menu-card {
  background: var(--bg-card);
  border-radius: 16px;
  padding: 20px;
  box-shadow: var(--shadow);
  transition: all 0.2s;
  cursor: pointer;
  text-decoration: none;
  color: inherit;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border-color);
}

.menu-card:hover {
  outline: 2px solid var(--accent-color);
  outline-offset: 2px;
  transform: translateY(-2px);
}

.menu-card.danger {
  border-color: var(--danger-color);
}

.menu-card.danger:hover {
  outline: 2px solid var(--danger-color);
  outline-offset: 2px;
}

.menu-card.danger .card-icon {
  color: var(--danger-color);
}

.card-icon {
  font-size: 2.5rem;
  margin-bottom: 10px;
}

.card-title {
  font-size: 1.3rem;
  font-weight: 600;
  color: var(--heading-color);
  margin-bottom: 5px;
}

.card-desc {
  color: var(--text-secondary);
  font-size: 0.9rem;
}
</style>