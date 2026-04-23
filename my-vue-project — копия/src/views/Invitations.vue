<template>
  <div class="invitations-page">
    <header class="page-header">
      <h1>{{ $t('invitations.title') }}</h1>
      <div class="header-actions">
        <ThemeToggle />
        <LanguageSwitcher />
        <HomeButton/>
      </div>
    </header>

    <!-- Полученные приглашения -->
    <div class="invites-list">
      <div v-if="loading" class="loading">{{ $t('common.loading') }}</div>
      <div v-else-if="invitations.length === 0" class="empty">
        <div class="empty-icon">📭</div>
        <p>{{ $t('invitations.noReceived') }}</p>
      </div>
      <TransitionGroup name="fade" tag="div" class="invites-grid">
        <div v-for="inv in invitations" :key="inv.id" class="invite-card">
          <div class="card-header">
            <span class="project-title">{{ inv.project_title }}</span>
            <span class="badge pending">{{ $t('invitations.statusPending') }}</span>
          </div>
          <div class="card-body">
            <div class="info-row">
              <span class="info-label">{{ $t('invitations.from') }}:</span>
              <span class="info-value">{{ inv.invited_by_nickname }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">{{ $t('invitations.role') }}:</span>
              <span class="info-value role-badge">{{ getRoleDisplay(inv.role) }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">{{ $t('invitations.date') }}:</span>
              <span class="info-value">{{ formatDate(inv.created_at) }}</span>
            </div>
          </div>
          <div class="card-actions">
            <button class="accept-btn" @click="acceptInvite(inv.id)">
              <span>✅</span> {{ $t('common.accept') }}
            </button>
            <button class="reject-btn" @click="rejectInvite(inv.id)">
              <span>❌</span> {{ $t('common.reject') }}
            </button>
          </div>
        </div>
      </TransitionGroup>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '@/stores/auth';
import { useUsersStore } from '@/stores/users';
import HomeButton from '@/components/HomeButton.vue';
import { useProjectsStore } from '@/stores/projects';
import ThemeToggle from '@/components/ThemeToggle.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';
import axios from 'axios';
import type { User, ProjectRole } from '@/types';

const { t } = useI18n();
const router = useRouter();
const authStore = useAuthStore();
const usersStore = useUsersStore();
const projectsStore = useProjectsStore();

const loading = ref(true);
const invitations = ref<any[]>([]);

function getRoleDisplay(role: string) {
  return t(`roles.${role}`);
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString();
}

async function loadInvitations() {
  loading.value = true;
  try {
    const res = await axios.get('/invitations');
    invitations.value = res.data;
  } catch (err) {
    console.error(err);
  } finally {
    loading.value = false;
  }
}

async function acceptInvite(id: number) {
  try {
    await axios.put(`/invitations/${id}/accept`);
    await loadInvitations();
    await projectsStore.fetchUserProjects();
  } catch (err) {
    console.error(err);
    alert(t('invitations.acceptError'));
  }
}

async function rejectInvite(id: number) {
  try {
    await axios.put(`/invitations/${id}/reject`);
    await loadInvitations();
  } catch (err) {
    console.error(err);
    alert(t('invitations.rejectError'));
  }
}

onMounted(async () => {
  await usersStore.fetchAllUsers();
  await loadInvitations();
});

function goHome() {
  router.push('/main');
}
</script>

<style scoped>
/* Стили остаются те же, что и в предыдущей версии, но без вкладок и лишних элементов */
.invitations-page {
  min-height: 100vh;
  background: var(--bg-page);
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1000px;
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



.invites-list {
  max-width: 1000px;
  margin: 0 auto;
}

.invites-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
}

.invite-card {
  background: var(--bg-card);
  border-radius: 20px;
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: var(--shadow);
  border: 1px solid var(--border-color);
}

.invite-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-strong);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: rgba(66, 185, 131, 0.05);
  border-bottom: 1px solid var(--border-color);
}

.project-title {
  font-weight: 600;
  font-size: 1.1rem;
  color: var(--heading-color);
}

.badge {
  padding: 4px 12px;
  border-radius: 30px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.badge.pending {
  background: #ff9800;
  color: white;
}

.card-body {
  padding: 16px 20px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  font-size: 0.9rem;
}

.info-label {
  color: var(--text-secondary);
  font-weight: 500;
}

.info-value {
  color: var(--text-primary);
}

.role-badge {
  background: var(--accent-color);
  color: white;
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 0.8rem;
}

.card-actions {
  padding: 12px 20px 20px;
  display: flex;
  gap: 12px;
  border-top: 1px solid var(--border-color);
}

.accept-btn, .reject-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 0;
  border: none;
  border-radius: 40px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.accept-btn {
  background: #4caf50;
  color: white;
}
.accept-btn:hover {
  background: #45a049;
  transform: scale(1.02);
}

.reject-btn {
  background: #f44336;
  color: white;
}
.reject-btn:hover {
  background: #d32f2f;
  transform: scale(1.02);
}

.empty {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 16px;
  opacity: 0.6;
}

.loading {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

@media (max-width: 768px) {
  .invites-grid {
    grid-template-columns: 1fr;
  }
}
</style>