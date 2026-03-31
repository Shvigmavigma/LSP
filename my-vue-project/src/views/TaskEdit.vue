<template>
  <div class="task-edit-page">
    <!-- Уведомления -->
    <Transition name="fade">
      <div v-if="notification.show" class="notification" :class="notification.type">
        <span class="notification-message">{{ notification.message }}</span>
        <button class="notification-close" @click="closeNotification">✕</button>
      </div>
    </Transition>

    <header class="edit-header">
      <h1>{{ isNew ? $t('taskEdit.createTitle') : $t('taskEdit.editTitle') }}</h1>
      <div class="header-actions">
        <ThemeToggle />
        <LanguageSwitcher />
        <button class="home-button" @click="goHome" :title="$t('common.home')">🏠</button>
        <button class="back-button" @click="goBack" :title="$t('common.back')">◀</button>
      </div>
    </header>

    <!-- Информационная подсказка для админа/куратора -->
    <div v-if="isAdminOrCurator" class="admin-hint">
      <span class="hint-icon">⚙️</span>
      <span class="hint-text">{{ $t('taskEdit.adminHint') }}</span>
    </div>

    <div v-if="loading" class="loading">{{ $t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="!hasEditPermission" class="error">{{ $t('taskEdit.noEditPermission') }}</div>

    <div v-else class="edit-card">
      <form @submit.prevent="handleSubmit">
        <!-- Основная информация -->
        <div class="form-section">
          <h2>{{ $t('taskEdit.basicInfo') }}</h2>
          <div class="form-group">
            <label for="title">{{ $t('taskEdit.taskTitle') }}</label>
            <input id="title" v-model="form.title" type="text" required />
          </div>
          <div class="form-group">
            <label for="body">{{ $t('taskEdit.description') }}</label>
            <textarea id="body" v-model="form.body" rows="4" required></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="timeline">{{ $t('taskEdit.startDate') }}</label>
              <input
                id="timeline"
                :value="form.timeline"
                @input="updateTimeline"
                type="text"
                :placeholder="$t('taskEdit.datePlaceholder')"
                :class="{ 'invalid': timelineError }"
              />
              <span v-if="timelineError" class="error-message">{{ timelineError }}</span>
            </div>
            <div class="form-group">
              <label for="timelinend">{{ $t('taskEdit.endDate') }}</label>
              <input
                id="timelinend"
                :value="form.timelinend"
                @input="updateTimelinend"
                type="text"
                :placeholder="$t('taskEdit.datePlaceholder')"
                :class="{ 'invalid': timelinendError }"
              />
              <span v-if="timelinendError" class="error-message">{{ timelinendError }}</span>
            </div>
          </div>
        </div>

        <!-- Статус задачи -->
        <div class="form-section">
          <h2>{{ $t('taskEdit.taskStatus') }}</h2>
          <div class="status-selector">
            <label>{{ $t('taskEdit.currentStatus') }}: <strong>{{ getStatusText(form.status) }}</strong></label>
            <div class="status-buttons">
              <button
                type="button"
                class="status-btn"
                :class="{ active: form.status === 'в работе' }"
                @click="form.status = 'в работе'"
                :disabled="form.status === 'в работе'"
              >
                {{ $t('taskEdit.status.inProgress') }}
              </button>
              <button
                type="button"
                class="status-btn"
                :class="{ active: form.status === 'ожидает' }"
                @click="form.status = 'ожидает'"
                :disabled="form.status === 'ожидает'"
              >
                {{ $t('taskEdit.status.waiting') }}
              </button>
              <button
                type="button"
                class="status-btn"
                :class="{ active: form.status === 'выполнена' }"
                @click="form.status = 'выполнена'"
                :disabled="form.status === 'выполнена'"
              >
                {{ $t('taskEdit.status.completed') }}
              </button>
            </div>
          </div>
        </div>

        <!-- Подзадачи -->
        <div class="form-section">
          <div class="subtasks-header">
            <h2>{{ $t('taskEdit.subtasks') }}</h2>
            <button type="button" class="add-subtask-button" @click="addSubtask">+ {{ $t('taskEdit.addSubtask') }}</button>
          </div>

          <div v-if="subtasks.length === 0" class="no-subtasks">
            {{ $t('taskEdit.noSubtasks') }}
          </div>

          <div v-else class="subtasks-list">
            <div
              v-for="(subtask, index) in subtasks"
              :key="subtask.id"
              class="subtask-item"
            >
              <div class="subtask-header">
                <input
                  v-model="subtask.title"
                  :placeholder="$t('taskEdit.subtaskTitlePlaceholder')"
                  class="subtask-title-input"
                />
                <button
                  type="button"
                  class="remove-subtask"
                  @click="removeSubtask(index)"
                  :title="$t('common.delete')"
                >✕</button>
              </div>
              <textarea
                v-model="subtask.description"
                :placeholder="$t('taskEdit.subtaskDescriptionPlaceholder')"
                rows="2"
                class="subtask-description"
              ></textarea>
              <div class="subtask-percent">
                <label>{{ $t('taskEdit.percentOfTask') }}:</label>
                <input
                  type="number"
                  v-model.number="subtask.progressPercent"
                  min="0"
                  max="100"
                  step="1"
                />%
                <span class="percent-hint">({{ $t('taskEdit.sum') }}: {{ totalSubtasksPercent }}%)</span>
              </div>
              <div class="subtask-completed">
                <label>
                  <input type="checkbox" v-model="subtask.completed" />
                  {{ $t('taskEdit.completed') }}
                </label>
              </div>
            </div>
          </div>
          <div v-if="totalSubtasksPercent > 100" class="error-message">
            {{ $t('taskEdit.sumExceeds100', { sum: totalSubtasksPercent }) }}
          </div>
        </div>

        <!-- НОВОЕ: Обязательные файлы для завершения задачи -->
        <div class="form-section">
          <div class="required-files-header">
            <h2>{{ $t('taskEdit.requiredFiles') }}</h2>
            <button type="button" class="add-required-file" @click="addRequiredFile">
              + {{ $t('common.add') }}
            </button>
          </div>

          <div v-if="requiredFiles.length === 0" class="no-required-files">
            {{ $t('taskEdit.noRequiredFiles') }}
          </div>

          <div v-else class="required-files-list">
            <div v-for="(rf, idx) in requiredFiles" :key="rf.id" class="required-file-item">
              <div class="required-file-header">
                <input
                  v-model="rf.name"
                  :placeholder="$t('taskEdit.requiredFileName')"
                  class="required-file-name"
                />
                <button
                  type="button"
                  class="remove-required-file"
                  @click="removeRequiredFile(idx)"
                  :title="$t('common.delete')"
                >✕</button>
              </div>
              <textarea
                v-model="rf.description"
                :placeholder="$t('taskEdit.requiredFileDescription')"
                rows="2"
              ></textarea>
            </div>
          </div>
        </div>

        <!-- Старое поле "требуется файл" – скрыто, но оставлено для совместимости (можно удалить) -->
        <!-- <div class="form-section">
          <div class="form-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="form.requires_file" />
              {{ $t('taskEdit.requiresFile') }}
            </label>
          </div>
        </div> -->

        <!-- Кнопки сохранения -->
        <div class="form-actions">
          <button type="submit" class="save-button" :disabled="saving || totalSubtasksPercent > 100">
            {{ saving ? $t('common.saving') : $t('common.save') }}
          </button>
          <button type="button" class="cancel-button" @click="goBack">{{ $t('common.cancel') }}</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useProjectsStore } from '@/stores/projects';
import { useAuthStore } from '@/stores/auth';
import { useUsersStore } from '@/stores/users';
import ThemeToggle from '@/components/ThemeToggle.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';
import type { Project, Task, SubTask, ProjectRole, RequiredFile } from '@/types';
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';

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
const isNew = route.path.includes('/new');
const loading = ref(true);
const error = ref('');
const saving = ref(false);

const project = ref<Project | null>(null);
const originalTask = ref<Task | null>(null);

// Форма задачи
const form = reactive({
  title: '',
  body: '',
  timeline: '',
  timelinend: '',
  status: 'ожидает' as Task['status'],
  progress: 0,
  // requires_file: false,  // оставлено для совместимости, но не используется
});

// Подзадачи
interface EditableSubTask extends SubTask {}
const subtasks = ref<EditableSubTask[]>([]);

// Обязательные файлы
const requiredFiles = ref<RequiredFile[]>([]);

// Ошибки дат
const timelineError = ref('');
const timelinendError = ref('');

// Уведомления
const notification = ref({
  show: false,
  message: '',
  type: 'error' as 'error' | 'info' | 'success'
});

let notificationTimeout: number | null = null;

function showNotification(message: string, type: 'error' | 'info' | 'success' = 'error', duration = 5000) {
  if (notificationTimeout) {
    clearTimeout(notificationTimeout);
    notificationTimeout = null;
  }
  notification.value = { show: true, message, type };
  notificationTimeout = window.setTimeout(() => {
    notification.value.show = false;
    notificationTimeout = null;
  }, duration);
}

function closeNotification() {
  notification.value.show = false;
  if (notificationTimeout) {
    clearTimeout(notificationTimeout);
    notificationTimeout = null;
  }
}

// Является ли пользователь куратором (глобально) – исправлено
const isCurator = computed(() => {
  const user = authStore.user;
  if (!user) return false;
  if (!user.is_teacher) return false;
  return user.teacher_info?.curator ?? false;
});

// Является ли пользователь администратором или куратором – исправлено
const isAdminOrCurator = computed(() => (authStore.user?.is_admin ?? false) || isCurator.value);

// Право на редактирование задачи (заказчик, исполнитель, куратор в проекте, либо глобальный админ/куратор)
const hasEditPermission = computed(() => {
  if (!project.value) return false;
  // Глобальные права
  if (authStore.user?.is_admin || isCurator.value) return true;

  // Права в рамках проекта
  const participant = project.value.participants?.find(p => p.user_id === authStore.userId);
  const role = participant?.role;
  return role === 'customer' || role === 'executor' || role === 'curator';
});

// Форматирование даты (маска)
function formatDateInput(value: string): string {
  let digits = value.replace(/\D/g, '');
  if (digits.length > 8) digits = digits.slice(0, 8);
  let formatted = '';
  if (digits.length > 0) {
    formatted = digits.slice(0, 2);
    if (digits.length > 2) formatted += '.' + digits.slice(2, 4);
    if (digits.length > 4) formatted += '.' + digits.slice(4, 8);
  }
  return formatted;
}

function updateTimeline(e: Event) {
  const input = e.target as HTMLInputElement;
  form.timeline = formatDateInput(input.value);
  timelineError.value = '';
}

function updateTimelinend(e: Event) {
  const input = e.target as HTMLInputElement;
  form.timelinend = formatDateInput(input.value);
  timelinendError.value = '';
}

// Валидация даты
function parseDate(dateStr: string): Date | null {
  if (!dateStr) return null;
  const parts = dateStr.split('.');
  if (parts.length !== 3) return null;
  const [day, month, year] = parts.map(Number);
  if (isNaN(day) || isNaN(month) || isNaN(year)) return null;
  return new Date(year, month - 1, day);
}

function isValidDate(dateStr: string): boolean {
  if (!dateStr) return true;
  const parts = dateStr.split('.');
  if (parts.length !== 3) return false;
  const [day, month, year] = parts.map(Number);
  if (isNaN(day) || isNaN(month) || isNaN(year)) return false;
  if (day < 1 || day > 31 || month < 1 || month > 12 || year < 1000 || year > 9999) return false;
  const date = new Date(year, month - 1, day);
  return date.getDate() === day && date.getMonth() === month - 1 && date.getFullYear() === year;
}

// Сумма процентов подзадач
const totalSubtasksPercent = computed(() => {
  return subtasks.value.reduce((sum, st) => sum + (st.progressPercent || 0), 0);
});

// Перевод статуса
function getStatusText(status: string): string {
  const map: Record<string, string> = {
    'в работе': t('taskEdit.status.inProgress'),
    'ожидает': t('taskEdit.status.waiting'),
    'выполнена': t('taskEdit.status.completed'),
  };
  return map[status] || status;
}

// --- Работа с обязательными файлами ---
function addRequiredFile() {
  requiredFiles.value.push({
    id: uuidv4(),
    name: '',
    description: '',
  });
}

function removeRequiredFile(index: number) {
  requiredFiles.value.splice(index, 1);
}

// Загрузка данных
onMounted(async () => {
  if (isNaN(projectId)) {
    error.value = t('taskEdit.invalidProjectId');
    loading.value = false;
    return;
  }

  if (usersStore.users.length === 0) {
    await usersStore.fetchAllUsers();
  }

  try {
    project.value = await projectsStore.fetchProjectById(projectId);
    if (!project.value) {
      error.value = t('taskEdit.projectNotFound');
      return;
    }

    if (taskIndex < 0 || taskIndex >= (project.value.tasks?.length || 0)) {
      error.value = t('taskEdit.taskNotFound');
      return;
    }

    originalTask.value = project.value.tasks[taskIndex];
    if (originalTask.value) {
      form.title = originalTask.value.title;
      form.body = originalTask.value.body;
      form.timeline = originalTask.value.timeline || '';
      form.timelinend = originalTask.value.timelinend || '';
      form.status = originalTask.value.status || 'ожидает';
      form.progress = originalTask.value.progress || 0;
      // form.requires_file = originalTask.value.requires_file || false; // не используется

      subtasks.value = originalTask.value.subtasks?.map(st => ({ ...st })) || [];
      requiredFiles.value = originalTask.value.required_files ? [...originalTask.value.required_files] : [];
    }
  } catch (err) {
    console.error('Ошибка загрузки:', err);
    error.value = t('taskEdit.loadError');
  } finally {
    loading.value = false;
  }
});

// Добавление подзадачи
function addSubtask() {
  subtasks.value.push({
    id: generateId(),
    title: '',
    description: '',
    progressPercent: 0,
    completed: false,
  });
}

// Удаление подзадачи
function removeSubtask(index: number) {
  subtasks.value.splice(index, 1);
}

// Сохранение
async function handleSubmit() {
  if (!project.value || !originalTask.value) return;

  if (!form.title.trim()) {
    showNotification(t('taskEdit.taskTitleRequired'), 'info');
    return;
  }
  if (!form.body.trim()) {
    showNotification(t('taskEdit.taskDescriptionRequired'), 'info');
    return;
  }

  timelineError.value = '';
  timelinendError.value = '';
  let valid = true;

  if (!isValidDate(form.timeline || '')) {
    timelineError.value = t('taskEdit.invalidStartDate');
    valid = false;
  }
  if (!isValidDate(form.timelinend || '')) {
    timelinendError.value = t('taskEdit.invalidEndDate');
    valid = false;
  }

  if (!valid) return;

  if (form.timeline && form.timelinend) {
    const start = parseDate(form.timeline);
    const end = parseDate(form.timelinend);
    if (start && end && start > end) {
      showNotification(t('taskEdit.startBeforeEnd'), 'info');
      return;
    }
  }

  if (totalSubtasksPercent.value > 100) {
    showNotification(t('taskEdit.sumExceeds100', { sum: totalSubtasksPercent.value }), 'error');
    return;
  }

  saving.value = true;

  const updatedTask: Task = {
    title: form.title,
    body: form.body,
    timeline: form.timeline || undefined,
    timelinend: form.timelinend || undefined,
    status: form.status,
    subtasks: subtasks.value,
    progress: totalSubtasksPercent.value,
    required_files: requiredFiles.value,   // отправляем список обязательных файлов
    // requires_file: form.requires_file, // не используется
  };

  const updatedTasks = [...project.value.tasks];
  updatedTasks[taskIndex] = updatedTask;

  try {
    await projectsStore.updateProject(projectId, { tasks: updatedTasks });
    showNotification(t('taskEdit.saveSuccess'), 'success');
    setTimeout(() => {
      router.push(`/project/${projectId}/task/${taskIndex}`);
    }, 1000);
  } catch (err: any) {
    console.error('Ошибка сохранения задачи:', err);
    if (err.response?.status === 403) {
      showNotification(t('taskEdit.noEditPermission'), 'error');
    } else {
      showNotification(t('taskEdit.saveError'), 'error');
    }
  } finally {
    saving.value = false;
  }
}

// Навигация
const goBack = () => router.push(`/project/${projectId}/task/${taskIndex}`);
const goHome = () => router.push('/main');
</script>

<style scoped>
/* Копируем стили из ProjectEdit.vue и адаптируем */
.task-edit-page {
  min-height: 100vh;
  background: var(--bg-page);
  padding: 20px;
  box-sizing: border-box;
  transition: background 0.3s;
}

.edit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 800px;
  margin: 0 auto 20px;
}

.edit-header h1 {
  color: var(--heading-color);
  font-size: 2rem;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.home-button, .back-button {
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

.home-button:hover, .back-button:hover {
  background: rgba(255, 255, 255, 0.1);
}

.light-theme .home-button:hover,
.light-theme .back-button:hover {
  background: rgba(0, 0, 0, 0.05);
}

/* Подсказка для админа/куратора */
.admin-hint {
  max-width: 800px;
  margin: 0 auto 15px;
  padding: 10px 16px;
  background-color: rgba(255, 193, 7, 0.1);
  border-left: 4px solid #ffc107;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-primary);
  font-size: 0.95rem;
}

.hint-icon {
  font-size: 1.2rem;
}

.edit-card {
  background: var(--bg-card);
  border-radius: 32px;
  box-shadow: var(--shadow-strong);
  padding: 40px;
  max-width: 800px;
  margin: 0 auto;
  transition: background 0.3s;
}

.form-section {
  margin-bottom: 40px;
  padding-bottom: 20px;
  border-bottom: 2px dashed var(--border-color);
}

.form-section h2 {
  color: var(--heading-color);
  margin-bottom: 20px;
  font-weight: 500;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 6px;
  color: var(--text-secondary);
  font-weight: 500;
}

input, select, textarea {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s, box-shadow 0.2s;
  outline: none;
  box-sizing: border-box;
  font-family: inherit;
  background: var(--input-bg);
  color: var(--text-primary);
}

input:focus, select:focus, textarea:focus {
  border-color: var(--accent-color);
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.2);
}

.dark-theme input:focus,
.dark-theme select:focus,
.dark-theme textarea:focus {
  box-shadow: 0 0 0 3px rgba(1, 69, 172, 0.2);
}

input.invalid {
  border-color: var(--danger-color);
}

.error-message {
  display: block;
  margin-top: 4px;
  color: var(--danger-color);
  font-size: 0.85rem;
}

textarea {
  resize: vertical;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

/* Статус */
.status-selector {
  background: var(--bg-page);
  padding: 20px;
  border-radius: 12px;
}

.status-buttons {
  display: flex;
  gap: 15px;
  margin-top: 15px;
  flex-wrap: wrap;
}

.status-btn {
  flex: 1;
  min-width: 120px;
  padding: 12px 20px;
  border: 2px solid var(--border-color);
  border-radius: 30px;
  background: var(--bg-card);
  color: var(--text-primary);
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.status-btn.active {
  border-color: var(--accent-color);
  background: rgba(66, 185, 131, 0.1);
  color: var(--accent-color);
}

.status-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Подзадачи */
.subtasks-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.add-subtask-button {
  background: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 30px;
  padding: 8px 16px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.add-subtask-button:hover {
  background: var(--accent-hover);
}

.no-subtasks {
  text-align: center;
  color: var(--text-secondary);
  font-style: italic;
  padding: 30px;
  border: 1px dashed var(--border-color);
  border-radius: 12px;
}

.subtasks-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.subtask-item {
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px;
  background: var(--bg-card);
}

.subtask-header {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.subtask-title-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-primary);
}

.remove-subtask {
  background: none;
  border: none;
  color: var(--danger-color);
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0 8px;
}

.subtask-description {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-primary);
  margin-bottom: 10px;
  resize: vertical;
}

.subtask-percent {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.subtask-percent input {
  width: 80px;
  padding: 6px;
  border: 1px solid var(--input-border);
  border-radius: 6px;
  background: var(--input-bg);
  color: var(--text-primary);
}

.percent-hint {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.subtask-completed {
  margin-top: 8px;
}

.subtask-completed label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.subtask-completed input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: var(--accent-color);
}

/* НОВЫЕ СТИЛИ ДЛЯ ОБЯЗАТЕЛЬНЫХ ФАЙЛОВ */
.required-files-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.add-required-file {
  background: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 30px;
  padding: 8px 16px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.add-required-file:hover {
  background: var(--accent-hover);
}

.no-required-files {
  text-align: center;
  color: var(--text-secondary);
  font-style: italic;
  padding: 20px;
  border: 1px dashed var(--border-color);
  border-radius: 12px;
}

.required-files-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.required-file-item {
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px;
  background: var(--bg-card);
}

.required-file-header {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.required-file-name {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-primary);
}

.remove-required-file {
  background: none;
  border: none;
  color: var(--danger-color);
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0 8px;
}

/* Кнопки действий */
.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 40px;
}

.save-button, .cancel-button {
  flex: 1;
  padding: 14px;
  border: none;
  border-radius: 50px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.save-button {
  background-color: var(--accent-color);
  color: var(--button-text);
}

.save-button:hover:not(:disabled) {
  background-color: var(--accent-hover);
}

.save-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.cancel-button {
  background-color: var(--bg-page);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.cancel-button:hover {
  background-color: var(--bg-card);
}

.loading, .error {
  text-align: center;
  color: var(--text-primary);
  font-size: 1.2rem;
  padding: 40px;
}

/* Уведомления */
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
</style>