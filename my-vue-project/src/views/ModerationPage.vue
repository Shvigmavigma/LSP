<template>
  <div class="moderation-page">
    <!-- Заголовок -->
    <header class="page-header">
      <h1 class="page-title">🛡️ {{ $t('moderation.title') }}</h1>
      <div class="header-actions">
        <ThemeToggle />
        <LanguageSwitcher />
        <HomeButton />
      </div>
    </header>

    <!-- Загрузка -->
    <div v-if="loading" class="state-container">
      <div class="spinner"></div>
      <p>{{ $t('common.loading') }}</p>
    </div>

    <!-- Ошибка -->
    <div v-else-if="error" class="state-container error">
      <p>❌ {{ error }}</p>
      <button class="btn btn-primary" @click="loadRequests">{{ $t('common.retry') }}</button>
    </div>

    <!-- Основной контент -->
    <div v-else class="content">
      <!-- Табы -->
      <div class="tabs">
        <button 
          v-for="tab in tabs" 
          :key="tab.key" 
          :class="['tab', { active: activeTab === tab.key }]"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
          <span v-if="tab.count > 0" class="badge">{{ tab.count }}</span>
        </button>
      </div>

      <!-- Список заявок -->
      <div class="requests">
        <!-- Pending -->
        <template v-if="activeTab === 'pending'">
          <div v-if="pending.length === 0" class="empty">
            📋 {{ $t('moderation.noPending') }}
          </div>
          <div v-for="req in pending" :key="req.project_id" class="card pending">
            <div class="card-header">
              <h3>{{ req.project_title }}</h3>
              <div class="status-group">
                <span v-if="req.is_old" class="old-project-badge">{{ $t('projectDetails.oldProject') }}</span>
                <span class="status pending">{{ $t('moderation.pendingStatus') }}</span>
              </div>
            </div>
            <div class="card-body">
              <div class="info-row">
                <span class="label">{{ $t('moderation.requestedBy') }}:</span>
                <span class="value">{{ req.requested_by_name || '—' }}</span>
              </div>
              <div class="info-row" v-if="req.customer_name">
                <span class="label">{{ $t('moderation.customer') }}:</span>
                <span class="value">{{ req.customer_name }}</span>
              </div>
              <div class="info-row" v-if="req.requested_at">
                <span class="label">{{ $t('moderation.requestedAt') }}:</span>
                <span class="value">{{ formatDate(req.requested_at) }}</span>
              </div>
            </div>
            <div class="card-actions">
              <button class="btn btn-outline" @click="viewProject(req.project_id)">
                👁️ {{ $t('moderation.view') }}
              </button>
              <button class="btn btn-success" @click="handleApprove(req.project_id)">
                ✅ {{ $t('moderation.approve') }}
              </button>
              <button class="btn btn-danger" @click="openReject(req)">
                ❌ {{ $t('moderation.reject') }}
              </button>
            </div>
          </div>
        </template>

        <!-- Approved -->
        <template v-if="activeTab === 'approved'">
          <div v-if="approved.length === 0" class="empty">
            ✅ {{ $t('moderation.noApproved') }}
          </div>
          <div v-for="req in approved" :key="req.project_id" class="card approved">
            <div class="card-header">
              <h3>{{ req.project_title }}</h3>
              <div class="status-group">
                <span v-if="req.is_old" class="old-project-badge">{{ $t('projectDetails.oldProject') }}</span>
                <span class="status approved">{{ $t('moderation.approvedStatus') }}</span>
              </div>
            </div>
            <div class="card-body">
              <div class="info-row">
                <span class="label">{{ $t('moderation.requestedBy') }}:</span>
                <span class="value">{{ req.requested_by_name || '—' }}</span>
              </div>
              <div class="info-row" v-if="req.customer_name">
                <span class="label">{{ $t('moderation.customer') }}:</span>
                <span class="value">{{ req.customer_name }}</span>
              </div>
            </div>
            <div class="card-actions">
              <button class="btn btn-outline" @click="viewProject(req.project_id)">
                👁️ {{ $t('moderation.view') }}
              </button>
            </div>
          </div>
        </template>

        <!-- Rejected -->
        <template v-if="activeTab === 'rejected'">
          <div v-if="rejected.length === 0" class="empty">
            ❌ {{ $t('moderation.noRejected') }}
          </div>
          <div v-for="req in rejected" :key="req.project_id" class="card rejected">
            <div class="card-header">
              <h3>{{ req.project_title }}</h3>
              <div class="status-group">
                <span v-if="req.is_old" class="old-project-badge">{{ $t('projectDetails.oldProject') }}</span>
                <span class="status rejected">{{ $t('moderation.rejectedStatus') }}</span>
              </div>
            </div>
            <div class="card-body">
              <div class="info-row">
                <span class="label">{{ $t('moderation.requestedBy') }}:</span>
                <span class="value">{{ req.requested_by_name || '—' }}</span>
              </div>
              <div class="info-row" v-if="req.customer_name">
                <span class="label">{{ $t('moderation.customer') }}:</span>
                <span class="value">{{ req.customer_name }}</span>
              </div>
            </div>
            <div class="card-actions">
              <button class="btn btn-outline" @click="viewProject(req.project_id)">
                👁️ {{ $t('moderation.view') }}
              </button>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- Модальное окно отклонения -->
    <Teleport to="body">
      <div v-if="showRejectModal" class="modal-overlay" @click.self="showRejectModal = false">
        <div class="modal">
          <h2>{{ $t('moderation.rejectTitle') }}</h2>
          <p class="modal-project">{{ selectedRequest?.project_title }}</p>
          <textarea
            v-model="rejectComment"
            :placeholder="$t('moderation.rejectPlaceholder')"
            rows="3"
            class="modal-textarea"
          ></textarea>
          <div class="modal-actions">
            <button class="btn btn-outline" @click="showRejectModal = false">
              {{ $t('common.cancel') }}
            </button>
            <button class="btn btn-danger" @click="confirmReject">
              {{ $t('moderation.reject') }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '@/stores/auth';
import ThemeToggle from '@/components/ThemeToggle.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';
import HomeButton from '@/components/HomeButton.vue';
import api from '@/utils/api';
import type { ApprovalRequestItem } from '@/types';

const { t } = useI18n();
const router = useRouter();
const authStore = useAuthStore();

// Проверка доступа
if (!authStore.user?.is_admin && !authStore.user?.teacher_info?.curator) {
  router.push('/main');
}

// Состояние
const loading = ref(true);
const error = ref('');
const activeTab = ref('pending');
const showRejectModal = ref(false);
const rejectComment = ref('');
const selectedRequest = ref<ApprovalRequestItem | null>(null);

const pending = ref<ApprovalRequestItem[]>([]);
const approved = ref<ApprovalRequestItem[]>([]);
const rejected = ref<ApprovalRequestItem[]>([]);

const tabs = computed(() => [
  { key: 'pending', label: `🕐 ${t('moderation.pendingTab')}`, count: pending.value.length },
  { key: 'approved', label: `✅ ${t('moderation.approvedTab')}`, count: approved.value.length },
  { key: 'rejected', label: `❌ ${t('moderation.rejectedTab')}`, count: rejected.value.length },
]);

const formatDate = (dateStr: string | null) => {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleString();
};

// Загрузка данных
const loadRequests = async () => {
  loading.value = true;
  error.value = '';
  try {
    const { data } = await api.get('/admin/approval-requests');
    pending.value = data.pending || [];
    approved.value = data.approved || [];
    rejected.value = data.rejected || [];
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Ошибка загрузки';
    console.error('Load error:', err);
  } finally {
    loading.value = false;
  }
};

// Просмотр проекта
const viewProject = (id: number) => {
  router.push(`/project/${id}`);
};

// Одобрение
const handleApprove = async (id: number) => {
  try {
    await api.post(`/projects/${id}/approve`, {
      action: 'approve',
      comment: null
    });
    await loadRequests();
  } catch (err: any) {
    alert(err.response?.data?.detail || 'Ошибка одобрения');
  }
};

// Отклонение
const openReject = (req: ApprovalRequestItem) => {
  selectedRequest.value = req;
  rejectComment.value = '';
  showRejectModal.value = true;
};

const confirmReject = async () => {
  if (!selectedRequest.value) return;
  try {
    await api.post(`/projects/${selectedRequest.value.project_id}/approve`, {
      action: 'reject',
      comment: rejectComment.value || null
    });
    showRejectModal.value = false;
    await loadRequests();
  } catch (err: any) {
    alert(err.response?.data?.detail || 'Ошибка отклонения');
  }
};

onMounted(() => {
  loadRequests();
});
</script>

<style scoped>
.moderation-page {
  min-height: 100vh;
  background: var(--bg-page);
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto 32px;
  gap: 16px;
}

.page-title {
  color: var(--heading-color);
  font-size: 2rem;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.content {
  max-width: 1200px;
  margin: 0 auto;
}

/* Табы */
.tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 24px;
  background: var(--bg-card);
  border-radius: 16px;
  padding: 4px;
}

.tab {
  flex: 1;
  padding: 12px 20px;
  border: none;
  background: transparent;
  color: var(--text-primary);
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  border-radius: 12px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.tab:hover {
  background: var(--bg-hover);
}

.tab.active {
  background: var(--accent-color);
  color: white;
}

.badge {
  background: rgba(255,255,255,0.3);
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
}

/* Карточки */
.requests {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.card {
  background: var(--bg-card);
  border-radius: 16px;
  padding: 24px;
  border-left: 4px solid var(--accent-color);
  box-shadow: var(--shadow);
}

.card.pending { border-left-color: #ff9800; }
.card.approved { border-left-color: #4caf50; }
.card.rejected { border-left-color: #f44336; }

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-header h3 {
  margin: 0;
  color: var(--heading-color);
  font-size: 1.2rem;
}

.status {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
}

.status-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.old-project-badge {
  padding: 4px 12px;
  border-radius: 20px;
  background: rgba(255, 152, 0, 0.14);
  color: #ff9800;
  border: 1px solid rgba(255, 152, 0, 0.35);
  font-size: 0.85rem;
  font-weight: 700;
}

.status.pending { background: rgba(255,152,0,0.1); color: #ff9800; }
.status.approved { background: rgba(76,175,80,0.1); color: #4caf50; }
.status.rejected { background: rgba(244,67,54,0.1); color: #f44336; }

.card-body {
  margin-bottom: 16px;
}

.info-row {
  display: flex;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 0.95rem;
}

.label {
  color: var(--text-secondary);
  min-width: 100px;
}

.value {
  color: var(--text-primary);
  font-weight: 500;
}

.card-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* Кнопки */
.btn {
  padding: 8px 18px;
  border: none;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-primary {
  background: var(--accent-color);
  color: white;
}

.btn-outline {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-primary);
}

.btn-outline:hover {
  background: var(--bg-hover);
}

.btn-success {
  background: #4caf50;
  color: white;
}

.btn-success:hover {
  background: #43a047;
}

.btn-danger {
  background: #f44336;
  color: white;
}

.btn-danger:hover {
  background: #e53935;
}

/* Состояния */
.state-container {
  text-align: center;
  padding: 80px 20px;
  color: var(--text-primary);
}

.state-container.error {
  color: #f44336;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-color);
  border-top-color: var(--accent-color);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty {
  text-align: center;
  color: var(--text-secondary);
  padding: 60px 20px;
  font-size: 1.1rem;
}

/* Модальное окно */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal {
  background: var(--bg-card);
  border-radius: 20px;
  padding: 32px;
  max-width: 480px;
  width: 90%;
  box-shadow: var(--shadow-strong);
}

.modal h2 {
  margin: 0 0 8px;
  color: var(--heading-color);
}

.modal-project {
  color: var(--text-secondary);
  margin-bottom: 20px;
  font-weight: 500;
}

.modal-textarea {
  width: 100%;
  padding: 12px;
  background: var(--bg-page);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  color: var(--text-primary);
  font-size: 1rem;
  resize: vertical;
  box-sizing: border-box;
  margin-bottom: 20px;
  font-family: inherit;
}

.modal-textarea:focus {
  outline: none;
  border-color: var(--accent-color);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* Адаптивность */
@media (max-width: 640px) {
  .moderation-page {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .tabs {
    flex-direction: column;
  }
  
  .card-actions {
    flex-direction: column;
  }
  
  .btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
