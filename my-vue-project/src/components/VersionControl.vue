<template>
  <div class="version-control">
    <!-- Кнопка открытия панели версий (видна всем, но управление только у модераторов) -->
    <button 
      class="version-btn"
      @click="showPanel = !showPanel"
      :class="{ active: showPanel }"
    >
      <span class="btn-icon">🕐</span>
      {{ $t('versionControl.title') }}
      <span v-if="versionStats" class="version-badge">
        v{{ versionStats.current_version }}.{{ versionStats.current_points }}
      </span>
    </button>

    <!-- Панель версий -->
    <Transition name="slide">
      <div v-if="showPanel" class="version-panel">
        <!-- Заголовок -->
        <div class="panel-header">
          <h3>{{ $t('versionControl.history') }}</h3>
          <button class="close-btn" @click="showPanel = false">✕</button>
        </div>

        <!-- Статистика -->
        <div v-if="versionStats" class="version-stats">
          <div class="stat-item">
            <span class="stat-label">{{ $t('versionControl.checkpoints') }}</span>
            <span class="stat-value">{{ versionStats.total_checkpoints }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">{{ $t('versionControl.changes') }}</span>
            <span class="stat-value">{{ versionStats.total_changes }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">{{ $t('versionControl.toNextCheckpoint') }}</span>
            <span class="stat-value">{{ versionStats.points_to_next_checkpoint }} / {{ versionStats.points_threshold }}</span>
          </div>
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ width: (versionStats.progress_percent || 0) + '%' }"
              :class="{ warning: (versionStats.progress_percent || 0) > 80 }"
            ></div>
          </div>
        </div>

        <!-- Загрузка -->
        <div v-if="loading" class="loading">
          <div class="spinner"></div>
          <p>{{ $t('common.loading') }}</p>
        </div>

        <!-- Ошибка -->
        <div v-else-if="error" class="error">
          <p>{{ error }}</p>
          <button class="retry-btn" @click="loadVersions">{{ $t('common.retry') }}</button>
        </div>

        <!-- Список версий -->
        <div v-else class="versions-list">
          <!-- Кнопка создания чекпоинта (только для модераторов) -->
          <div v-if="isModerator" class="create-checkpoint">
            <button 
              class="checkpoint-btn" 
              @click="showCreateCheckpoint = !showCreateCheckpoint"
              :disabled="creating"
            >
              📌 {{ $t('versionControl.createCheckpoint') }}
            </button>
            <div v-if="showCreateCheckpoint" class="checkpoint-form">
              <input 
                v-model="checkpointMessage" 
                type="text" 
                :placeholder="$t('versionControl.checkpointPlaceholder')"
                @keyup.enter="createCheckpoint"
              />
              <button @click="createCheckpoint" :disabled="creating">
                {{ creating ? '...' : '✓' }}
              </button>
            </div>
          </div>

          <!-- Чекпоинты и изменения -->
          <div 
            v-for="(checkpoint, cpIndex) in versions" 
            :key="String(checkpoint.version)"
            class="version-group"
          >
            <!-- Заголовок чекпоинта -->
            <div 
              class="checkpoint-header"
              :class="{ current: checkpoint.is_current }"
              @click="toggleCheckpoint(cpIndex)"
            >
              <div class="checkpoint-info">
                <span class="checkpoint-version">
                  {{ checkpoint.is_current ? $t('versionControl.current') : 'v' + checkpoint.version }}
                </span>
                <span class="checkpoint-message">{{ checkpoint.message }}</span>
              </div>
              <div class="checkpoint-meta">
                <span class="checkpoint-points">{{ checkpoint.total_points }} pts</span>
                <span class="checkpoint-arrow">{{ expandedCheckpoints[cpIndex] ? '▾' : '▸' }}</span>
              </div>
            </div>

            <!-- Список изменений -->
            <Transition name="expand">
              <div v-if="expandedCheckpoints[cpIndex]" class="changes-list">
                <div 
                  v-for="change in checkpoint.changes" 
                  :key="String(change.version)"
                  class="change-item"
                >
                  <div class="change-header" @click="toggleChange(String(checkpoint.version), change.change_version)">
                    <div class="change-info">
                      <span class="change-type-icon">{{ getChangeIcon(change.type) }}</span>
                      <span class="change-version">{{ change.version }}</span>
                      <span class="change-type">{{ getChangeLabel(change.type) }}</span>
                      <span class="change-points">+{{ change.points }}</span>
                    </div>
                    <div class="change-meta">
                      <span class="change-time">{{ formatTime(change.created_at) }}</span>
                      <span class="change-arrow">{{ expandedChanges[String(change.version)] ? '▾' : '▸' }}</span>
                    </div>
                  </div>

                  <!-- Детали изменения -->
                  <Transition name="expand">
                    <div v-if="expandedChanges[String(change.version)]" class="change-details">
                      <p class="change-desc">{{ change.description }}</p>
                      
                      <!-- Кнопки действий (только для модераторов) -->
                      <div v-if="isModerator" class="change-actions">
                        <button 
                          class="action-btn restore-btn"
                          @click="confirmRestore(checkpoint.version, change.change_version)"
                        >
                          ⏪ {{ $t('versionControl.restore') }}
                        </button>
                        <button 
                          class="action-btn delete-btn"
                          @click="confirmDeleteChange(checkpoint.version, change.change_version)"
                        >
                          🗑️ {{ $t('versionControl.delete') }}
                        </button>
                      </div>
                    </div>
                  </Transition>
                </div>

                <!-- Действия для всего чекпоинта (только для модераторов) -->
                <div v-if="isModerator" class="checkpoint-actions">
                  <button 
                    class="action-btn restore-btn"
                    @click="confirmRestore(checkpoint.version, 0)"
                  >
                    ⏪ {{ $t('versionControl.restoreToCheckpoint') }}
                  </button>
                  <button 
                    v-if="!checkpoint.is_current"
                    class="action-btn delete-btn"
                    @click="confirmDeleteCheckpoint(checkpoint.version)"
                  >
                    🗑️ {{ $t('versionControl.deleteCheckpoint') }}
                  </button>
                </div>
              </div>
            </Transition>
          </div>

          <!-- Если нет версий -->
          <div v-if="versions.length === 0" class="no-versions">
            {{ $t('versionControl.noVersions') }}
          </div>
        </div>
      </div>
    </Transition>

    <!-- Модальное окно подтверждения восстановления -->
    <Teleport to="body">
      <div v-if="showRestoreConfirm" class="modal-overlay" @click.self="showRestoreConfirm = false">
        <div class="modal">
          <div class="modal-header warning">
            <span class="modal-icon">⚠️</span>
            <h2>{{ $t('versionControl.confirmRestore') }}</h2>
          </div>
          <p class="modal-text">
            {{ $t('versionControl.restoreWarning') }}
          </p>
          <p class="modal-version">
            {{ $t('versionControl.restoringTo') }}: <strong>v{{ restoreTarget.cp }}.{{ restoreTarget.ch }}</strong>
          </p>
          <div class="modal-actions">
            <button class="modal-btn cancel" @click="showRestoreConfirm = false">
              {{ $t('common.cancel') }}
            </button>
            <button class="modal-btn danger" @click="restoreVersion" :disabled="restoring">
              {{ restoring ? $t('common.processing') : $t('versionControl.confirm') }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '@/stores/auth';
import api from '@/utils/api';

const { t } = useI18n();
const authStore = useAuthStore();

const props = defineProps<{
  projectId: number;
}>();

// Проверка прав - админ или куратор (не обязательно участник проекта)
const isModerator = computed(() => {
  const user = authStore.user;
  if (!user) return false;
  // Админ всегда модератор
  if (user.is_admin) return true;
  // Куратор (учитель с флагом curator) тоже модератор
  if (user.is_teacher && user.teacher_info?.curator === true) return true;
  return false;
});

// Состояние панели
const showPanel = ref(false);
const loading = ref(false);
const error = ref('');
const versions = ref<any[]>([]);
const versionStats = ref<any>(null);

// Раскрытые элементы
const expandedCheckpoints = ref<Record<number, boolean>>({});
const expandedChanges = ref<Record<string, boolean>>({});

// Создание чекпоинта
const showCreateCheckpoint = ref(false);
const checkpointMessage = ref('');
const creating = ref(false);

// Восстановление
const showRestoreConfirm = ref(false);
const restoreTarget = ref({ cp: 0, ch: 0 });
const restoring = ref(false);

// Загрузка версий
const loadVersions = async () => {
  loading.value = true;
  error.value = '';
  try {
    const [versRes, statsRes] = await Promise.all([
      api.get(`/projects/${props.projectId}/versions`),
      api.get(`/projects/${props.projectId}/version-stats`)
    ]);
    versions.value = versRes.data.checkpoints || [];
    versionStats.value = statsRes.data;
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load versions';
  } finally {
    loading.value = false;
  }
};

// Переключение чекпоинта
const toggleCheckpoint = (index: number) => {
  expandedCheckpoints.value[index] = !expandedCheckpoints.value[index];
};

// Переключение изменения
const toggleChange = (cpVersion: string, chVersion: number) => {
  const key = `${cpVersion}.${chVersion}`;
  expandedChanges.value[key] = !expandedChanges.value[key];
};

// Создание чекпоинта
const createCheckpoint = async () => {
  if (!checkpointMessage.value.trim()) return;
  creating.value = true;
  try {
    await api.post(`/projects/${props.projectId}/checkpoint`, {
      message: checkpointMessage.value
    });
    checkpointMessage.value = '';
    showCreateCheckpoint.value = false;
    await loadVersions();
  } catch (err: any) {
    alert(err.response?.data?.detail || 'Failed to create checkpoint');
  } finally {
    creating.value = false;
  }
};

// Подтверждение восстановления
// Исправленная функция confirmRestore
const confirmRestore = (cpVersion: any, ch: number) => {
  // Очищаем версию от текста "(current)" и преобразуем в число
  const cleanVersion = String(cpVersion).replace(/\s*\(current\)\s*/, '').trim();
  const cp = parseInt(cleanVersion, 10);
  
  if (isNaN(cp) || cp <= 0) {
    alert('Invalid checkpoint version');
    return;
  }
  
  restoreTarget.value = { cp, ch };
  showRestoreConfirm.value = true;
};

// Восстановление версии
const restoreVersion = async () => {
  restoring.value = true;
  try {
    const params: any = {};
    if (restoreTarget.value.ch > 0) {
      params.change_version = restoreTarget.value.ch;
    }
    await api.post(
      `/projects/${props.projectId}/restore/${restoreTarget.value.cp}`,
      null,
      { params }
    );
    showRestoreConfirm.value = false;
    showPanel.value = false;
    window.location.reload();
  } catch (err: any) {
    alert(err.response?.data?.detail || 'Failed to restore version');
  } finally {
    restoring.value = false;
  }
};

// Удаление изменения
const confirmDeleteChange = async (cp: number, ch: number) => {
  if (!confirm(t('versionControl.confirmDelete'))) return;
  try {
    await api.delete(`/projects/${props.projectId}/versions/${cp}?change_version=${ch}`);
    await loadVersions();
  } catch (err: any) {
    alert(err.response?.data?.detail || 'Failed to delete change');
  }
};

// Удаление чекпоинта
const confirmDeleteCheckpoint = async (cp: number) => {
  if (!confirm(t('versionControl.confirmDeleteCheckpoint'))) return;
  try {
    await api.delete(`/projects/${props.projectId}/versions/${cp}?change_version=0`);
    await loadVersions();
  } catch (err: any) {
    alert(err.response?.data?.detail || 'Failed to delete checkpoint');
  }
};

// Вспомогательные функции
const getChangeIcon = (type: string): string => {
  const icons: Record<string, string> = {
    comment_add: '💬', comment_delete: '🗑️', comment_restore: '🔄',
    task_comment_add: '💬', task_comment_delete: '🗑️',
    link_update: '🔗', link_delete: '🗑️',
    task_update: '📋', tasks_bulk_update: '📋', subtask_move: '↔️',
    file_upload: '📎', file_delete: '🗑️',
    project_full_update: '📝', project_title_update: '📝',
    participant_add: '👤', participant_remove: '👋',
    project_create: '🆕', admin_delete_project: '💀',
    suggestion_create: '💡', suggestion_accept: '✅', suggestion_reject: '❌',
    join_request_create: '📨', join_request_accept: '✅', join_request_reject: '❌',
    project_approval_request: '📤', project_approval_decision: '📥',
    project_approval_cancel: '↩️',
    project_hide_toggle: '👁️', project_mark_old: '📦', project_unmark_old: '📦',
    admin_delete_all_files: '🗑️', admin_update_project: '📝',
    admin_toggle_file_limits: '⚙️',
  };
  return icons[type] || '📌';
};

const getChangeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    comment_add: 'Comment added', comment_delete: 'Comment deleted',
    comment_restore: 'Comment restored', task_comment_add: 'Task comment',
    task_comment_delete: 'Task comment deleted', link_update: 'Link updated',
    link_delete: 'Link deleted', task_update: 'Task updated',
    tasks_bulk_update: 'Tasks updated', subtask_move: 'Subtask moved',
    file_upload: 'File uploaded', file_delete: 'File deleted',
    project_full_update: 'Project updated', participant_add: 'Participant added',
    participant_remove: 'Participant removed', project_create: 'Project created',
    admin_delete_project: 'Project deleted', suggestion_create: 'Suggestion',
    suggestion_accept: 'Suggestion accepted', suggestion_reject: 'Suggestion rejected',
    join_request_create: 'Join request', join_request_accept: 'Request accepted',
    join_request_reject: 'Request rejected', project_approval_request: 'Approval requested',
    project_approval_decision: 'Approval decision', project_approval_cancel: 'Approval cancelled',
    project_hide_toggle: 'Visibility toggled', project_mark_old: 'Marked old',
    project_unmark_old: 'Unmarked old', admin_delete_all_files: 'Files deleted',
    admin_update_project: 'Admin update', admin_toggle_file_limits: 'File limits',
  };
  return labels[type] || type;
};

const formatTime = (time: string | null): string => {
  if (!time) return '';
  return new Date(time).toLocaleString();
};

// Загрузка при открытии
watch(showPanel, (val) => {
  if (val) loadVersions();
});
</script>

<style scoped>
.version-control { position: relative; }
.version-btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 8px 16px; background: var(--bg-card);
  border: 1px solid var(--border-color); border-radius: 8px;
  color: var(--text-primary); font-size: 0.9rem; cursor: pointer; transition: all 0.2s;
}
.version-btn:hover, .version-btn.active { border-color: var(--accent-color); color: var(--accent-color); }
.version-badge { background: var(--accent-color); color: #fff; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; }
.version-panel {
  position: absolute; top: 100%; right: 0; margin-top: 8px; width: 480px; max-height: 600px;
  background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0,0,0,.2); z-index: 100; display: flex; flex-direction: column; overflow: hidden;
}
.panel-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid var(--border-color); }
.panel-header h3 { margin: 0; color: var(--heading-color); }
.close-btn { background: none; border: none; color: var(--text-secondary); font-size: 1.2rem; cursor: pointer; }
.version-stats { padding: 12px 20px; background: var(--bg-page); border-bottom: 1px solid var(--border-color); }
.stat-item { display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 0.85rem; }
.stat-label { color: var(--text-secondary); }
.stat-value { font-weight: 600; color: var(--heading-color); }
.progress-bar { height: 4px; background: var(--border-color); border-radius: 2px; margin-top: 8px; overflow: hidden; }
.progress-fill { height: 100%; background: var(--accent-color); border-radius: 2px; transition: width .3s; }
.progress-fill.warning { background: #ff9800; }
.versions-list { flex: 1; overflow-y: auto; padding: 12px; }
.create-checkpoint { margin-bottom: 12px; }
.checkpoint-btn { width: 100%; padding: 10px; background: var(--accent-color); color: #fff; border: none; border-radius: 8px; cursor: pointer; font-weight: 500; }
.checkpoint-form { display: flex; gap: 8px; margin-top: 8px; }
.checkpoint-form input { flex: 1; padding: 8px 12px; background: var(--bg-page); border: 1px solid var(--border-color); border-radius: 8px; color: var(--text-primary); }
.checkpoint-form button { padding: 8px 12px; background: #4caf50; color: #fff; border: none; border-radius: 8px; cursor: pointer; }
.version-group { margin-bottom: 8px; border: 1px solid var(--border-color); border-radius: 12px; overflow: hidden; }
.checkpoint-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: var(--bg-page); cursor: pointer; transition: background .2s; }
.checkpoint-header:hover { background: var(--bg-hover); }
.checkpoint-header.current { background: rgba(var(--accent-rgb),.1); border-left: 3px solid var(--accent-color); }
.checkpoint-version { font-weight: 700; color: var(--accent-color); margin-right: 8px; }
.checkpoint-message { color: var(--text-primary); font-size: .9rem; }
.checkpoint-meta { display: flex; align-items: center; gap: 12px; color: var(--text-secondary); font-size: .85rem; }
.changes-list { background: var(--bg-card); }
.change-item { border-bottom: 1px solid var(--border-color); }
.change-item:last-child { border-bottom: none; }
.change-header { display: flex; justify-content: space-between; align-items: center; padding: 10px 16px 10px 32px; cursor: pointer; transition: background .2s; }
.change-header:hover { background: var(--bg-hover); }
.change-info { display: flex; align-items: center; gap: 8px; font-size: .85rem; }
.change-version { font-weight: 600; color: var(--accent-color); }
.change-type { color: var(--text-primary); }
.change-points { color: var(--text-secondary); font-size: .8rem; }
.change-time { color: var(--text-secondary); font-size: .8rem; margin-right: 8px; }
.change-details { padding: 12px 16px 12px 32px; background: var(--bg-page); border-top: 1px solid var(--border-color); }
.change-desc { color: var(--text-primary); font-size: .9rem; margin-bottom: 12px; }
.change-actions, .checkpoint-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.checkpoint-actions { padding: 12px 16px; border-top: 1px solid var(--border-color); }
.action-btn { padding: 6px 12px; border: none; border-radius: 6px; font-size: .85rem; cursor: pointer; transition: all .2s; }
.restore-btn { background: #ff9800; color: #fff; }
.restore-btn:hover { background: #e68900; }
.delete-btn { background: rgba(244,67,54,.1); color: #f44336; }
.delete-btn:hover { background: #f44336; color: #fff; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.5); display: flex; align-items: center; justify-content: center; z-index: 1000; backdrop-filter: blur(4px); }
.modal { background: var(--bg-card); border-radius: 20px; padding: 24px; max-width: 480px; width: 90%; box-shadow: 0 16px 48px rgba(0,0,0,.3); }
.modal-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.modal-header.warning { color: #ff9800; }
.modal-icon { font-size: 2rem; }
.modal-header h2 { margin: 0; color: var(--heading-color); }
.modal-text { color: var(--text-primary); margin-bottom: 8px; }
.modal-version { color: var(--text-secondary); margin-bottom: 20px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 12px; }
.modal-btn { padding: 10px 20px; border: none; border-radius: 8px; font-weight: 500; cursor: pointer; }
.modal-btn.cancel { background: var(--bg-page); color: var(--text-primary); }
.modal-btn.danger { background: #f44336; color: #fff; }
.loading { text-align: center; padding: 40px; color: var(--text-secondary); }
.spinner { width: 32px; height: 32px; border: 3px solid var(--border-color); border-top-color: var(--accent-color); border-radius: 50%; animation: spin .8s linear infinite; margin: 0 auto 12px; }
@keyframes spin { to { transform: rotate(360deg); } }
.error { text-align: center; padding: 20px; color: #f44336; }
.retry-btn { padding: 8px 16px; background: var(--accent-color); color: #fff; border: none; border-radius: 8px; cursor: pointer; margin-top: 8px; }
.no-versions { text-align: center; color: var(--text-secondary); padding: 40px; }
.slide-enter-active, .slide-leave-active { transition: all .3s ease; }
.slide-enter-from, .slide-leave-to { opacity: 0; transform: translateY(-10px); }
.expand-enter-active, .expand-leave-active { transition: all .3s ease; }
.expand-enter-from, .expand-leave-to { opacity: 0; max-height: 0; }
</style>