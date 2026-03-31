<template>
  <div class="task-details-page">
    <!-- Уведомление -->
    <Transition name="fade">
      <div v-if="notification.show" class="notification" :class="notification.type">
        <span class="notification-message">{{ notification.message }}</span>
        <button class="notification-close" @click="closeNotification">✕</button>
      </div>
    </Transition>

    <header class="details-header">
      <h1>{{ $t('taskDetails.title') }}</h1>
      <div class="header-actions">
        <ThemeToggle />
        <LanguageSwitcher />
        <router-link v-if="canEditTask" :to="`/project/${projectId}/task/${taskIndex}/edit`">
          <button class="icon-button edit-task-button" :title="$t('common.edit')">✎</button>
        </router-link>
        <button class="icon-button home-button" @click="goHome" :title="$t('common.home')">🏠</button>
        <button class="icon-button back-button" @click="goBack" :title="$t('common.back')">◀</button>
      </div>
    </header>

    <div v-if="loading" class="loading">{{ $t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <div v-else-if="task" class="task-card" :class="taskStatusClass">
      <h2 class="task-title">{{ task.title }}</h2>

      <section class="task-section">
        <h3>{{ $t('taskDetails.status') }}</h3>
        <p>{{ getTaskStatusText(task.status) }}</p>
      </section>

      <section class="task-section">
        <h3>{{ $t('taskDetails.description') }}</h3>
        <p>{{ task.body }}</p>
      </section>

      <section class="task-section">
        <h3>{{ $t('taskDetails.period') }}</h3>
        <p>
          <span :class="{ 'invalid-date': !isValidDateFormat(task.timeline) }">{{ task.timeline || '?' }}</span>
          –
          <span :class="{ 'invalid-date': !isValidDateFormat(task.timelinend) }">{{ task.timelinend || '?' }}</span>
        </p>
        <span v-if="!isValidDateFormat(task.timeline) && task.timeline" class="date-warning">
          ⚠️ {{ $t('taskDetails.invalidStartDateWarning') }}
        </span>
        <span v-if="!isValidDateFormat(task.timelinend) && task.timelinend" class="date-warning">
          ⚠️ {{ $t('taskDetails.invalidEndDateWarning') }}
        </span>
      </section>

      <!-- Комментарии к задаче -->
      <section class="task-section comments-main-section">
        <div class="section-header">
          <h3>{{ $t('taskDetails.taskComments') }}</h3>
          <button v-if="hasFullAccess" class="comment-toggle-btn" @click="showTaskComments = !showTaskComments">
            <span class="btn-content">
              <span class="comment-icon">💬</span>
              {{ showTaskComments ? $t('common.hide') : $t('common.show') }}
              <span v-if="unreadTaskCommentsCount > 0" class="header-unread-badge">{{ unreadTaskCommentsCount }}</span>
            </span>
          </button>
        </div>

        <CommentsSection
          v-if="showTaskComments"
          :comments="taskComments"
          :can-comment="hasFullAccess"
          :is-author="canEditTask"
          :can-hide-comments="canHideComments"
          :is-admin="isAdmin"
          :is-curator="isCurator"
          :on-add-comment="addTaskComment"
          :on-mark-as-read="markTaskCommentAsRead"
          :on-hide-comment="hideTaskComment"
          :on-permanent-delete="permanentDeleteComment"
          :on-restore-comment="restoreTaskComment"
        />
      </section>

      <!-- ========== ОБЯЗАТЕЛЬНЫЕ ФАЙЛЫ ========== -->
      <section v-if="requiredFiles.length" class="task-section required-files-section">
        <h3>{{ $t('taskDetails.requiredFiles') }}</h3>
        <div class="required-files-list">
          <div
            v-for="req in requiredFiles"
            :key="req.id"
            class="required-file-status"
            :class="{ satisfied: isRequiredFileSatisfied(req.id) }"
          >
            <div class="rf-info">
              <span class="rf-name">{{ req.name }}</span>
              <span v-if="req.description" class="rf-desc">{{ req.description }}</span>
            </div>
            <div class="rf-actions">
              <button
                v-if="!isRequiredFileSatisfied(req.id)"
                class="upload-file-btn"
                @click="uploadFileForRequired(req.id)"
                :disabled="uploadingFiles[req.id]"
              >
                {{ uploadingFiles[req.id] ? $t('common.sending') : '📎 ' + $t('common.upload') }}
              </button>
              <span v-else class="satisfied-badge">✅ {{ $t('taskDetails.attached') }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- ========== ПРИКРЕПЛЁННЫЕ ФАЙЛЫ ========== -->
      <section v-if="attachments.length" class="task-section attachments-section">
        <h3>{{ $t('taskDetails.attachments') }}</h3>
        <div class="attachments-list">
          <div v-for="att in attachments" :key="att.id" class="attachment-item">
            <a href="#" @click.prevent="previewAttachment(att)">{{ att.original_filename }}</a>
            <span class="attachment-meta">({{ formatFileSize(att.size) }})</span>
            <button
              v-if="canEditTask"
              class="delete-attachment"
              @click="openDeleteFileModal(att.file_id)"
              :disabled="deletingAttachment"
              :title="$t('common.delete')"
            >🗑</button>
          </div>
        </div>
      </section>

      <!-- Кнопка загрузки любого файла -->
      <div class="upload-generic-btn-wrapper">
        <button class="upload-generic-btn" @click="uploadGenericFile" :disabled="uploadingFiles['generic']">
          {{ uploadingFiles['generic'] ? $t('common.sending') : '📁 ' + $t('taskDetails.uploadFile') }}
        </button>
      </div>

      <!-- Диаграмма Ганта, подзадачи, прогресс -->
      <section class="gantt-section">
        <h3>{{ $t('taskDetails.totalProgress') }}</h3>
        <div class="gantt-container">
          <div class="gantt-bar-container">
            <div class="gantt-bar" :style="{ width: totalProgress + '%', backgroundColor: barColor }"
                 :title="`${$t('taskDetails.progress')}: ${totalProgress.toFixed(1)}%`"></div>
            <span class="gantt-percent">{{ totalProgress.toFixed(1) }}%</span>
            <span class="gantt-dates">{{ task.timeline || '?' }} – {{ task.timelinend || '?' }}</span>
          </div>
          <div class="gantt-labels">
            <span>{{ task.timeline || '?' }}</span>
            <span>{{ $t('taskDetails.today') }}</span>
            <span>{{ task.timelinend || '?' }}</span>
          </div>
        </div>
        <div class="progress-breakdown" v-if="subtasks.length > 0">
          <div class="breakdown-item">
            <span class="breakdown-label">{{ $t('taskDetails.subtasks') }}:</span>
            <span class="breakdown-value">{{ completedSubtasksPercent.toFixed(1) }}%</span>
          </div>
          <div class="breakdown-item">
            <span class="breakdown-label">{{ $t('taskDetails.extra') }}:</span>
            <span class="breakdown-value">{{ extraProgress }}%</span>
          </div>
        </div>
      </section>

      <section v-if="subtasks.length > 0" class="subtasks-section">
        <h3>{{ $t('taskDetails.subtasks') }}</h3>
        <div class="subtasks-list">
          <div v-for="subtask in subtasks" :key="subtask.id" class="subtask-item" :class="{ completed: subtask.completed }">
            <div class="subtask-info">
              <input type="checkbox" :checked="subtask.completed" @change="toggleSubtask(subtask)"
                     :disabled="actionInProgress || !canEditTask" />
              <span class="subtask-title">{{ subtask.title }}</span>
              <span class="subtask-percent">{{ subtask.progressPercent }}%</span>
            </div>
            <p v-if="subtask.description" class="subtask-description">{{ subtask.description }}</p>
          </div>
        </div>
        <div class="subtasks-summary">
          {{ $t('taskDetails.subtasksCompleted') }}: {{ completedSubtasksPercent.toFixed(1) }}% / {{ totalSubtasksPercent.toFixed(1) }}%
        </div>
      </section>

      <section v-if="showManualProgress && canEditTask" class="progress-section">
        <h3>{{ $t('taskDetails.extraProgress') }}</h3>
        <div class="progress-slider-container">
          <span class="progress-value">{{ sliderValue }}%</span>
          <span class="progress-max"> / {{ maxExtra.toFixed(1) }}%</span>
          <input
            type="range"
            :value="sliderValue"
            @input="updateSliderValue"
            class="progress-slider"
            :min="0"
            :max="maxExtra"
            step="1"
          />
        </div>
        <button class="apply-progress-button" @click="openConfirmDialog">{{ $t('taskDetails.applyExtraProgress') }}</button>
      </section>
      <div v-else-if="showManualProgress && !canEditTask" class="progress-section-disabled">
        <p class="disabled-message">🔒 {{ $t('taskDetails.onlyEditorsCanChangeProgress') }}</p>
      </div>

      <section class="action-buttons" v-if="hasFullAccess">
        <div v-if="task.status !== 'выполнена'">
          <button class="complete-button" @click="completeTask"
                  :disabled="actionInProgress || totalProgress < 100 || !canEditTask || !areAllRequiredFilesAttached"
                  :title="getCompleteButtonTitle()">
            {{ actionInProgress ? $t('common.sending') : $t('taskDetails.completeTask') }}
          </button>
        </div>
        <div v-else>
          <template v-if="canEditTask">
            <button v-if="!showRenewOptions" class="renew-button" @click="showRenewOptions = true" :disabled="actionInProgress">
              🔄 {{ $t('taskDetails.renew') }}
            </button>
            <div v-else class="renew-options">
              <button class="status-option work" @click="updateTaskStatus('в работе')" :disabled="actionInProgress">
                {{ $t('projectDetails.status.inProgress') }}
              </button>
              <button class="status-option waiting" @click="updateTaskStatus('ожидает')" :disabled="actionInProgress">
                {{ $t('projectDetails.status.waiting') }}
              </button>
              <button class="status-option cancel" @click="showRenewOptions = false">
                {{ $t('common.cancel') }}
              </button>
            </div>
          </template>
          <span v-else class="task-completed-info">{{ $t('taskDetails.taskCompleted') }}</span>
        </div>
      </section>

      <section class="status-badges">
        <span v-if="isInvalid" class="badge invalid">{{ $t('taskDetails.impossibleDeadline') }}</span>
        <span v-if="isOverdue" class="badge overdue">{{ $t('taskDetails.overdue') }}</span>
        <span v-if="isUrgent && !isOverdue && !isInvalid" class="badge urgent">{{ $t('taskDetails.urgent') }}</span>
      </section>
    </div>

    <!-- Модальное окно подтверждения (общий прогресс) -->
    <div v-if="showConfirmDialog" class="modal-overlay" @click.self="closeConfirmDialog">
      <div class="modal-content">
        <h3>{{ $t('common.confirm') }}</h3>
        <p>{{ $t('taskDetails.confirmExtraProgress', { value: sliderValue }) }}</p>
        <div class="modal-actions">
          <button class="modal-confirm" @click="confirmExtraChange">{{ $t('common.yes') }}</button>
          <button class="modal-cancel" @click="closeConfirmDialog">{{ $t('common.no') }}</button>
        </div>
      </div>
    </div>

    <!-- Модальное окно предпросмотра файла -->
    <FilePreviewModal
      :show="previewModalVisible"
      :file="previewFile"
      :base-url="baseUrl"
      @close="previewModalVisible = false"
    />

    <!-- Модальное окно подтверждения удаления файла -->
    <div v-if="showDeleteFileModal" class="modal-overlay" @click.self="closeDeleteFileModal">
      <div class="modal-content">
        <h3>{{ $t('common.confirm') }}</h3>
        <p>{{ $t('taskDetails.confirmDeleteFile') }}</p>
        <div class="modal-actions">
          <button class="modal-confirm" @click="confirmDeleteFile">{{ $t('common.yes') }}</button>
          <button class="modal-cancel" @click="closeDeleteFileModal">{{ $t('common.no') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useProjectsStore } from '@/stores/projects';
import { useAuthStore } from '@/stores/auth';
import { useUsersStore } from '@/stores/users';
import ThemeToggle from '@/components/ThemeToggle.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';
import CommentsSection from '@/components/CommentsSection.vue';
import FilePreviewModal from '@/components/FilePreviewModal.vue';
import type { Task, SubTask, Comment, ProjectRole, RequiredFile, TaskAttachment } from '@/types';
import axios from 'axios';

const { t } = useI18n();
const baseUrl = 'http://localhost:8000';
const generateId = () => Date.now().toString(36) + Math.random().toString(36).substr(2);

const route = useRoute();
const router = useRouter();
const projectsStore = useProjectsStore();
const authStore = useAuthStore();
const usersStore = useUsersStore();

const projectId = Number(route.params.projectId);
const taskIndex = Number(route.params.taskIndex);

const project = ref<any>(null);
const task = ref<Task | null>(null);
const loading = ref(true);
const error = ref('');
const actionInProgress = ref(false);
const showRenewOptions = ref(false);
const showTaskComments = ref(false);
const previewModalVisible = ref(false);
const previewFile = ref<any>(null);

const savedProgress = ref(0);
const sliderValue = ref(0);
const oldSliderValue = ref(0);
const showConfirmDialog = ref(false);

// === Состояния для модального окна удаления файла ===
const showDeleteFileModal = ref(false);
const fileToDelete = ref<number | null>(null);

// === Файловая часть с состояниями загрузки ===
const requiredFiles = computed<RequiredFile[]>(() => task.value?.required_files || []);
const attachments = computed<TaskAttachment[]>(() => task.value?.attachments || []);

const areAllRequiredFilesAttached = computed(() => {
  if (!requiredFiles.value.length) return true;
  return requiredFiles.value.every(req =>
    attachments.value.some(att => att.required_file_id === req.id)
  );
});

const uploadingFiles = ref<Record<string, boolean>>({});
const deletingAttachment = ref(false);

const extraProgress = computed(() => sliderValue.value);

// Уведомления
const notification = ref({ show: false, message: '', type: 'error' as 'error' | 'info' | 'success' });
let notificationTimeout: number | null = null;

function showNotification(message: string, type: 'error' | 'info' | 'success' = 'error', duration = 5000) {
  if (notificationTimeout) clearTimeout(notificationTimeout);
  notification.value = { show: true, message, type };
  notificationTimeout = window.setTimeout(() => { notification.value.show = false; }, duration);
}

function closeNotification() {
  notification.value.show = false;
  if (notificationTimeout) {
    clearTimeout(notificationTimeout);
    notificationTimeout = null;
  }
}

// Роль текущего пользователя в проекте
const userRole = computed<ProjectRole | null>(() => {
  if (!authStore.userId || !project.value) return null;
  const participant = project.value.participants?.find((p: any) => p.user_id === authStore.userId);
  return participant?.role || null;
});

const isAdmin = computed(() => (authStore.user?.is_admin ?? false));
const isCurator = computed(() => {
  const user = authStore.user;
  if (!user) return false;
  if (!user.is_teacher) return false;
  return user.teacher_info?.curator ?? false;
});

const hasFullAccess = computed(() => !!userRole.value || isAdmin.value || isCurator.value);
const canEditTask = computed(() => 
  userRole.value === 'customer' || 
  userRole.value === 'executor' || 
  userRole.value === 'curator' ||
  isAdmin.value || 
  isCurator.value
);
const canHideComments = computed(() => 
  userRole.value === 'supervisor' || 
  isAdmin.value || 
  isCurator.value
);

const taskComments = computed(() => task.value?.comments || []);
const unreadTaskCommentsCount = computed(() => {
  const comments = task.value?.comments || [];
  if (canHideComments.value) return comments.filter(c => !c.isRead).length;
  return comments.filter(c => !c.hidden && !c.isRead).length;
});

// Вспомогательные функции
function parseDate(dateStr?: string): Date | null {
  if (!dateStr) return null;
  const parts = dateStr.split('.');
  if (parts.length !== 3) return null;
  const [day, month, year] = parts.map(Number);
  if (isNaN(day) || isNaN(month) || isNaN(year)) return null;
  return new Date(year, month - 1, day);
}

function isValidDateFormat(dateStr?: string): boolean {
  if (!dateStr) return true;
  const parts = dateStr.split('.');
  if (parts.length !== 3) return false;
  const [day, month, year] = parts.map(Number);
  if (isNaN(day) || isNaN(month) || isNaN(year)) return false;
  if (day < 1 || day > 31 || month < 1 || month > 12 || year < 1000 || year > 9999) return false;
  const date = new Date(year, month - 1, day);
  return date.getDate() === day && date.getMonth() === month - 1 && date.getFullYear() === year;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// Подзадачи
const subtasks = computed(() => task.value?.subtasks || []);
const totalSubtasksPercent = computed(() => subtasks.value.reduce((sum, st) => sum + (st.progressPercent || 0), 0));
const completedSubtasksPercent = computed(() => subtasks.value.filter(st => st.completed).reduce((sum, st) => sum + (st.progressPercent || 0), 0));
const maxExtra = computed(() => {
  const val = 100 - completedSubtasksPercent.value;
  return (isNaN(val) || val < 0) ? 0 : val;
});
const totalProgress = computed(() => completedSubtasksPercent.value + sliderValue.value);
const showManualProgress = computed(() => task.value?.status === 'в работе' && maxExtra.value > 0);

// Загрузка задачи
async function loadTask() {
  if (isNaN(projectId) || isNaN(taskIndex) || taskIndex < 0) {
    error.value = t('taskDetails.invalidParams');
    loading.value = false;
    return;
  }
  try {
    const response = await axios.get(`${baseUrl}/projects/${projectId}`);
    project.value = response.data;
    if (!project.value || !project.value.tasks || !project.value.tasks[taskIndex]) {
      error.value = t('taskDetails.taskNotFound');
    } else {
      const loadedTask = project.value.tasks[taskIndex];
      task.value = loadedTask;
      savedProgress.value = loadedTask.progress ?? 0;
      if (loadedTask.subtasks && loadedTask.subtasks.length > 0) {
        const completedSum = loadedTask.subtasks
          .filter((st: SubTask) => st.completed)
          .reduce((sum: number, st: SubTask) => sum + (st.progressPercent || 0), 0);
        sliderValue.value = Math.max(0, savedProgress.value - completedSum);
      } else {
        sliderValue.value = savedProgress.value;
      }
    }
  } catch (err) {
    error.value = t('taskDetails.loadError');
    console.error(err);
  } finally {
    loading.value = false;
  }
}
onMounted(loadTask);
watch(() => route.params.id, loadTask);

// Статусы задачи
const isInvalid = computed(() => {
  const tsk = task.value;
  if (!tsk) return false;
  let startStr = tsk.timeline;
  let endStr = tsk.timelinend;
  if (!endStr && startStr && startStr.includes('-')) {
    const parts = startStr.split('-');
    startStr = parts[0] || '';
    endStr = parts[1] || '';
  }
  const start = parseDate(startStr || '');
  const end = parseDate(endStr || '');
  const startValid = isValidDateFormat(startStr);
  const endValid = isValidDateFormat(endStr);
  if ((startStr && !startValid) || (endStr && !endValid)) return true;
  return !start || !end || start > end;
});

const isOverdue = computed(() => {
  const tsk = task.value;
  if (!tsk || isInvalid.value) return false;
  let endStr = tsk.timelinend;
  if (!endStr && tsk.timeline && tsk.timeline.includes('-')) {
    const parts = tsk.timeline.split('-');
    endStr = parts[1] || '';
  }
  const end = parseDate(endStr || '');
  if (!end) return false;
  const today = new Date(); today.setHours(0, 0, 0, 0);
  return today > end && tsk.status !== 'выполнена';
});

const isUrgent = computed(() => {
  const tsk = task.value;
  if (!tsk || isInvalid.value || isOverdue.value) return false;
  let startStr = tsk.timeline;
  let endStr = tsk.timelinend;
  if (!endStr && startStr && startStr.includes('-')) {
    const parts = startStr.split('-');
    startStr = parts[0] || '';
    endStr = parts[1] || '';
  }
  const start = parseDate(startStr || '');
  const end = parseDate(endStr || '');
  if (!start || !end) return false;
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const totalDuration = (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24);
  if (totalDuration <= 0) return false;
  const elapsed = (today.getTime() - start.getTime()) / (1000 * 60 * 60 * 24);
  if (elapsed < 0) return false;
  const prog = elapsed / totalDuration;
  return prog > 2 / 3 && tsk.status !== 'выполнена';
});

const barColor = computed(() => {
  if (isInvalid.value) return '#9e9e9e';
  if (isOverdue.value) return '#f44336';
  if (isUrgent.value) return '#ff9800';
  return '#42b983';
});

const taskStatusClass = computed(() => {
  if (isInvalid.value) return 'task-invalid';
  if (isOverdue.value) return 'task-overdue';
  if (isUrgent.value) return 'task-urgent';
  return '';
});

function getTaskStatusText(status: string): string {
  switch (status) {
    case 'в работе': return t('projectDetails.status.inProgress');
    case 'ожидает': return t('projectDetails.status.waiting');
    case 'выполнена': return t('projectDetails.status.completed');
    default: return status;
  }
}

function getCompleteButtonTitle(): string {
  if (!canEditTask.value) return t('taskDetails.onlyEditorsCanComplete');
  if (totalProgress.value < 100) return t('taskDetails.completeOnlyAt100');
  if (!areAllRequiredFilesAttached.value) return t('taskDetails.missingRequiredFiles');
  return '';
}

// --- Методы для задач ---
const toggleSubtask = async (subtask: SubTask) => {
  if (!canEditTask.value) { 
    showNotification(t('taskDetails.onlyEditorsCanEditSubtasks'), 'info'); 
    return; 
  }
  const currentProject = project.value;
  const currentTask = task.value;
  if (!currentProject || !currentTask) return;
  actionInProgress.value = true;

  try {
    const updatedSubtasks = currentTask.subtasks?.map(st => {
      if (st.id === subtask.id) return { ...st, completed: !st.completed };
      return st;
    }) || [];

    const newCompletedSum = updatedSubtasks.filter(st => st.completed).reduce((sum, st) => sum + (st.progressPercent || 0), 0);

    if (sliderValue.value > (100 - newCompletedSum)) sliderValue.value = 100 - newCompletedSum;

    const newTotal = newCompletedSum + sliderValue.value;

    const updatedTask = { ...currentTask, subtasks: updatedSubtasks, progress: newTotal };
    const updatedTasks = [...currentProject.tasks];
    updatedTasks[taskIndex] = updatedTask;
    await projectsStore.updateProject(projectId, { tasks: updatedTasks });

    project.value.tasks = updatedTasks;
    task.value = updatedTask;
    savedProgress.value = newTotal;
  } catch (err) {
    console.error('Ошибка при переключении подзадачи:', err);
    showNotification(t('taskDetails.subtaskUpdateError'), 'error');
  } finally { actionInProgress.value = false; }
};

const completeTask = async () => {
  if (!canEditTask.value) { 
    showNotification(t('taskDetails.onlyEditorsCanComplete'), 'info'); 
    return; 
  }
  if (totalProgress.value < 100) {
    showNotification(t('taskDetails.completeOnlyAt100'), 'info');
    return;
  }
  if (!areAllRequiredFilesAttached.value) {
    showNotification(t('taskDetails.missingRequiredFiles'), 'info');
    return;
  }

  const currentProject = project.value;
  const currentTask = task.value;
  if (!currentProject || !currentTask || actionInProgress.value) return;
  actionInProgress.value = true;
  try {
    const updatedTasks = [...currentProject.tasks];
    updatedTasks[taskIndex] = { ...updatedTasks[taskIndex], status: 'выполнена' } as Task;
    await projectsStore.updateProject(projectId, { tasks: updatedTasks });
    router.push(`/project/${projectId}`);
  } catch (err) {
    console.error('Ошибка при завершении задачи:', err);
    showNotification(t('taskDetails.completeError'), 'error');
  } finally { actionInProgress.value = false; }
};

const updateTaskStatus = async (newStatus: string) => {
  if (!canEditTask.value) { 
    showNotification(t('taskDetails.onlyEditorsCanChangeStatus'), 'info'); 
    return; 
  }
  const currentProject = project.value;
  const currentTask = task.value;
  if (!currentProject || !currentTask || actionInProgress.value) return;
  actionInProgress.value = true;
  try {
    const updatedTasks = [...currentProject.tasks];
    updatedTasks[taskIndex] = { ...updatedTasks[taskIndex], status: newStatus } as Task;
    await projectsStore.updateProject(projectId, { tasks: updatedTasks });
    project.value = { ...currentProject, tasks: updatedTasks };
    task.value = updatedTasks[taskIndex];
    showRenewOptions.value = false;
  } catch (err) {
    console.error('Ошибка при обновлении статуса задачи:', err);
    showNotification(t('taskDetails.statusUpdateError'), 'error');
  } finally { actionInProgress.value = false; }
};

// --- Функции для работы с комментариями ---
const addTaskComment = async (content: string) => {
  if (!hasFullAccess.value) { 
    showNotification(t('taskDetails.onlyParticipantsCanComment'), 'info'); 
    return; 
  }
  if (!project.value || !task.value || !authStore.user) return;

  const newComment: Comment = {
    id: generateId(),
    authorId: authStore.user.id,
    content,
    createdAt: new Date().toISOString(),
    isRead: false,
    hidden: false,
  };

  try {
    const response = await axios.post(`${baseUrl}/projects/${projectId}/tasks/${taskIndex}/comments`, newComment);
    project.value = response.data;
    task.value = project.value.tasks[taskIndex];
    showTaskComments.value = true;
  } catch (error) {
    console.error('Failed to add comment:', error);
    showNotification(t('commentsSection.saveError'), 'error');
  }
};

const markTaskCommentAsRead = async (commentId: string) => {
  if (!task.value || !hasFullAccess.value) return;
  try {
    await axios.put(`${baseUrl}/projects/${projectId}/tasks/${taskIndex}/comments/${commentId}/read`);
    if (task.value.comments) {
      const updatedComments = task.value.comments.map(c => c.id === commentId ? { ...c, isRead: true } : c);
      const updatedTask = { ...task.value, comments: updatedComments };
      const updatedTasks = [...project.value.tasks];
      updatedTasks[taskIndex] = updatedTask;
      project.value.tasks = updatedTasks;
      task.value = updatedTask;
    }
  } catch (error) {
    console.error('Failed to mark comment as read:', error);
    showNotification(t('commentsSection.markReadError'), 'error');
  }
};

const hideTaskComment = async (commentId: string) => {
  if (!project.value) return;
  try {
    const response = await axios.delete(`${baseUrl}/projects/${projectId}/tasks/${taskIndex}/comments/${commentId}`);
    project.value = response.data;
    task.value = project.value.tasks[taskIndex];
  } catch (error) {
    console.error('Failed to hide comment:', error);
    showNotification(t('commentsSection.hideError'), 'error');
  }
};

const permanentDeleteComment = async (commentId: string) => {
  if (!project.value) return;
  try {
    await axios.delete(`${baseUrl}/admin/comments/${commentId}`);
    showNotification(t('commentsSection.permanentDeleteSuccess'), 'success');
    const updatedProject = await projectsStore.fetchProjectById(projectId);
    project.value = updatedProject;
    if (updatedProject && updatedProject.tasks && updatedProject.tasks[taskIndex]) {
      task.value = updatedProject.tasks[taskIndex];
    }
  } catch (error) {
    console.error('Failed to delete comment permanently', error);
    showNotification(t('commentsSection.permanentDeleteError'), 'error');
  }
};

const restoreTaskComment = async (commentId: string) => {
  if (!project.value) return;
  try {
    await axios.post(`${baseUrl}/projects/${projectId}/tasks/${taskIndex}/comments/${commentId}/restore`);
    showNotification(t('commentsSection.restoreSuccess'), 'success');
    const updatedProject = await projectsStore.fetchProjectById(projectId);
    project.value = updatedProject;
    if (updatedProject && updatedProject.tasks && updatedProject.tasks[taskIndex]) {
      task.value = updatedProject.tasks[taskIndex];
    }
  } catch (error) {
    console.error('Failed to restore comment', error);
    showNotification(t('commentsSection.restoreError'), 'error');
  }
};

// === Файловые методы с кастомным модальным окном ===
function isRequiredFileSatisfied(requiredId: string): boolean {
  return attachments.value.some(att => att.required_file_id === requiredId);
}

function uploadFileForRequired(requiredId: string) {
  const input = document.createElement('input');
  input.type = 'file';
  input.onchange = async (e) => {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (!file) return;
    const key = requiredId || 'generic';
    uploadingFiles.value[key] = true;
    const formData = new FormData();
    formData.append('file', file);
    formData.append('task_id', String(taskIndex));
    if (requiredId) formData.append('required_file_id', requiredId);
    try {
      await axios.post(`${baseUrl}/projects/${projectId}/files`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      await loadTask();
      showNotification(t('taskDetails.fileUploaded'), 'success');
    } catch (err: any) {
      console.error(err);
      showNotification(err.response?.data?.detail || t('taskDetails.uploadError'), 'error');
    } finally {
      uploadingFiles.value[key] = false;
    }
  };
  input.click();
}

function uploadGenericFile() {
  uploadFileForRequired('');
}

// Открытие модального окна удаления
function openDeleteFileModal(fileId: number) {
  fileToDelete.value = fileId;
  showDeleteFileModal.value = true;
}

function closeDeleteFileModal() {
  showDeleteFileModal.value = false;
  fileToDelete.value = null;
}

// Подтверждение удаления
async function confirmDeleteFile() {
  if (!fileToDelete.value) return;
  await deleteAttachment(fileToDelete.value);
  closeDeleteFileModal();
}

// Основная функция удаления (без confirm)
async function deleteAttachment(fileId: number) {
  deletingAttachment.value = true;
  try {
    await axios.delete(`${baseUrl}/files/${fileId}`);
    // Принудительная перезагрузка задачи
    const response = await axios.get(`${baseUrl}/projects/${projectId}`);
    project.value = response.data;
    task.value = project.value.tasks[taskIndex];
    savedProgress.value = task.value?.progress ?? 0;
    if (task.value?.subtasks && task.value.subtasks.length > 0) {
      const completedSum = task.value.subtasks
        .filter(st => st.completed)
        .reduce((sum, st) => sum + (st.progressPercent || 0), 0);
      sliderValue.value = Math.max(0, savedProgress.value - completedSum);
    } else {
      sliderValue.value = savedProgress.value;
    }
    showNotification(t('taskDetails.fileDeleted'), 'success');
  } catch (err: any) {
    console.error(err);
    showNotification(err.response?.data?.detail || t('taskDetails.deleteError'), 'error');
  } finally {
    deletingAttachment.value = false;
  }
}

function previewAttachment(att: TaskAttachment) {
  previewFile.value = { id: att.file_id, original_filename: att.original_filename };
  previewModalVisible.value = true;
}

// Метод для обновления ползунка
const updateSliderValue = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target) {
    sliderValue.value = parseFloat(target.value);
  }
};

// Диалог подтверждения изменения прогресса
const openConfirmDialog = () => { 
  oldSliderValue.value = sliderValue.value; 
  showConfirmDialog.value = true; 
};
const closeConfirmDialog = () => { 
  showConfirmDialog.value = false; 
};
const confirmExtraChange = async () => {
  if (!canEditTask.value) { 
    showNotification(t('taskDetails.onlyEditorsCanChangeProgress'), 'info'); 
    closeConfirmDialog(); 
    return; 
  }
  const currentProject = project.value;
  const currentTask = task.value;
  if (!currentProject || !currentTask) { 
    closeConfirmDialog(); 
    return; 
  }

  const newTotal = completedSubtasksPercent.value + sliderValue.value;
  actionInProgress.value = true;
  try {
    const updatedTasks = [...currentProject.tasks];
    updatedTasks[taskIndex] = { ...updatedTasks[taskIndex], progress: newTotal } as Task;
    await projectsStore.updateProject(projectId, { tasks: updatedTasks });
    project.value.tasks = updatedTasks;
    task.value = updatedTasks[taskIndex];
    savedProgress.value = newTotal;
  } catch (err) {
    console.error('Ошибка при обновлении прогресса:', err);
    showNotification(t('taskDetails.progressUpdateError'), 'error');
    sliderValue.value = savedProgress.value - completedSubtasksPercent.value;
  } finally { 
    actionInProgress.value = false; 
    showConfirmDialog.value = false; 
  }
};

const goBack = () => router.push(`/project/${projectId}`);
const goHome = () => router.push('/main');
</script>

<style scoped>
/* Все стили из оригинального файла остаются без изменений */
.required-files-section, .attachments-section {
  margin-bottom: 28px;
}
.required-files-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.required-file-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border-radius: 12px;
  background: var(--bg-page);
  border-left: 4px solid #ff9800;
}
.required-file-status.satisfied {
  background: rgba(76, 175, 80, 0.1);
  border-left-color: #4caf50;
}
.rf-name {
  font-weight: 600;
}
.rf-desc {
  font-size: 0.8rem;
  color: var(--text-secondary);
  display: block;
}
.satisfied-badge {
  color: #4caf50;
  font-weight: 500;
}
.upload-file-btn, .upload-generic-btn {
  background: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 20px;
  padding: 6px 12px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: background 0.2s;
}
.upload-file-btn:hover, .upload-generic-btn:hover {
  background: var(--accent-hover);
}
.attachments-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.attachment-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  background: var(--bg-page);
  border-radius: 8px;
}
.attachment-item a {
  color: var(--link-color);
  text-decoration: none;
  flex: 1;
}
.attachment-item a:hover {
  text-decoration: underline;
}
.attachment-meta {
  font-size: 0.75rem;
  color: var(--text-secondary);
}
.delete-attachment {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.1rem;
  padding: 4px;
  border-radius: 4px;
}
.delete-attachment:hover {
  background: rgba(244, 67, 54, 0.2);
}
.upload-generic-btn-wrapper {
  margin-bottom: 28px;
  text-align: right;
}
</style>

<!-- Остальные стили (диаграмма Ганта, подзадачи, прогресс) идут без изменений -->
<style scoped>
/* ---------- Общие стили ---------- */
.task-details-page {
  min-height: 100vh;
  background: var(--bg-page);
  padding: 20px;
  box-sizing: border-box;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  transition: background 0.3s;
}

.details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 800px;
  margin: 0 auto 20px;
  flex-wrap: wrap;
  gap: 10px;
}

.details-header h1 {
  color: var(--heading-color);
  font-size: 2rem;
  margin: 0;
  text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
}

.light-theme .details-header h1 {
  text-shadow: 1px 1px 2px rgba(255,255,255,0.5);
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.icon-button {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 50%;
  width: 44px;
  height: 44px;
  font-size: 1.4rem;
  cursor: pointer;
  box-shadow: var(--shadow);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s, box-shadow 0.2s;
  color: var(--text-primary);
}

.icon-button:hover {
  background: var(--bg-card);
  box-shadow: var(--shadow-strong);
}

/* ---------- Карточка задачи ---------- */
.task-card {
  background: var(--bg-card);
  border-radius: 32px;
  box-shadow: var(--shadow-strong);
  padding: 30px;
  max-width: 800px;
  margin: 0 auto;
  transition: border 0.2s, background 0.3s;
}

.task-card.task-overdue {
  border: 2px solid #f44336;
}

.task-card.task-urgent {
  border: 2px solid #ff9800;
}

.task-card.task-invalid {
  border: 2px solid #9e9e9e;
  opacity: 0.9;
}

.task-title {
  color: var(--heading-color);
  margin-bottom: 24px;
  font-size: 2rem;
  border-bottom: 2px solid var(--border-color);
  padding-bottom: 10px;
}

.task-section {
  margin-bottom: 28px;
}

.task-section h3 {
  color: var(--heading-color);
  margin-bottom: 10px;
  font-weight: 500;
  font-size: 1.2rem;
}

.task-section p {
  color: var(--text-primary);
  line-height: 1.6;
}

/* ---------- Валидация дат ---------- */
.invalid-date {
  color: #f44336;
  font-weight: 600;
  text-decoration: underline wavy #f44336;
}

.date-warning {
  display: block;
  color: #f44336;
  font-size: 0.85rem;
  margin-top: 4px;
}

/* ---------- Стили для комментариев ---------- */
.comments-main-section {
  margin-bottom: 28px;
  padding-bottom: 20px;
  border-bottom: 2px dashed var(--border-color);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.comment-toggle-btn {
  background: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 30px;
  padding: 8px 16px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s, box-shadow 0.2s;
  display: flex;
  align-items: center;
  box-shadow: var(--shadow);
}

.comment-toggle-btn:hover {
  background: var(--accent-hover);
  box-shadow: var(--shadow-strong);
}

.btn-content {
  display: flex;
  align-items: center;
  gap: 6px;
}

.comment-icon {
  font-size: 1.1rem;
}

.header-unread-badge {
  background: #f44336;
  color: white;
  border-radius: 50%;
  min-width: 20px;
  height: 20px;
  font-size: 11px;
  font-weight: bold;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
  margin-left: 4px;
}

/* ---------- Диаграмма Ганта ---------- */
.gantt-section {
  margin-top: 40px;
  padding-top: 20px;
  border-top: 2px dashed var(--border-color);
}

.gantt-section h3 {
  color: var(--heading-color);
  margin-bottom: 15px;
  font-weight: 500;
  text-align: center;
}

.gantt-container {
  width: 100%;
}

.gantt-bar-container {
  position: relative;
  height: 30px;
  background: var(--input-bg);
  border-radius: 15px;
  margin-bottom: 5px;
  display: flex;
  align-items: center;
  overflow: hidden;
}

.gantt-bar {
  height: 100%;
  background: #42b983;
  border-radius: 15px 0 0 15px;
  width: 0%;
  transition: width 0.3s ease;
}

.gantt-percent {
  position: absolute;
  left: 10px;
  font-size: 0.85rem;
  color: #3b82f6;
  background: rgba(0, 0, 0, 0.5);
  padding: 2px 8px;
  border-radius: 12px;
  font-weight: 500;
  z-index: 1;
  pointer-events: none;
}

.light-theme .gantt-percent {
  background: rgba(255, 255, 255, 0.8);
  color: #2563eb;
}

.gantt-dates {
  position: absolute;
  right: 10px;
  font-size: 0.85rem;
  color: var(--text-primary);
  background: rgba(0,0,0,0.5);
  padding: 2px 8px;
  border-radius: 12px;
  font-weight: 500;
}

.light-theme .gantt-dates {
  background: rgba(255,255,255,0.8);
  color: #1a3a1a;
}

.gantt-labels {
  display: flex;
  justify-content: space-between;
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-top: 5px;
}

.progress-breakdown {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 10px;
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.breakdown-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.breakdown-label {
  font-weight: 500;
}

.breakdown-value {
  font-weight: 600;
  color: var(--heading-color);
}

/* ---------- Подзадачи ---------- */
.subtasks-section {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 2px dashed var(--border-color);
}

.subtasks-section h3 {
  color: var(--heading-color);
  margin-bottom: 15px;
  font-weight: 500;
}

.subtasks-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.subtask-item {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 12px;
  transition: opacity 0.2s;
}

.subtask-item.completed {
  opacity: 0.6;
  background: var(--completed-bg);
}

.subtask-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.subtask-info input[type=checkbox] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--accent-color);
}

.subtask-title {
  flex: 1;
  color: var(--text-primary);
  font-weight: 500;
}

.subtask-percent {
  font-size: 0.9rem;
  color: var(--text-secondary);
  background: var(--bg-page);
  padding: 2px 8px;
  border-radius: 12px;
}

.subtask-description {
  margin-top: 8px;
  font-size: 0.9rem;
  color: var(--text-secondary);
  padding-left: 28px;
}

.subtasks-summary {
  margin-top: 10px;
  font-size: 0.9rem;
  color: var(--text-secondary);
  text-align: right;
}

/* ---------- Ползунок прогресса ---------- */
.progress-section {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 2px dashed var(--border-color);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.progress-section h3 {
  color: var(--heading-color);
  margin-bottom: 5px;
  font-weight: 500;
}

.progress-slider-container {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: center;
}

.progress-value {
  font-weight: 600;
  color: var(--heading-color);
  min-width: 40px;
}

.progress-max {
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.progress-slider {
  flex: 1;
  height: 8px;
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
  background: #3b82f6;
  border-radius: 4px;
  outline: none;
  transition: background 0.2s ease;
}

.progress-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  background: #3b82f6;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 6px var(--shadow);
  transition: background 0.2s ease;
  border: 2px solid white;
}

.progress-slider::-webkit-slider-thumb:hover {
  background: #2563eb;
}

.progress-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  background: #3b82f6;
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid white;
  transition: background 0.2s ease;
}

.progress-slider::-moz-range-thumb:hover {
  background: #2563eb;
}

.progress-slider::-moz-range-track {
  background: #3b82f6;
  height: 8px;
  border-radius: 4px;
}

.apply-progress-button {
  background: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 30px;
  padding: 10px 30px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
  box-shadow: var(--shadow);
  margin-top: 10px;
}

.apply-progress-button:hover {
  background: var(--accent-hover);
}

.progress-section-disabled {
  margin-top: 30px;
  padding: 15px;
  background: var(--bg-card);
  border-radius: 12px;
  text-align: center;
  border: 1px dashed var(--border-color);
}

.disabled-message {
  color: var(--text-secondary);
  font-size: 0.95rem;
}

/* ---------- Кнопки действий ---------- */
.action-buttons {
  margin-top: 30px;
  text-align: center;
}

.complete-button, .renew-button {
  background: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 30px;
  padding: 12px 30px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
  box-shadow: var(--shadow);
}

.complete-button:hover:not(:disabled), .renew-button:hover:not(:disabled) {
  background: var(--accent-hover);
}

.complete-button:disabled, .renew-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.renew-options {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

.status-option {
  padding: 10px 20px;
  border: none;
  border-radius: 30px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
  box-shadow: var(--shadow);
}

.status-option.work {
  background: var(--accent-color);
  color: var(--button-text);
}

.status-option.work:hover:not(:disabled) {
  background: var(--accent-hover);
}

.status-option.waiting {
  background: #ff9800;
  color: white;
}

.status-option.waiting:hover:not(:disabled) {
  background: #f57c00;
}

.status-option.cancel {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.status-option.cancel:hover:not(:disabled) {
  background: var(--bg-page);
}

.status-option:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.task-completed-info {
  display: inline-block;
  padding: 8px 16px;
  background: var(--completed-bg);
  color: var(--text-secondary);
  border-radius: 20px;
  font-size: 0.95rem;
}

/* ---------- Бейджики состояния ---------- */
.status-badges {
  margin-top: 20px;
  display: flex;
  gap: 10px;
  justify-content: center;
}

.badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: bold;
  color: white;
  box-shadow: var(--shadow);
}

.badge.overdue {
  background-color: #f44336;
}

.badge.urgent {
  background-color: #ff9800;
}

.badge.invalid {
  background-color: #9e9e9e;
}

/* ---------- Уведомления ---------- */
.notification {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 16px 24px;
  border-radius: 8px;
  color: white;
  font-weight: 500;
  box-shadow: var(--shadow-strong);
  z-index: 2000;
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 300px;
  max-width: 400px;
  backdrop-filter: blur(4px);
}

.notification.error {
  background-color: rgba(244, 67, 54, 0.9);
  border-left: 4px solid #d32f2f;
}

.notification.success {
  background-color: rgba(76, 175, 80, 0.9);
  border-left: 4px solid #388e3c;
}

.notification.info {
  background-color: rgba(33, 150, 243, 0.9);
  border-left: 4px solid #1976d2;
}

.notification-message {
  flex: 1;
}

.notification-close {
  background: none;
  border: none;
  color: white;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 4px;
  line-height: 1;
  opacity: 0.8;
  transition: opacity 0.2s;
}

.notification-close:hover {
  opacity: 1;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* ---------- Состояния загрузки ---------- */
.loading, .error {
  text-align: center;
  color: var(--text-primary);
  font-size: 1.2rem;
  padding: 40px;
}

/* ---------- Модальное окно ---------- */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: var(--overlay-bg);
  backdrop-filter: blur(3px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s;
}

.modal-content {
  background: var(--modal-bg);
  border-radius: 32px;
  padding: 30px;
  max-width: 400px;
  width: 90%;
  box-shadow: var(--shadow-strong);
  animation: slideUp 0.3s;
  color: var(--modal-text);
}

.modal-content h3 {
  color: var(--heading-color);
  margin-bottom: 15px;
  font-weight: 500;
  font-size: 1.5rem;
}

.modal-content p {
  color: var(--text-primary);
  margin-bottom: 25px;
  font-size: 1.1rem;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.modal-confirm, .modal-cancel {
  padding: 10px 25px;
  border: none;
  border-radius: 30px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.modal-confirm {
  background: var(--accent-color);
  color: var(--button-text);
}

.modal-confirm:hover {
  background: var(--accent-hover);
}

.modal-cancel {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.modal-cancel:hover {
  background: var(--bg-page);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
</style>