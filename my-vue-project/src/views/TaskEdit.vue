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
      <h1>{{ isNew ? 'Создание задачи' : 'Редактирование задачи' }}</h1>
      <div class="header-actions">
        <ThemeToggle />
        <button class="home-button" @click="goHome" title="На главную">🏠</button>
        <button class="back-button" @click="goBack" title="Вернуться к задаче">◀</button>
      </div>
    </header>

    <!-- Информационная подсказка для админа/куратора -->
    <div v-if="isAdminOrCurator" class="admin-hint">
      <span class="hint-icon">⚙️</span>
      <span class="hint-text">Вы имеете полные права как администратор или куратор.</span>
    </div>

    <div v-if="loading" class="loading">Загрузка...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="!hasEditPermission" class="error">У вас нет прав для редактирования этой задачи</div>

    <div v-else class="edit-card">
      <form @submit.prevent="handleSubmit">
        <!-- Основная информация -->
        <div class="form-section">
          <h2>Основная информация</h2>
          <div class="form-group">
            <label for="title">Название задачи</label>
            <input id="title" v-model="form.title" type="text" required />
          </div>
          <div class="form-group">
            <label for="body">Описание</label>
            <textarea id="body" v-model="form.body" rows="4" required></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="timeline">Дата начала (ДД.ММ.ГГГГ)</label>
              <input
                id="timeline"
                :value="form.timeline"
                @input="updateTimeline"
                type="text"
                placeholder="01.01.2025"
                :class="{ 'invalid': timelineError }"
              />
              <span v-if="timelineError" class="error-message">{{ timelineError }}</span>
            </div>
            <div class="form-group">
              <label for="timelinend">Дата окончания (ДД.ММ.ГГГГ)</label>
              <input
                id="timelinend"
                :value="form.timelinend"
                @input="updateTimelinend"
                type="text"
                placeholder="31.12.2025"
                :class="{ 'invalid': timelinendError }"
              />
              <span v-if="timelinendError" class="error-message">{{ timelinendError }}</span>
            </div>
          </div>
        </div>

        <!-- Статус задачи -->
        <div class="form-section">
          <h2>Статус задачи</h2>
          <div class="status-selector">
            <label>Текущий статус: <strong>{{ getStatusText(form.status) }}</strong></label>
            <div class="status-buttons">
              <button
                type="button"
                class="status-btn"
                :class="{ active: form.status === 'в работе' }"
                @click="form.status = 'в работе'"
                :disabled="form.status === 'в работе'"
              >
                В работе
              </button>
              <button
                type="button"
                class="status-btn"
                :class="{ active: form.status === 'ожидает' }"
                @click="form.status = 'ожидает'"
                :disabled="form.status === 'ожидает'"
              >
                Ожидает
              </button>
              <button
                type="button"
                class="status-btn"
                :class="{ active: form.status === 'выполнена' }"
                @click="form.status = 'выполнена'"
                :disabled="form.status === 'выполнена'"
              >
                Выполнена
              </button>
            </div>
          </div>
        </div>

        <!-- Подзадачи -->
        <div class="form-section">
          <div class="subtasks-header">
            <h2>Подзадачи</h2>
            <button type="button" class="add-subtask-button" @click="addSubtask">+ Добавить подзадачу</button>
          </div>

          <div v-if="subtasks.length === 0" class="no-subtasks">
            Нет подзадач. Добавьте подзадачи, чтобы распределить прогресс.
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
                  placeholder="Название подзадачи"
                  class="subtask-title-input"
                />
                <button
                  type="button"
                  class="remove-subtask"
                  @click="removeSubtask(index)"
                  title="Удалить подзадачу"
                >✕</button>
              </div>
              <textarea
                v-model="subtask.description"
                placeholder="Описание (необязательно)"
                rows="2"
                class="subtask-description"
              ></textarea>
              <div class="subtask-percent">
                <label>Процент от задачи:</label>
                <input
                  type="number"
                  v-model.number="subtask.progressPercent"
                  min="0"
                  max="100"
                  step="1"
                />%
                <span class="percent-hint">(сумма: {{ totalSubtasksPercent }}%)</span>
              </div>
              <div class="subtask-completed">
                <label>
                  <input type="checkbox" v-model="subtask.completed" />
                  Выполнено
                </label>
              </div>
            </div>
          </div>
          <div v-if="totalSubtasksPercent > 100" class="error-message">
            Сумма процентов подзадач не может превышать 100%! Текущая сумма: {{ totalSubtasksPercent }}%
          </div>
        </div>

        <!-- Кнопки сохранения -->
        <div class="form-actions">
          <button type="submit" class="save-button" :disabled="saving || totalSubtasksPercent > 100">
            {{ saving ? 'Сохранение...' : 'Сохранить' }}
          </button>
          <button type="button" class="cancel-button" @click="goBack">Отмена</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useProjectsStore } from '@/stores/projects';
import { useAuthStore } from '@/stores/auth';
import { useUsersStore } from '@/stores/users';
import ThemeToggle from '@/components/ThemeToggle.vue';
import type { Project, Task, SubTask, ProjectRole } from '@/types';
import axios from 'axios';

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
});

// Подзадачи
interface EditableSubTask extends SubTask {}
const subtasks = ref<EditableSubTask[]>([]);

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

// Является ли пользователь куратором (глобально)
const isCurator = computed(() => {
  return authStore.user?.is_teacher && authStore.user?.teacher_info?.curator === true;
});

// Является ли пользователь администратором или куратором
const isAdminOrCurator = computed(() => authStore.user?.is_admin || isCurator.value);

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
    'в работе': 'В работе',
    'ожидает': 'Ожидает',
    'выполнена': 'Выполнена',
  };
  return map[status] || status;
}

// Загрузка данных
onMounted(async () => {
  if (isNaN(projectId)) {
    error.value = 'Некорректный ID проекта';
    loading.value = false;
    return;
  }

  if (usersStore.users.length === 0) {
    await usersStore.fetchAllUsers();
  }

  try {
    project.value = await projectsStore.fetchProjectById(projectId);
    if (!project.value) {
      error.value = 'Проект не найден';
      return;
    }

    // Проверка прав (hasEditPermission computed обновится автоматически)
    // Если нет прав, покажем сообщение, но загрузку продолжим для отображения ошибки

    if (taskIndex < 0 || taskIndex >= (project.value.tasks?.length || 0)) {
      error.value = 'Задача не найдена';
      return;
    }

    originalTask.value = project.value.tasks[taskIndex];
    if (originalTask.value) {
      // Заполняем форму
      form.title = originalTask.value.title;
      form.body = originalTask.value.body;
      form.timeline = originalTask.value.timeline || '';
      form.timelinend = originalTask.value.timelinend || '';
      form.status = originalTask.value.status || 'ожидает';
      form.progress = originalTask.value.progress || 0;

      // Подзадачи
      subtasks.value = originalTask.value.subtasks?.map(st => ({ ...st })) || [];
    }
  } catch (err) {
    console.error('Ошибка загрузки:', err);
    error.value = 'Ошибка загрузки данных';
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

  // Валидация обязательных полей
  if (!form.title.trim()) {
    showNotification('Название задачи не может быть пустым', 'info');
    return;
  }
  if (!form.body.trim()) {
    showNotification('Описание задачи не может быть пустым', 'info');
    return;
  }

  // Валидация дат
  timelineError.value = '';
  timelinendError.value = '';
  let valid = true;

  if (!isValidDate(form.timeline || '')) {
    timelineError.value = 'Неверный формат даты начала';
    valid = false;
  }
  if (!isValidDate(form.timelinend || '')) {
    timelinendError.value = 'Неверный формат даты окончания';
    valid = false;
  }

  if (!valid) return;

  if (form.timeline && form.timelinend) {
    const start = parseDate(form.timeline);
    const end = parseDate(form.timelinend);
    if (start && end && start > end) {
      showNotification('Дата начала не может быть позже даты окончания', 'info');
      return;
    }
  }

  if (totalSubtasksPercent.value > 100) {
    showNotification(`Сумма процентов подзадач (${totalSubtasksPercent.value}%) не может превышать 100%`, 'error');
    return;
  }

  saving.value = true;

  // Собираем обновлённую задачу
  const updatedTask: Task = {
    title: form.title,
    body: form.body,
    timeline: form.timeline || undefined,
    timelinend: form.timelinend || undefined,
    status: form.status,
    subtasks: subtasks.value,
    progress: totalSubtasksPercent.value,
  };

  // Копируем массив задач
  const updatedTasks = [...project.value.tasks];
  updatedTasks[taskIndex] = updatedTask;

  try {
    await projectsStore.updateProject(projectId, { tasks: updatedTasks });
    showNotification('Задача успешно сохранена', 'success');
    setTimeout(() => {
      router.push(`/project/${projectId}/task/${taskIndex}`);
    }, 1000);
  } catch (err: any) {
    console.error('Ошибка сохранения задачи:', err);
    if (err.response?.status === 403) {
      showNotification('У вас недостаточно прав для редактирования задачи', 'error');
    } else {
      showNotification('Не удалось сохранить задачу', 'error');
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