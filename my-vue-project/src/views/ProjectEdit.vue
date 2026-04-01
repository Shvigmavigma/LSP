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
        <LanguageSwitcher />
        <button class="home-button" @click="goHome" :title="$t('common.home')">🏠</button>
      </div>
    </header>

    <!-- Информационная подсказка о правах -->
    <div v-if="!isNew" class="permission-hint" :class="{ 'admin-hint': isAdminOrCurator }">
      <span class="hint-icon">{{ isAdminOrCurator ? '⚙️' : 'ℹ️' }}</span>
      <span class="hint-text">
        <template v-if="isAdminOrCurator">
          {{ $t('projectEdit.adminHint') }}
        </template>
        <template v-else>
          {{ $t('projectEdit.noRightsHint') }}
        </template>
      </span>
    </div>

    <div class="edit-card">
      <form @submit.prevent="handleSubmit">
        <!-- Основная информация -->
        <div class="form-section">
          <h2>{{ $t('projectEdit.basicInfo') }}</h2>
          <div class="form-group">
            <label for="title">{{ $t('projectEdit.projectTitle') }}</label>
            <input id="title" v-model="form.title" type="text" required />
          </div>
          <div class="form-group">
            <label for="body">{{ $t('projectEdit.description') }}</label>
            <textarea id="body" v-model="form.body" rows="4" required></textarea>
          </div>
          <div class="form-group">
            <label for="underbody">{{ $t('projectEdit.additionalInfo') }}</label>
            <textarea id="underbody" v-model="form.underbody" rows="2"></textarea>
          </div>
        </div>

        <!-- Участники проекта -->
        <div class="form-section">
          <h2>{{ $t('projectEdit.participants') }}</h2>
          <div class="participants-section">
            <div v-if="participants.length > 0" class="current-participants">
              <span class="participants-label">{{ $t('projectEdit.currentParticipants') }}:</span>
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
              <label>{{ $t('projectEdit.addParticipantByNickname') }}</label>
              <div class="search-row">
                <input
                  v-model="searchQuery"
                  type="text"
                  :placeholder="$t('projectEdit.nicknamePlaceholder')"
                  @input="searchUsers"
                />
                <select v-model="selectedRole">
                  <option v-for="role in availableRolesForSelected" :key="role" :value="role">
                    {{ getRoleDisplay(role) }}
                  </option>
                </select>
                <button @click="addParticipant" :disabled="!selectedUser">{{ $t('common.add') }}</button>
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
              <p>⚠️ {{ $t('projectEdit.suggestModeNote') }}</p>
            </div>
            <div v-if="isApplyingSuggestion" class="suggest-note">
              <p>📝 {{ $t('projectEdit.applySuggestionNote') }}</p>
            </div>
          </div>
        </div>

        <!-- Приглашение по email (только для существующих проектов) -->
        <div v-if="isEdit" class="form-section">
          <h2>{{ $t('projectEdit.inviteByEmail') }}</h2>
          <div class="invite-section">
            <div class="invite-row">
              <input
                v-model="inviteEmail"
                type="email"
                :placeholder="$t('projectEdit.emailPlaceholder')"
                class="invite-input"
              />
              <select v-model="inviteRole">
                <option value="executor">{{ $t('roles.executor') }}</option>
                <option value="customer">{{ $t('roles.customer') }}</option>
                <option value="supervisor">{{ $t('roles.supervisor') }}</option>
                <option value="expert">{{ $t('roles.expert') }}</option>
                <option value="curator">{{ $t('roles.curator') }}</option>
              </select>
              <button @click="sendInvite" :disabled="!inviteEmail || sendingInvite">
                {{ sendingInvite ? $t('common.sending') : $t('projectEdit.sendInvite') }}
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
            <h2>{{ $t('projectEdit.tasks') }}</h2>
            <div class="task-buttons">
              <button type="button" class="add-task-button" @click="addTask">+ {{ $t('projectEdit.addTask') }}</button>
              <button type="button" class="add-default-tasks-button" @click="addDefaultTasks">📋 {{ $t('projectEdit.addDefaultTasks') }}</button>
            </div>
          </div>

          <div v-if="tasks.length === 0" class="no-tasks">
            {{ $t('projectEdit.noTasks') }}
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
                <span class="task-title">{{ task.title || $t('projectEdit.untitled') }}</span>
                <button
                  type="button"
                  class="delete-task-button"
                  @click.stop="removeTask(index)"
                  :title="$t('common.delete')"
                >✕</button>
              </div>

              <!-- Развёрнутая форма задачи -->
              <div v-else class="task-form">
                <div class="task-form-header">
                  <h3>{{ task.id ? $t('projectEdit.editTask') : $t('projectEdit.newTask') }}</h3>
                  <button type="button" class="close-task-form" @click="toggleTaskExpand(index)">✕</button>
                </div>

                <div class="form-group">
                  <label :for="'task-title-'+index">{{ $t('projectEdit.taskTitle') }}</label>
                  <input :id="'task-title-'+index" v-model="task.title" type="text" required />
                </div>

                <div class="form-group">
                  <label :for="'task-status-'+index">{{ $t('projectEdit.taskStatus') }}</label>
                  <select :id="'task-status-'+index" v-model="task.status">
                    <option value="в работе">{{ $t('projectEdit.status.inProgress') }}</option>
                    <option value="ожидает">{{ $t('projectEdit.status.waiting') }}</option>
                    <option value="выполнена">{{ $t('projectEdit.status.completed') }}</option>
                  </select>
                </div>

                <div class="form-group">
                  <label :for="'task-body-'+index">{{ $t('projectEdit.taskDescription') }}</label>
                  <textarea :id="'task-body-'+index" v-model="task.body" rows="2" required></textarea>
                </div>

                <div class="form-row">
                  <div class="form-group">
                    <label :for="'task-start-'+index">{{ $t('projectEdit.startDate') }}</label>
                    <input
                      :id="'task-start-'+index"
                      :value="task.timeline"
                      @input="updateTaskDate(index, 'timeline', $event)"
                      type="text"
                      :placeholder="$t('projectEdit.datePlaceholder')"
                      :class="{ 'invalid': task.startError }"
                    />
                    <span v-if="task.startError" class="error-message">{{ task.startError }}</span>
                  </div>

                  <div class="form-group">
                    <label :for="'task-end-'+index">{{ $t('projectEdit.endDate') }}</label>
                    <input
                      :id="'task-end-'+index"
                      :value="task.timelinend"
                      @input="updateTaskDate(index, 'timelinend', $event)"
                      type="text"
                      :placeholder="$t('projectEdit.datePlaceholder')"
                      :class="{ 'invalid': task.endError }"
                    />
                    <span v-if="task.endError" class="error-message">{{ task.endError }}</span>
                  </div>
                </div>

                <div class="task-form-actions">
                  <button type="button" class="save-task-button" @click="saveTask(index)">✓ {{ $t('common.save') }}</button>
                  <button type="button" class="cancel-task-button" @click="toggleTaskExpand(index)">{{ $t('common.cancel') }}</button>
                </div>
              </div>
            </div>
          </div>
          <div v-if="isSuggestMode" class="suggest-note">
            <p>⚠️ {{ $t('projectEdit.suggestModeTasksNote') }}</p>
          </div>
          <div v-if="isApplyingSuggestion" class="suggest-note">
            <p>📝 {{ $t('projectEdit.applySuggestionTasksNote') }}</p>
          </div>
        </div>

        <!-- Кнопки отправки -->
        <div class="form-actions">
          <button type="submit" class="save-button" :disabled="saving">
            {{ saving ? (isSuggestMode ? $t('common.sending') : (isApplyingSuggestion ? $t('projectEdit.acceptingAndSaving') : $t('common.saving'))) : submitButtonText }}
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
import { useI18n } from 'vue-i18n';
import { isTaskTitleUnique } from '@/utils/taskUtils';
import { useProjectsStore } from '@/stores/projects';
import { useAuthStore } from '@/stores/auth';
import { useUsersStore } from '@/stores/users';
import ThemeToggle from '@/components/ThemeToggle.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';
import type { Project, Task, User, Participant, ProjectRole, Suggestion } from '@/types';
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';

const { t } = useI18n();
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
  const user = authStore.user;
  if (!user) return false;
  if (!user.is_teacher) return false;
  return user.teacher_info?.curator ?? false;
});

// Является ли пользователь администратором или куратором
const isAdminOrCurator = computed(() => (authStore.user?.is_admin ?? false) || isCurator.value);

// Определение роли создателя проекта
function getCreatorRole(): ProjectRole {
  const user = authStore.user;
  if (!user) return 'executor';
  if (!user.is_teacher) return 'executor';
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
    title: 'Предзащита 1',
    body: 'Подготовить тему и техническое задание',
    status: 'ожидает',
    timeline: '01.09.2025',
    timelinend: '20.11.2025',
    required_files: [
      { id: uuidv4(), name: 'Техническое задание', description: 'Документ с требованиями' },
      { id: uuidv4(), name: 'Презентация', description: 'Презентация по теме' }
    ]
  },
  {
    title: 'Предзащита 2',
    body: 'Подготовить ТЗ, начальный фрагмент кода и начать пояснительную записку',
    status: 'ожидает',
    timeline: '21.11.2025',
    timelinend: '20.02.2026',
    required_files: [
      { id: uuidv4(), name: 'Техническое задание', description: 'Уточнённое ТЗ' },
      { id: uuidv4(), name: 'Фрагмент кода', description: 'Рабочий прототип' },
      { id: uuidv4(), name: 'Презентация', description: 'Презентация к предзащите 2' }
    ]
  },
  {
    title: 'Защита',
    body: 'Полностью подготовить проект к защите',
    status: 'ожидает',
    timeline: '21.02.2026',
    timelinend: '14.06.2026',
    required_files: [
      { id: uuidv4(), name: 'Техническое задание', description: 'Финальное ТЗ' },
      { id: uuidv4(), name: 'Пояснительная записка', description: 'Полная ПЗ' },
      { id: uuidv4(), name: 'Презентация', description: 'Итоговая презентация' },
      { id: uuidv4(), name: 'Код проекта', description: 'Исходный код' }
    ]
  }
]);

// Роль текущего пользователя в проекте
const userRole = ref<ProjectRole | null>(null);

// Право предлагать изменения (с учётом админа и куратора)
const canSuggest = computed(() =>
  userRole.value === 'expert' ||
  userRole.value === 'supervisor' ||
  userRole.value === 'executor' ||
  (authStore.user?.is_admin ?? false) ||
  isCurator.value
);

// Право на прямое редактирование проекта (с учётом админа и куратора)
const canEdit = computed(() => 
  userRole.value === 'customer' || 
  userRole.value === 'executor' || 
  (authStore.user?.is_admin ?? false) || 
  isCurator.value
);

const pageTitle = computed(() => {
  if (isNew) return t('projectEdit.newProjectTitle');
  if (isApplyingSuggestion.value) return t('projectEdit.applySuggestionTitle');
  return isSuggestMode.value ? t('projectEdit.suggestChangesTitle') : t('projectEdit.editProjectTitle');
});

const submitButtonText = computed(() => {
  if (isNew) return t('projectEdit.createProject');
  if (isApplyingSuggestion.value) return t('projectEdit.acceptAndSave');
  return isSuggestMode.value ? t('projectEdit.sendSuggestion') : t('common.save');
});

const cancelButtonText = computed(() => t('common.cancel'));

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
  if (!isAdminOrCurator.value && participant.user_id === currentUserId.value) {
    showNotification(t('projectEdit.cannotRemoveSelf'), 'info');
    return;
  }
  if (participants.value.length === 1) {
    showNotification(t('projectEdit.needAtLeastOneParticipant'), 'info');
    return;
  }
  participants.value.splice(index, 1);
}

function getRemoveTitle(userId: number): string {
  if (!isAdminOrCurator.value && userId === currentUserId.value) return t('projectEdit.cannotRemoveSelfTooltip');
  if (participants.value.length === 1) return t('projectEdit.cannotRemoveLastTooltip');
  return t('common.delete');
}

// Загрузка данных
onMounted(async () => {
  if (usersStore.users.length === 0) {
    await usersStore.fetchAllUsers();
  }

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

    if (isApplyingSuggestion.value && applyingSuggestionId.value) {
      const suggestion = project.suggestions?.find(s => s.id === applyingSuggestionId.value);
      if (!suggestion) {
        showNotification(t('projectEdit.suggestionNotFound'), 'error');
        router.push(`/project/${projectId}`);
        return;
      }
      applySuggestionChanges(suggestion);
    } else {
      const modeParam = route.query.mode;
      if (modeParam === 'suggest') {
        if (!canSuggest.value) {
          showNotification(t('projectEdit.noSuggestRights'), 'error');
          setTimeout(() => router.push(`/project/${projectId}`), 2000);
          return;
        }
        isSuggestMode.value = true;
      } else {
        if (!canEdit.value) {
          showNotification(t('projectEdit.noEditRights'), 'info');
          setTimeout(() => router.push(`/project/${projectId}`), 2000);
          return;
        }
        isSuggestMode.value = false;
      }

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
  return t(`roles.${role}`);
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
    inviteResult.value = `${t('projectEdit.inviteCreated')} ${response.data.token}`;
    inviteSuccess.value = true;
    inviteEmail.value = '';
    showNotification(t('projectEdit.inviteSuccess'), 'success');
  } catch (error: any) {
    console.error('Failed to create invite:', error);
    const msg = error.response?.data?.detail || t('projectEdit.inviteError');
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

function addDefaultTasks() {
  // Получаем существующие названия задач (в нижнем регистре)
  const existingTitles = tasks.value.map(t => t.title.trim().toLowerCase());
  
  // Фильтруем дефолтные задачи, оставляя только те, чьи названия не встречаются
  const newTasksToAdd = defaultTasks.value
    .filter(task => {
      const title = task.title?.trim().toLowerCase() || 'новая задача';
      return !existingTitles.includes(title);
    })
    .map(task => {
      const requiredFiles = (task.required_files || []).map(rf => ({
        id: uuidv4(),
        name: rf.name,
        description: rf.description || ''
      }));
      return {
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
        required_files: requiredFiles,
      };
    });
  
  if (newTasksToAdd.length === 0) {
    showNotification(t('projectEdit.allDefaultTasksAlreadyExist'), 'info');
    return;
  }
  
  tasks.value.push(...newTasksToAdd);
  showNotification(t('taskEdit.defaultTasksAdded', { count: newTasksToAdd.length }), 'success');
}

function saveTask(index: number) {
  const task = tasks.value[index];
  if (!task) return;
  if (!task.title.trim()) {
    showNotification(t('projectEdit.taskTitleRequired'), 'info');
    return;
  }
  if (!task.body.trim()) {
    showNotification(t('projectEdit.taskDescriptionRequired'), 'info');
    return;
  }

  // Проверка уникальности названия
  if (!isTaskTitleUnique(tasks.value, task.title, index)) {
    showNotification(t('projectEdit.taskTitleMustBeUnique'), 'info');
    return;
  }

  if (task.timeline && task.timelinend) {
    const start = parseDate(task.timeline);
    const end = parseDate(task.timelinend);
    if (start && end && start > end) {
      showNotification(t('projectEdit.startBeforeEnd'), 'info');
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
    showNotification(t('projectEdit.fillRequired'), 'info');
    return;
  }

  for (let i = 0; i < tasks.value.length; i++) {
    if (tasks.value[i]?.expanded) {
      showNotification(t('projectEdit.finishEditing'), 'info');
      return;
    }
  }

  if (participants.value.length === 0 && !isNew) {
    showNotification(t('projectEdit.needAtLeastOneParticipant'), 'info');
    return;
  }

  const projectData = {
    title: form.title,
    body: form.body,
    underbody: form.underbody || '',
    participants: participants.value,
    tasks: tasks.value.map(({ expanded, startError, endError, id, ...task }) => task),
  };

  saving.value = true;

  try {
    if (isApplyingSuggestion.value && applyingSuggestionId.value) {
      await axios.put(`${baseUrl}/projects/${projectId}/suggestions/${applyingSuggestionId.value}/accept`);
      showNotification(t('projectEdit.suggestionAccepted'), 'success');
    }

    if (isNew) {
      if (!authStore.userId) throw new Error('User not authenticated');
      if (!participants.value.some(p => p.user_id === authStore.userId)) {
        const defaultRole = getCreatorRole();
        projectData.participants.push({
          user_id: authStore.userId,
          role: defaultRole,
          joined_at: new Date().toISOString(),
        });
      }
      const created = await projectsStore.createProject(projectData);
      showNotification(t('projectEdit.projectCreated'), 'success');
      router.push(`/project/${created.id}`);
    } else if (isSuggestMode.value) {
      const suggestionData = {
        target_type: 'project',
        changes: projectData,
      };
      await axios.post(`${baseUrl}/projects/${projectId}/suggestions`, suggestionData);
      showNotification(t('projectEdit.suggestionSent'), 'success');
      setTimeout(() => router.push(`/project/${projectId}`), 1500);
    } else {
      await projectsStore.updateProject(projectId, projectData);
      showNotification(t('projectEdit.changesSaved'), 'success');
      setTimeout(() => router.push(`/project/${projectId}`), 1500);
    }
  } catch (err: any) {
    console.error('Error saving project:', err);
    if (err.response?.status === 403) {
      showNotification(t('projectEdit.noEditRights'), 'error');
    } else {
      showNotification(t('projectEdit.saveError'), 'error');
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