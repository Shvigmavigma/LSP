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

        <div class="menu-card danger" @click="confirmDeleteAllUsers">
          <span class="card-title">{{ $t('adminPanel.deleteAllUsers.title') }}</span>
          <span class="card-desc">{{ $t('adminPanel.deleteAllUsers.desc') }}</span>
        </div>

        <div class="menu-card danger" @click="confirmDeleteAllProjects">
          <span class="card-title">{{ $t('adminPanel.deleteAllProjects.title') }}</span>
          <span class="card-desc">{{ $t('adminPanel.deleteAllProjects.desc') }}</span>
        </div>
      </div>
    </div>

    <!-- Модальное подтверждение -->
    <Teleport to="body">
      <div v-if="showConfirmModal" class="modal-overlay" @click.self="closeModal">
        <div class="modal-content">
          <h3>{{ confirmTitle }}</h3>
          <p>{{ confirmMessage }}</p>
          <div class="modal-actions">
            <button class="confirm-btn" @click="executeAction">{{ $t('common.confirm') }}</button>
            <button class="cancel-btn" @click="closeModal">{{ $t('common.cancel') }}</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import ThemeToggle from '@/components/ThemeToggle.vue';
import axios from 'axios';
import HomeButton from '@/components/HomeButton.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';

const { t } = useI18n();
const router = useRouter();

const showConfirmModal = ref(false);
const confirmTitle = ref('');
const confirmMessage = ref('');
let action: 'deleteUsers' | 'deleteProjects' | null = null;

function goHome() {
  router.push('/main');
}

function confirmDeleteAllUsers() {
  confirmTitle.value = t('adminPanel.deleteAllUsers.confirmTitle');
  confirmMessage.value = t('adminPanel.deleteAllUsers.confirmMessage');
  action = 'deleteUsers';
  showConfirmModal.value = true;
}

function confirmDeleteAllProjects() {
  confirmTitle.value = t('adminPanel.deleteAllProjects.confirmTitle');
  confirmMessage.value = t('adminPanel.deleteAllProjects.confirmMessage');
  action = 'deleteProjects';
  showConfirmModal.value = true;
}

function closeModal() {
  showConfirmModal.value = false;
  action = null;
}

async function executeAction() {
  if (action === 'deleteUsers') {
    try {
      await axios.delete('/admin/users/all');
      alert(t('adminPanel.deleteAllUsers.success'));
    } catch (error) {
      console.error(error);
      alert(t('adminPanel.deleteAllUsers.error'));
    }
  } else if (action === 'deleteProjects') {
    try {
      await axios.delete('/admin/projects/all');
      alert(t('adminPanel.deleteAllProjects.success'));
    } catch (error) {
      console.error(error);
      alert(t('adminPanel.deleteAllProjects.error'));
    }
  }
  closeModal();
}
</script>

<style scoped>
/* стили без изменений */
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
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}
.modal-content {
  background: var(--modal-bg);
  border-radius: 24px;
  padding: 30px;
  max-width: 400px;
  width: 90%;
  box-shadow: var(--shadow-strong);
}
.modal-content h3 {
  color: var(--heading-color);
  margin-bottom: 10px;
}
.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}
.confirm-btn {
  background: var(--danger-color);
  color: white;
  border: none;
  border-radius: 30px;
  padding: 10px 20px;
  cursor: pointer;
}
.cancel-btn {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  border-radius: 30px;
  padding: 10px 20px;
  cursor: pointer;
}
</style>