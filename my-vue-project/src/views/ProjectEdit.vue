<template>
  <div class="project-edit-page">
    <!-- Уведомление об ошибке/информации -->
    <Transition name="fade">
      <div v-if="notification.show" class="notification" :class="notification.type">
        <span class="notification-message">{{ notification.message }}</span>
        <button class="notification-close" @click="closeNotification">✕</button>
      </div>
    </Transition>

    <header class="edit-header">
      <h1>{{ pageTitle }}</h1>
      <div class="header-actions">
        <ThemeToggle />
        <button class="home-button" @click="goHome" title="На главную">🏠</button>
      </div>
    </header>

    <!-- Информационная подсказка о правах -->
    <div v-if="!isNew" class="permission-hint" :class="{ 'admin-hint': isAdminOrCurator }">
      <span class="hint-icon">{{ isAdminOrCurator ? '⚙️' : 'ℹ️' }}</span>
      <span class="hint-text">
        <template v-if="isAdminOrCurator">
          Вы имеете полные права как администратор или куратор.
        </template>
        <template v-else>
          Редактировать проект могут только заказчик, исполнитель, администратор или куратор.
        </template>
      </span>
    </div>

    <div class="edit-card">
      <form @submit.prevent="handleSubmit">
        <!-- Основная информация -->
        <div class="form-section">
          <h2>Основная информация</h2>
          <div class="form-group">
            <label for="title">Название проекта</label>
            <input id="title" v-model="form.title" type="text" required />
          </div>
          <div class="form-group">
            <label for="body">Описание</label>
            <textarea id="body" v-model="form.body" rows="4" required></textarea>
          </div>
          <div class="form-group">
            <label for="underbody">Дополнительная информация</label>
            <textarea id="underbody" v-model="form.underbody" rows="2"></textarea>
          </div>
        </div>

        <!-- Участники проекта -->
        <div class="form-section">
          <h2>Участники проекта</h2>
          <div class="participants-section">
            <div v-if="participants.length > 0" class="current-participants">
              <span class="participants-label">Текущие участники:</span>
              <div class="participant-tags">
                <div
                  v-for="(p, index) in participants"
                  :key="p.user_id"
                  class="participant-tag"
                >
                  <div class="participant-info">
                    <span class="participant-name">{{ getUserNickname(p.user_id) }}</span>
                    <span class="participant-role">{{ getRoleDisplay(p.role) }}</span>
                  </div>
                  <button
                    type="button"
                    class="remove-participant"
                    @click="removeParticipant(index)"
                    :disabled="p.user_id === currentUserId || participants.length === 1"
                    :title="getRemoveTitle(p.user_id)"
                  >✕</button>
                </div>
              </div>
            </div>

            <div class="participant-search">
              <label>Добавить участника по никнейму</label>
              <div class="search-row">
                <input
                  v-model="searchQuery"
                  type="text"
                  placeholder="Введите никнейм..."
                  @input="searchUsers"
                />
                <select v-model="selectedRole">
                  <option v-for="role in availableRolesForSelected" :key="role" :value="role">
                    {{ getRoleDisplay(role) }}
                  </option>
                </select>
                <button @click="addParticipant" :disabled="!selectedUser">Добавить</button>
              </div>
              <div v-if="searchResults.length > 0" class="search-results">
                <div
                  v-for="user in searchResults"
                  :key="user.id"
                  class="search-result-item"
                  @click="selectUser(user)"
                >
                  {{ user.nickname }} ({{ user.fullname }})
                  <span class="user-roles-hint">({{ getUserRolesHint(user) }})</span>
                </div>
              </div>
            </div>
            <div v-if="isSuggestMode" class="suggest-note">
              <p>⚠️ В режиме предложения вы можете изменять любые поля – они будут отправлены как предложение.</p>
            </div>
            <div v-if="isApplyingSuggestion" class="suggest-note">
              <p>📝 Вы редактируете проект на основе предложения. После сохранения предложение будет автоматически принято.</p>
            </div>
          </div>
        </div>

        <!-- Приглашение по email (только для существующих проектов) -->
        <div v-if="isEdit" class="form-section">
          <h2>Пригласить участника по email</h2>
          <div class="invite-section">
            <div class="invite-row">
              <input
                v-model="inviteEmail"
                type="email"
                placeholder="Email пользователя"
                class="invite-input"
              />
              <select v-model="inviteRole">
                <option value="executor">Исполнитель</option>
                <option value="customer">Заказчик</option>
                <option value="supervisor">Научный руководитель</option>
                <option value="expert">Эксперт</option>
                <option value="curator">Куратор</option>
              </select>
              <button @click="sendInvite" :disabled="!inviteEmail || sendingInvite">
                {{ sendingInvite ? 'Отправка...' : 'Отправить приглашение' }}
              </button>
            </div>
            <div v-if="inviteResult" class="invite-result" :class="{ success: inviteSuccess, error: !inviteSuccess }">
              {{ inviteResult }}
            </div>
          </div>
        </div>

        <!-- Задачи -->
        <div class="form-section">
          <div class="tasks-header">
            <h2>Задачи проекта</h2>
            <div class="task-buttons">
              <button type="button" class="add-task-button" @click="addTask">+ Добавить задачу</button>
              <button type="button" class="add-default-tasks-button" @click="addDefaultTasks">📋 Добавить дефолтные задачи</button>
            </div>
          </div>

          <div v-if="tasks.length === 0" class="no-tasks">
            Пока нет задач. Нажмите "Добавить задачу", чтобы создать первую.
          </div>

          <div v-else class="tasks-list">
            <div
              v-for="(task, index) in tasks"
              :key="index"
              class="task-item"
              :class="{ 'expanded': task.expanded }"
            >
              <!-- Компактное отображение задачи -->
              <div v-if="!task.expanded" class="task-compact" @click="toggleTaskExpand(index)">
                <span class="task-title">{{ task.title || 'Без названия' }}</span>
                <button
                  type="button"
                  class="delete-task-button"
                  @click.stop="removeTask(index)"
                  title="Удалить задачу"
                >✕</button>
              </div>

              <!-- Развёрнутая форма задачи -->
              <div v-else class="task-form">
                <div class="task-form-header">
                  <h3>{{ task.id ? 'Редактирование задачи' : 'Новая задача' }}</h3>
                  <button type="button" class="close-task-form" @click="toggleTaskExpand(index)">✕</button>
                </div>

                <div class="form-group">
                  <label :for="'task-title-'+index">Название задачи</label>
                  <input :id="'task-title-'+index" v-model="task.title" type="text" required />
                </div>

                <div class="form-group">
                  <label :for="'task-status-'+index">Статус</label>
                  <select :id="'task-status-'+index" v-model="task.status">
                    <option value="в работе">В работе</option>
                    <option value="ожидает">Ожидает</option>
                    <option value="выполнена">Выполнена</option>
                  </select>
                </div>

                <div class="form-group">
                  <label :for="'task-body-'+index">Описание задачи</label>
                  <textarea :id="'task-body-'+index" v-model="task.body" rows="2" required></textarea>
                </div>

                <div class="form-row">
                  <div class="form-group">
                    <label :for="'task-start-'+index">Дата начала (ДД.ММ.ГГГГ)</label>
                    <input
                      :id="'task-start-'+index"
                      :value="task.timeline"
                      @input="updateTaskDate(index, 'timeline', $event)"
                      type="text"
                      placeholder="01.01.2025"
                      :class="{ 'invalid': task.startError }"
                    />
                    <span v-if="task.startError" class="error-message">{{ task.startError }}</span>
                  </div>

                  <div class="form-group">
                    <label :for="'task-end-'+index">Дата окончания (ДД.ММ.ГГГГ)</label>
                    <input
                      :id="'task-end-'+index"
                      :value="task.timelinend"
                      @input="updateTaskDate(index, 'timelinend', $event)"
                      type="text"
                      placeholder="31.12.2025"
                      :class="{ 'invalid': task.endError }"
                    />
                    <span v-if="task.endError" class="error-message">{{ task.endError }}</span>
                  </div>
                </div>

                <div class="task-form-actions">
                  <button type="button" class="save-task-button" @click="saveTask(index)">✓ Готово</button>
                  <button type="button" class="cancel-task-button" @click="toggleTaskExpand(index)">Отмена</button>
                </div>
              </div>
            </div>
          </div>
          <div v-if="isSuggestMode" class="suggest-note">
            <p>⚠️ В режиме предложения вы можете изменять задачи, они будут включены в предложение как есть.</p>
          </div>
          <div v-if="isApplyingSuggestion" class="suggest-note">
            <p>📝 Вы редактируете задачи на основе предложения. После сохранения предложение будет автоматически принято.</p>
          </div>
        </div>

        <!-- Кнопки отправки -->
        <div class="form-actions">
          <button type="submit" class="save-button" :disabled="saving">
            {{ saving ? (isSuggestMode ? 'Отправка...' : (isApplyingSuggestion ? 'Принять и сохранить...' : 'Сохранение...')) : submitButtonText }}
          </button>
          <button type="button" class="cancel-button" @click="goBack">{{ cancelButtonText }}</button>
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
import type { Project, Task, User, Participant, ProjectRole, Suggestion } from '@/types';
import axios from 'axios';

const baseUrl = 'http://localhost:8000';

const route = useRoute();
const router = useRouter();
const projectsStore = useProjectsStore();
const authStore = useAuthStore();
const usersStore = useUsersStore();

const projectId = Number(route.params.id);
const isNew = route.params.id === 'new';
const isEdit = computed(() => !isNew);
const isSuggestMode = ref(false);
const isApplyingSuggestion = ref(false);
const applyingSuggestionId = ref<string | null>(null);

const saving = ref(false);

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

// Форма проекта
const form = reactive({
  title: '',
  body: '',
  underbody: '',
});

// Участники
const participants = ref<Participant[]>([]);

// Текущий пользователь
const currentUserId = computed(() => authStore.user?.id);

// Является ли пользователь куратором (глобально)
const isCurator = computed(() => {
  return authStore.user?.is_teacher && authStore.user?.teacher_info?.curator === true;
});

// Является ли пользователь администратором или куратором
const isAdminOrCurator = computed(() => authStore.user?.is_admin || isCurator.value);

// Определение роли создателя проекта
function getCreatorRole(): ProjectRole {
  const user = authStore.user;
  if (!user) return 'executor';
  if (!user.is_teacher) return 'executor';
  // Учитель
  if (user.teacher_info) {
    if (user.teacher_info.roles?.includes('customer')) return 'customer';
    if (user.teacher_info.curator) return 'curator';
    if (user.teacher_info.roles?.includes('supervisor')) return 'supervisor';
    if (user.teacher_info.roles?.includes('expert')) return 'expert';
  }
  return 'executor';
}

// Поиск пользователей
interface UserWithRoles extends User {
  availableRoles: ProjectRole[];
}

const searchQuery = ref('');
const searchResults = ref<UserWithRoles[]>([]);
const selectedUser = ref<UserWithRoles | null>(null);
const selectedRole = ref<ProjectRole>('executor');

// Приглашение
const inviteEmail = ref('');
const inviteRole = ref<ProjectRole>('executor');
const sendingInvite = ref(false);
const inviteResult = ref('');
const inviteSuccess = ref(false);

// Задачи – расширяем Task служебными полями для UI
type EditableTask = Task & {
  expanded: boolean;
  startError?: string;
  endError?: string;
};

const tasks = ref<EditableTask[]>([]);

// --- Дефолтные задачи (пользователь может отредактировать этот массив) ---
const defaultTasks = ref<Partial<Task>[]>([
  {
    title: 'Исследование',
    body: 'Провести предварительное исследование',
    status: 'ожидает',
    timeline: '01.01.2025',
    timelinend: '15.01.2025',
  },
  {
    title: 'Прототипирование',
    body: 'Создать прототип',
    status: 'ожидает',
    timeline: '16.01.2025',
    timelinend: '31.01.2025',
  },
  {
    title: 'Тестирование',
    body: 'Провести тестирование',
    status: 'ожидает',
    timeline: '01.02.2025',
    timelinend: '15.02.2025',
  },
]);

// Роль текущего пользователя в проекте
const userRole = ref<ProjectRole | null>(null);

// Право предлагать изменения (с учётом админа и куратора)
const canSuggest = computed(() =>
  userRole.value === 'expert' ||
  userRole.value === 'supervisor' ||
  userRole.value === 'executor' ||
  authStore.user?.is_admin ||
  isCurator.value
);

// Право на прямое редактирование проекта (с учётом админа и куратора)
const canEdit = computed(() => 
  userRole.value === 'customer' || 
  userRole.value === 'executor' || 
  authStore.user?.is_admin || 
  isCurator.value
);

const pageTitle = computed(() => {
  if (isNew) return 'Создание нового проекта';
  if (isApplyingSuggestion.value) return 'Применить предложение';
  return isSuggestMode.value ? 'Предложить изменения проекта' : 'Редактирование проекта';
});

const submitButtonText = computed(() => {
  if (isNew) return 'Создать проект';
  if (isApplyingSuggestion.value) return 'Принять и сохранить';
  return isSuggestMode.value ? 'Отправить предложение' : 'Сохранить изменения';
});

const cancelButtonText = computed(() => 'Отмена');

// Получение доступных ролей для пользователя
function getAvailableRoles(user: User): ProjectRole[] {
  if (!user.is_teacher) {
    return ['executor'];
  }
  const teacherRoles = (user.teacher_info?.roles || []) as ProjectRole[];
  // Добавляем executor как всегда доступный
  if (!teacherRoles.includes('executor')) {
    teacherRoles.push('executor');
  }
  // Добавляем curator, если есть флаг
  if (user.teacher_info?.curator && !teacherRoles.includes('curator')) {
    teacherRoles.push('curator');
  }
  return teacherRoles;
}

// Поиск пользователей
function searchUsers() {
  if (!searchQuery.value.trim()) {
    searchResults.value = [];
    return;
  }
  const q = searchQuery.value.toLowerCase();
  const allUsers = usersStore.users.filter(u =>
    u.nickname.toLowerCase().includes(q) &&
    !participants.value.some(p => p.user_id === u.id)
  );
  searchResults.value = allUsers.map(user => ({
    ...user,
    availableRoles: getAvailableRoles(user)
  })).slice(0, 10);
}

function selectUser(user: UserWithRoles) {
  selectedUser.value = user;
  searchQuery.value = user.nickname;
  searchResults.value = [];
  // Устанавливаем роль по умолчанию – первую доступную
  selectedRole.value = user.availableRoles[0];
}

// Доступные роли для выбранного пользователя
const availableRolesForSelected = computed(() => {
  if (!selectedUser.value) return [];
  return selectedUser.value.availableRoles;
});

// Подсказка о доступных ролях для отображения в результатах поиска
function getUserRolesHint(user: UserWithRoles): string {
  return user.availableRoles.map(r => getRoleDisplay(r)).join(', ');
}

function addParticipant() {
  if (!selectedUser.value) return;
  participants.value.push({
    user_id: selectedUser.value.id,
    role: selectedRole.value,
    joined_at: new Date().toISOString(),
  });
  selectedUser.value = null;
  searchQuery.value = '';
  selectedRole.value = 'executor';
}

function removeParticipant(index: number) {
  const participant = participants.value[index];
  // Запрещаем удалять самого себя (кроме админа/куратора – они могут?)
  if (!isAdminOrCurator.value && participant.user_id === currentUserId.value) {
    showNotification('Вы не можете удалить себя из проекта', 'info');
    return;
  }
  if (participants.value.length === 1) {
    showNotification('Проект должен иметь хотя бы одного участника', 'info');
    return;
  }
  participants.value.splice(index, 1);
}

function getRemoveTitle(userId: number): string {
  if (!isAdminOrCurator.value && userId === currentUserId.value) return 'Нельзя удалить себя';
  if (participants.value.length === 1) return 'Нельзя удалить единственного участника';
  return 'Удалить';
}

// Загрузка данных
onMounted(async () => {
  if (usersStore.users.length === 0) {
    await usersStore.fetchAllUsers();
  }

  // Проверяем query-параметр suggestion
  const suggestionParam = route.query.suggestion as string | undefined;
  if (suggestionParam && !isNew) {
    isApplyingSuggestion.value = true;
    applyingSuggestionId.value = suggestionParam;
  }

  if (!isNew) {
    if (isNaN(projectId)) {
      router.push('/main');
      return;
    }
    const project = await projectsStore.fetchProjectById(projectId);
    if (!project) {
      router.push('/main');
      return;
    }

    const participant = project.participants?.find(p => p.user_id === authStore.userId);
    userRole.value = participant?.role || null;

    // Если мы в режиме применения предложения, загружаем предложение
    if (isApplyingSuggestion.value && applyingSuggestionId.value) {
      const suggestion = project.suggestions?.find(s => s.id === applyingSuggestionId.value);
      if (!suggestion) {
        showNotification('Предложение не найдено', 'error');
        router.push(`/project/${projectId}`);
        return;
      }
      // Применяем изменения из предложения к форме
      applySuggestionChanges(suggestion);
    } else {
      // Обычный режим – проверяем права
      const modeParam = route.query.mode;
      if (modeParam === 'suggest') {
        // Для режима предложения достаточно прав canSuggest
        if (!canSuggest.value) {
          showNotification('У вас нет прав для создания предложения', 'error');
          setTimeout(() => router.push(`/project/${projectId}`), 2000);
          return;
        }
        isSuggestMode.value = true;
      } else {
        // Для обычного редактирования проверяем canEdit
        if (!canEdit.value) {
          showNotification('У вас нет прав для редактирования проекта. Только заказчик, исполнитель, администратор или куратор могут редактировать.', 'info');
          setTimeout(() => router.push(`/project/${projectId}`), 2000);
          return;
        }
        isSuggestMode.value = false;
      }

      // Заполняем форму текущими данными проекта
      form.title = project.title;
      form.body = project.body;
      form.underbody = project.underbody || '';
      participants.value = project.participants || [];
      tasks.value = (project.tasks || []).map(task => ({
        ...task,
        expanded: false,
        startError: undefined,
        endError: undefined,
      }));
    }
  } else {
    // Новый проект: добавляем текущего пользователя с его ролью
    isSuggestMode.value = false;
    isApplyingSuggestion.value = false;
    if (authStore.userId) {
      const creatorRole = getCreatorRole();
      participants.value.push({
        user_id: authStore.userId,
        role: creatorRole,
        joined_at: new Date().toISOString(),
      });
    }
  }
});

// Применение изменений из предложения
function applySuggestionChanges(suggestion: Suggestion) {
  const changes = suggestion.changes;
  if (changes.title) form.title = changes.title;
  if (changes.body) form.body = changes.body;
  if (changes.underbody) form.underbody = changes.underbody;
  if (changes.participants) participants.value = changes.participants;
  if (changes.tasks) {
    tasks.value = changes.tasks.map((task: any) => ({
      ...task,
      expanded: false,
      startError: undefined,
      endError: undefined,
    }));
  }
}

function getUserNickname(id: number): string {
  const user = usersStore.users.find(u => u.id === id);
  return user ? user.nickname : `ID: ${id}`;
}

function getRoleDisplay(role: ProjectRole): string {
  const map: Record<ProjectRole, string> = {
    customer: 'Заказчик',
    supervisor: 'Научный руководитель',
    expert: 'Эксперт',
    executor: 'Исполнитель',
    curator: 'Куратор',
  };
  return map[role];
}

async function sendInvite() {
  if (!inviteEmail.value || !isEdit.value) return;
  sendingInvite.value = true;
  inviteResult.value = '';
  inviteSuccess.value = false;

  try {
    const response = await axios.post(`${baseUrl}/projects/${projectId}/invite`, {
      email: inviteEmail.value,
      role: inviteRole.value,
    });
    inviteResult.value = `Приглашение создано! Токен: ${response.data.token}`;
    inviteSuccess.value = true;
    inviteEmail.value = '';
    showNotification('Приглашение успешно создано', 'success');
  } catch (error: any) {
    console.error('Failed to create invite:', error);
    const msg = error.response?.data?.detail || 'Ошибка при создании приглашения';
    inviteResult.value = msg;
    inviteSuccess.value = false;
    showNotification(msg, 'error');
  } finally {
    sendingInvite.value = false;
  }
}

// --- Функции для задач ---
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

function updateTaskDate(index: number, field: 'timeline' | 'timelinend', event: Event) {
  const task = tasks.value[index];
  if (!task) return;
  const input = event.target as HTMLInputElement;
  const formatted = formatDateInput(input.value);
  task[field] = formatted;
  if (field === 'timeline') task.startError = undefined;
  else task.endError = undefined;
}

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

function addTask() {
  tasks.value.push({
    title: '',
    status: 'ожидает',
    body: '',
    timeline: '',
    timelinend: '',
    expanded: true,
    startError: undefined,
    endError: undefined,
  });
}

// Добавление дефолтных задач
function addDefaultTasks() {
  defaultTasks.value.forEach(task => {
    const newTask: EditableTask = {
      title: task.title || 'Новая задача',
      body: task.body || '',
      status: task.status || 'ожидает',
      timeline: task.timeline || '',
      timelinend: task.timelinend || '',
      progress: task.progress,
      subtasks: task.subtasks,
      comments: task.comments,
      assigned_to: task.assigned_to,
      id: task.id,
      expanded: false,
      startError: undefined,
      endError: undefined,
    };
    tasks.value.push(newTask);
  });
  showNotification(`Добавлено ${defaultTasks.value.length} дефолтных задач`, 'success');
}

function saveTask(index: number) {
  const task = tasks.value[index];
  if (!task) return;
  if (!task.title.trim()) { showNotification('Название задачи не может быть пустым', 'info'); return; }
  if (!task.body.trim()) { showNotification('Описание задачи не может быть пустым', 'info'); return; }

  task.startError = undefined;
  task.endError = undefined;
  let valid = true;

  if (!isValidDate(task.timeline || '')) {
    task.startError = 'Неверный формат даты начала';
    valid = false;
  }
  if (!isValidDate(task.timelinend || '')) {
    task.endError = 'Неверный формат даты окончания';
    valid = false;
  }

  if (!valid) return;

  if (task.timeline && task.timelinend) {
    const start = parseDate(task.timeline);
    const end = parseDate(task.timelinend);
    if (start && end && start > end) {
      showNotification('Дата начала не может быть позже даты окончания', 'info');
      return;
    }
  }

  task.expanded = false;
}

function removeTask(index: number) {
  tasks.value.splice(index, 1);
}

function toggleTaskExpand(index: number) {
  tasks.value[index].expanded = !tasks.value[index].expanded;
}

// Сохранение / отправка предложения
async function handleSubmit() {
  if (!form.title.trim() || !form.body.trim()) {
    showNotification('Заполните название и описание проекта', 'info');
    return;
  }

  for (let i = 0; i < tasks.value.length; i++) {
    if (tasks.value[i]?.expanded) {
      showNotification('Завершите редактирование всех задач перед сохранением', 'info');
      return;
    }
  }

  if (participants.value.length === 0 && !isNew) {
    showNotification('Проект должен иметь хотя бы одного участника', 'info');
    return;
  }

  const projectData = {
    title: form.title,
    body: form.body,
    underbody: form.underbody || '',
    participants: participants.value,
    tasks: tasks.value.map(({ expanded, startError, endError, id, ...task }) => task), // id исключается
  };

  saving.value = true;

  try {
    // Если мы в режиме применения предложения, сначала принимаем предложение
    if (isApplyingSuggestion.value && applyingSuggestionId.value) {
      await axios.put(`${baseUrl}/projects/${projectId}/suggestions/${applyingSuggestionId.value}/accept`);
      showNotification('Предложение принято', 'success');
    }

    if (isNew) {
      if (!authStore.userId) throw new Error('Пользователь не авторизован');
      // Убедимся, что текущий пользователь уже есть в participants (должен быть добавлен при монтировании)
      if (!participants.value.some(p => p.user_id === authStore.userId)) {
        // На случай, если по какой-то причине его нет – добавляем
        const defaultRole = getCreatorRole();
        projectData.participants.push({
          user_id: authStore.userId,
          role: defaultRole,
          joined_at: new Date().toISOString(),
        });
      }
      const created = await projectsStore.createProject(projectData);
      showNotification('Проект успешно создан', 'success');
      router.push(`/project/${created.id}`);
    } else if (isSuggestMode.value) {
      const suggestionData = {
        target_type: 'project',
        changes: projectData,
      };
      await axios.post(`${baseUrl}/projects/${projectId}/suggestions`, suggestionData);
      showNotification('Предложение отправлено!', 'success');
      setTimeout(() => router.push(`/project/${projectId}`), 1500);
    } else {
      await projectsStore.updateProject(projectId, projectData);
      showNotification('Изменения сохранены', 'success');
      setTimeout(() => router.push(`/project/${projectId}`), 1500);
    }
  } catch (err: any) {
    console.error('Ошибка сохранения проекта:', err);
    if (err.response?.status === 403) {
      showNotification('У вас недостаточно прав. Только заказчик, исполнитель, администратор или куратор могут редактировать проект.', 'error');
    } else {
      showNotification('Не удалось сохранить изменения. Пожалуйста, попробуйте позже.', 'error');
    }
  } finally {
    saving.value = false;
  }
}

const goHome = () => router.push('/main');
const goBack = () => router.go(-1);
</script>

<style scoped>
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

/* Подсказка о правах */
.permission-hint {
  max-width: 800px;
  margin: 0 auto 15px;
  padding: 10px 16px;
  background-color: rgba(33, 150, 243, 0.1);
  border-left: 4px solid #2196f3;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-primary);
  font-size: 0.95rem;
}

.permission-hint.admin-hint {
  background-color: rgba(255, 193, 7, 0.1);
  border-left-color: #ffc107;
}

.hint-icon {
  font-size: 1.2rem;
}

/* Остальные стили */
.invite-section {
  display: flex;
  flex-direction: column;
  gap: 15px;
}
.invite-row {
  display: flex;
  gap: 10px;
  align-items: center;
}
.invite-input {
  flex: 2;
  padding: 10px 12px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-primary);
}
.invite-row select {
  flex: 1;
  padding: 10px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-primary);
}
.invite-row button {
  flex: 1;
  padding: 10px 16px;
  background: var(--accent-color);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}
.invite-row button:hover:not(:disabled) {
  background: var(--accent-hover);
}
.invite-row button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.invite-result {
  padding: 10px;
  border-radius: 8px;
  font-size: 0.9rem;
}
.invite-result.success {
  background: rgba(76, 175, 80, 0.1);
  color: #4caf50;
  border: 1px solid #4caf50;
}
.invite-result.error {
  background: rgba(244, 67, 54, 0.1);
  color: #f44336;
  border: 1px solid #f44336;
}
.participants-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.current-participants {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}
.participants-label {
  font-weight: 500;
  color: var(--text-secondary);
}
.participant-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.participant-tag {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  padding: 6px 12px;
  border-radius: 30px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.participant-info {
  display: flex;
  gap: 6px;
  align-items: baseline;
}
.participant-name {
  font-weight: 500;
  color: var(--text-primary);
}
.participant-role {
  font-size: 0.85rem;
  color: var(--accent-color);
  background: rgba(66, 185, 131, 0.1);
  padding: 2px 8px;
  border-radius: 12px;
}
.remove-participant {
  background: none;
  border: none;
  color: var(--danger-color);
  font-size: 1.1rem;
  cursor: pointer;
  padding: 0 4px;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.remove-participant:hover:not(:disabled) {
  background: var(--danger-bg);
}
.remove-participant:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
.search-row {
  display: flex;
  gap: 10px;
  margin-top: 8px;
}
.search-row select {
  padding: 8px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-primary);
}
.search-row button {
  padding: 8px 16px;
  background: var(--accent-color);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}
.search-results {
  position: absolute;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  margin-top: 4px;
  max-height: 200px;
  overflow-y: auto;
  z-index: 10;
}
.search-result-item {
  padding: 8px 12px;
  cursor: pointer;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.search-result-item:hover {
  background: var(--bg-page);
}
.user-roles-hint {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-left: 8px;
}
.project-edit-page {
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
.home-button {
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
.home-button:hover {
  background: rgba(255, 255, 255, 0.1);
}
.light-theme .home-button:hover {
  background: rgba(0, 0, 0, 0.05);
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
.tasks-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.task-buttons {
  display: flex;
  gap: 10px;
}
.add-task-button,
.add-default-tasks-button {
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
.add-default-tasks-button {
  background: #ff9800;
}
.add-default-tasks-button:hover {
  background: #f57c00;
}
.add-task-button:hover {
  background: var(--accent-hover);
}
.add-task-button:disabled,
.add-default-tasks-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.no-tasks {
  text-align: center;
  color: var(--text-secondary);
  font-style: italic;
  padding: 20px;
  background: var(--bg-page);
  border-radius: 12px;
}
.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.task-item {
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background: var(--bg-card);
  transition: all 0.2s;
}
.task-item.expanded {
  border-color: var(--accent-color);
  box-shadow: var(--shadow);
}
.task-compact {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  border-radius: 12px;
}
.task-compact:hover {
  background: var(--bg-page);
}
.task-title {
  font-weight: 500;
  color: var(--text-primary);
  overflow-wrap: break-word;
  word-wrap: break-word;
  hyphens: auto;
}
.delete-task-button {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: var(--danger-color);
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}
.delete-task-button:hover:not(:disabled) {
  background: var(--danger-bg);
}
.delete-task-button:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
.task-form {
  padding: 20px;
  border-top: 1px solid var(--border-color);
}
.task-form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.task-form-header h3 {
  color: var(--heading-color);
  margin: 0;
  font-weight: 500;
}
.close-task-form {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--text-secondary);
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}
.close-task-form:hover {
  background: var(--bg-page);
}
.task-form-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}
.save-task-button, .cancel-task-button {
  flex: 1;
  padding: 10px;
  border: none;
  border-radius: 30px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.save-task-button {
  background: var(--accent-color);
  color: var(--button-text);
}
.save-task-button:hover:not(:disabled) {
  background: var(--accent-hover);
}
.save-task-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.cancel-task-button {
  background: var(--bg-page);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}
.cancel-task-button:hover {
  background: var(--bg-card);
}
.suggest-note {
  margin-top: 15px;
  padding: 10px;
  background: rgba(255, 152, 0, 0.1);
  border-left: 4px solid #ff9800;
  border-radius: 4px;
  color: var(--text-secondary);
  font-size: 0.9rem;
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
</style>