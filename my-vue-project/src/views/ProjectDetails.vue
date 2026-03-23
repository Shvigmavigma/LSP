<template>
  <div class="project-details-page">
    <!-- Шапка -->
    <header class="details-header" :class="{ 'author-header': userRole }">
      <h1 v-if="!userRole" class="page-title">{{ project?.title || 'Проект' }}</h1>
      <div class="header-buttons">
        <ThemeToggle />
        <button class="home-button" @click="goHome" title="На главную">🏠</button>
      </div>
    </header>

    <!-- Состояния загрузки/ошибки -->
    <div v-if="loading" class="loading">Загрузка...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="project">
      <!-- Макет для НЕ-участников -->
      <div v-if="!userRole && !isAdmin && !isCurator" class="non-author-layout">
        <div class="project-card">
          <div class="project-section">
            <h3>Описание</h3>
            <p>{{ project.body }}</p>
          </div>
          <div v-if="project.underbody" class="project-section">
            <h3>Дополнительно</h3>
            <p>{{ project.underbody }}</p>
          </div>
          <div class="project-section">
            <h3>Участники</h3>
            <div v-if="project.participants?.length" class="participants-list">
              <span
                v-for="participant in project.participants"
                :key="participant.user_id"
                class="participant-link"
                @click="goToUser(participant.user_id)"
              >
                {{ getUserNickname(participant.user_id) }}
                <span class="role-badge">{{ getRoleDisplay(participant.role) }}</span>
              </span>
            </div>
            <p v-else>Нет участников</p>
          </div>

          <!-- Кнопка отклика для учеников (не участников) -->
          <div v-if="isStudent && !hasExecutors" class="respond-project-section">
            <div v-if="userPendingRequest" class="already-responded">
              <span class="responded-message">✅ Вы уже откликнулись</span>
            </div>
            <button v-else class="respond-project-btn" @click="respondToProject" :disabled="responding">
              {{ responding ? 'Отправка...' : 'Откликнуться на проект' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Макет для УЧАСТНИКОВ, АДМИНИСТРАТОРОВ И КУРАТОРОВ -->
      <div v-else class="author-layout">
        <h1 class="project-title-center">{{ project.title }}</h1>

        <div class="two-columns">
          <!-- Левая колонка -->
          <div class="info-column">
            <div class="project-section">
              <h3>Описание</h3>
              <p>{{ project.body }}</p>
            </div>
            <div v-if="project.underbody" class="project-section">
              <h3>Дополнительно</h3>
              <p>{{ project.underbody }}</p>
            </div>

            <!-- Ссылки проекта -->
            <div class="project-links">
              <h3>Ссылки проекта</h3>
              <div class="links-buttons">
                <!-- GitHub -->
                <template v-if="project.links?.github">
                  <div v-if="!showEditGithub" class="link-display">
                    <a
                      :href="project.links.github"
                      target="_blank"
                      rel="noopener noreferrer"
                      class="link-button github-link"
                    >
                      <img :src="githubIcon" alt="GitHub" class="icon" />
                      GitHub репозиторий
                    </a>
                    <div class="link-actions">
                      <button class="link-edit" @click="startEditGithub" title="Редактировать">✎</button>
                      <button class="link-delete" @click="deleteGithubLink" title="Удалить">✖</button>
                    </div>
                  </div>
                  <div v-else class="link-input-wrapper">
                    <input
                      v-model="githubEditValue"
                      type="url"
                      placeholder="https://github.com/..."
                      class="link-input"
                      @keyup.enter="saveEditGithub"
                    />
                    <button class="link-save" @click="saveEditGithub">✔</button>
                    <button class="link-cancel" @click="cancelEditGithub">✖</button>
                  </div>
                </template>
                <template v-else>
                  <div v-if="showGithubInput" class="link-input-wrapper">
                    <input
                      v-model="githubInput"
                      type="url"
                      placeholder="https://github.com/..."
                      class="link-input"
                      @keyup.enter="saveGithubLink"
                    />
                    <button class="link-save" @click="saveGithubLink">✔</button>
                    <button class="link-cancel" @click="cancelGithub">✖</button>
                  </div>
                  <button v-else class="link-button add-github" @click="showGithubInput = true">
                    <img :src="githubIcon" alt="GitHub" class="icon" />
                    + Добавить GitHub
                  </button>
                </template>

                <!-- Google Drive -->
                <template v-if="project.links?.google_drive">
                  <div v-if="!showEditDrive" class="link-display">
                    <a
                      :href="project.links.google_drive"
                      target="_blank"
                      rel="noopener noreferrer"
                      class="link-button drive-link"
                    >
                      <img :src="driveIcon" alt="Google Drive" class="icon" />
                      Google Диск
                    </a>
                    <div class="link-actions">
                      <button class="link-edit" @click="startEditDrive" title="Редактировать">✎</button>
                      <button class="link-delete" @click="deleteDriveLink" title="Удалить">✖</button>
                    </div>
                  </div>
                  <div v-else class="link-input-wrapper">
                    <input
                      v-model="driveEditValue"
                      type="url"
                      placeholder="https://drive.google.com/..."
                      class="link-input"
                      @keyup.enter="saveEditDrive"
                    />
                    <button class="link-save" @click="saveEditDrive">✔</button>
                    <button class="link-cancel" @click="cancelEditDrive">✖</button>
                  </div>
                </template>
                <template v-else>
                  <div v-if="showDriveInput" class="link-input-wrapper">
                    <input
                      v-model="driveInput"
                      type="url"
                      placeholder="https://drive.google.com/..."
                      class="link-input"
                      @keyup.enter="saveDriveLink"
                    />
                    <button class="link-save" @click="saveDriveLink">✔</button>
                    <button class="link-cancel" @click="cancelDrive">✖</button>
                  </div>
                  <button v-else class="link-button add-drive" @click="showDriveInput = true">
                    <img :src="driveIcon" alt="Google Drive" class="icon" />
                    + Добавить Google Диск
                  </button>
                </template>
              </div>
            </div>

            <!-- Участники -->
            <div class="project-section">
              <h3>Участники</h3>
              <div v-if="project.participants?.length" class="participants-list">
                <span
                  v-for="participant in project.participants"
                  :key="participant.user_id"
                  class="participant-link"
                  @click="goToUser(participant.user_id)"
                >
                  {{ getUserNickname(participant.user_id) }}
                  <span class="role-badge">{{ getRoleDisplay(participant.role) }}</span>
                </span>
              </div>
              <p v-else>Нет участников</p>
            </div>

            <!-- Выполненные задачи -->
            <div v-if="completedTasks.length" class="project-section">
              <h3>Выполненные задачи</h3>
              <div class="completed-tasks">
                <div
                  v-for="task in completedTasks"
                  :key="task.title"
                  class="completed-task"
                  @click="goToTask(task)"
                >
                  <span class="completed-task-title">{{ task.title }}</span>
                  <span class="completed-task-date">{{ formatTaskDates(task) }}</span>
                </div>
              </div>
            </div>

            <!-- Кнопки управления проектом (единый блок) -->
            <div class="project-actions" v-if="hasManagementRights">
              <button class="edit-project-button" @click="goToEdit">✎ Редактировать проект</button>
              <button 
                class="delete-project-button" 
                @click="handleProjectDelete" 
                :disabled="deleteInProgress"
              >
                {{ deleteInProgress ? 'Обработка...' : (isAdminOrCurator ? '🗑 Удалить проект' : '🗑 Скрыть проект') }}
              </button>
            </div>
          </div>

          <!-- Правая колонка -->
          <div class="tasks-column">
            <!-- Заголовок над кнопками -->
            <h3 class="tasks-section-title">Активные задачи</h3>

            <!-- Кнопки управления -->
            <div class="task-header-buttons">
              <!-- Кнопка показа предложений -->
              <button 
                v-if="hasFullAccess" 
                class="suggestions-btn" 
                @click="showSuggestions = !showSuggestions"
              >
                <span class="btn-content">
                  <span class="suggestions-icon">📋</span>
                  {{ showSuggestions ? 'Скрыть' : 'Показать' }} предложения
                  <span v-if="pendingSuggestionsCount > 0" class="header-unread-badge">
                    {{ pendingSuggestionsCount }}
                  </span>
                </span>
              </button>

              <!-- Для экспертов, научруков и исполнителей – ссылка на редактирование в режиме предложения -->
              <router-link
                v-if="canSuggest"
                :to="`/project/edit/${project.id}?mode=suggest`"
                custom
                v-slot="{ navigate }"
              >
                <button class="suggest-btn" @click="navigate">💡 Предложить правку</button>
              </router-link>

              <!-- Кнопка приглашения -->
              <button v-if="canInvite" class="invite-btn" @click="openInviteModal">
                ✉️ Пригласить
              </button>

              <!-- Кнопка комментариев -->
              <button class="comments-header-btn" @click="showProjectComments = !showProjectComments">
                <span class="btn-content">
                  <span class="comment-icon">💬</span>
                  {{ showProjectComments ? 'Скрыть' : 'Показать' }} комментарии
                  <span v-if="unreadProjectCommentsCount > 0" class="header-unread-badge">
                    {{ unreadProjectCommentsCount }}
                  </span>
                </span>
              </button>

              <!-- Кнопка: Запросы на вступление (для заказчика, куратора, администратора) -->
              <button 
                v-if="canManageJoinRequests" 
                class="requests-btn" 
                @click="showJoinRequests = !showJoinRequests"
              >
                <span class="btn-content">
                  <span class="requests-icon">👥</span>
                  {{ showJoinRequests ? 'Скрыть' : 'Запросы' }}
                  <span v-if="pendingJoinRequestsCount > 0" class="header-unread-badge">
                    {{ pendingJoinRequestsCount }}
                  </span>
                </span>
              </button>
            </div>

            <!-- Блок предложений -->
            <div v-if="showSuggestions" class="suggestions-container">
              <SuggestionsSection
                :project-id="project.id"
                :suggestions="suggestions"
                :is-project-participant="hasFullAccess"
                :can-edit="canEdit"
                :can-hide-comments="canHideComments"
                :on-accept="acceptSuggestion"
                :on-reject="rejectSuggestion"
                :on-add-comment="addSuggestionComment"
                :on-mark-comment-read="markSuggestionCommentRead"
                :on-delete-comment="deleteSuggestionComment"
                :on-hide-comment="hideSuggestionComment"
              />
            </div>

            <!-- Блок комментариев проекта -->
            <div v-if="showProjectComments" class="comments-container">
            <CommentsSection
              :comments="project.comments || []"
              :can-comment="hasFullAccess"
              :is-author="canEdit"
              :can-hide-comments="canHideComments"
              :is-admin="isAdmin"
              :is-curator="isCurator"
              :on-add-comment="addProjectComment"
              :on-mark-as-read="markProjectCommentAsRead"
              :on-hide-comment="hideProjectComment"
              :on-restore-comment="restoreProjectComment"
              :on-permanent-delete="permanentDeleteComment"
            />
            </div>

            <!-- Блок запросов на вступление -->
            <div v-if="showJoinRequests" class="requests-container">
              <div class="requests-header">
                <h3>Запросы на вступление</h3>
                <span v-if="pendingJoinRequestsCount > 0" class="pending-badge">{{ pendingJoinRequestsCount }}</span>
              </div>

              <div v-if="project.join_requests === undefined" class="loading">Загрузка запросов...</div>
              <div v-else-if="pendingJoinRequests.length === 0" class="no-requests">
                Нет новых запросов
              </div>
              <div v-else class="requests-list">
                <div
                  v-for="request in pendingJoinRequests"
                  :key="request.id"
                  class="request-item"
                >
                  <div class="request-info">
                    <div class="request-user">
                      <div class="user-avatar">
                        <img
                          v-if="getUserAvatar(request.user_id)"
                          :src="getUserAvatar(request.user_id)"
                          :alt="getUserNickname(request.user_id)"
                          @error="handleAuthorImageError(request.user_id)"
                        />
                        <span v-else>{{ getUserInitials(request.user_id) }}</span>
                      </div>
                      <span class="user-name">{{ getUserNickname(request.user_id) }}</span>
                    </div>
                    <div class="request-task">
                      Хочет присоединиться к проекту как исполнитель
                    </div>
                  </div>
                  <div class="request-actions">
                    <button class="accept-request-btn" @click="acceptJoinRequest(request.id)">✅ Принять</button>
                    <button class="reject-request-btn" @click="rejectJoinRequest(request.id)">❌ Отклонить</button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Задачи в работе -->
            <div v-if="inProgressTasks.length > 0" class="task-group">
              <h4 class="task-group-title in-progress-title">В работе</h4>
              <div class="task-tree">
                <div
                  v-for="task in inProgressTasks"
                  :key="task.title"
                  class="task-node"
                  :class="taskStatusClass(task)"
                  @click="goToTask(task)"
                >
                  <span class="task-icon">📄</span>
                  <div class="task-content">
                    <strong>{{ task.title }}</strong>
                    <span class="task-status">{{ task.status }}</span>
                    <p>{{ task.body }}</p>
                    <span v-if="task.status === 'в работе'" class="task-progress">
                      Прогресс: {{ task.progress ?? 0 }}%
                    </span>
                    <small>Срок: {{ formatTaskDates(task) }}</small>
                    <span v-if="isTaskOverdue(task)" class="overdue-badge">Просрочено</span>
                    <span v-if="isTaskInvalid(task)" class="invalid-badge">Некорректные даты</span>
                    <span v-if="isTaskNotStarted(task)" class="not-started-badge">Не начато</span>
                    <span v-if="task.assigned_to" class="assigned-info">
                      Исполнитель: {{ getUserNickname(task.assigned_to) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Задачи в ожидании -->
            <div v-if="waitingTasks.length > 0" class="task-group">
              <h4 class="task-group-title waiting-title">Ожидают</h4>
              <div class="task-tree">
                <div
                  v-for="task in waitingTasks"
                  :key="task.title"
                  class="task-node"
                  :class="taskStatusClass(task)"
                  @click="goToTask(task)"
                >
                  <span class="task-icon">📄</span>
                  <div class="task-content">
                    <strong>{{ task.title }}</strong>
                    <span class="task-status">{{ task.status }}</span>
                    <p>{{ task.body }}</p>
                    <span v-if="task.status === 'в работе'" class="task-progress">
                      Прогресс: {{ task.progress ?? 0 }}%
                    </span>
                    <small>Срок: {{ formatTaskDates(task) }}</small>
                    <span v-if="isTaskOverdue(task)" class="overdue-badge">Просрочено</span>
                    <span v-if="isTaskInvalid(task)" class="invalid-badge">Некорректные даты</span>
                    <span v-if="isTaskNotStarted(task)" class="not-started-badge">Не начато</span>
                    <span v-if="task.assigned_to" class="assigned-info">
                      Исполнитель: {{ getUserNickname(task.assigned_to) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Сообщение, если нет ни одной активной задачи -->
            <div v-if="inProgressTasks.length === 0 && waitingTasks.length === 0" class="no-tasks">
              Нет активных задач
            </div>

            <!-- Диаграмма Ганта -->
            <div v-if="activeTasks.length" class="gantt-section">
              <h3>Таймлайн задач (прошедшее время)</h3>
              <div class="gantt-chart">
                <div v-for="(task, index) in activeTasksProgress" :key="index" class="gantt-row">
                  <div class="gantt-label">{{ task.title }}</div>
                  <div class="gantt-bar-container">
                    <div
                      class="gantt-bar"
                      :style="{ backgroundColor: task.barColor }"
                    ></div>
                    <span class="gantt-text">
                      {{ task.startStr || '???' }} – {{ task.endStr || '???' }} ({{ task.progress.toFixed(1) }}%)
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Модальное окно приглашения -->
    <InviteModal
      :show="showInviteModal"
      :project-id="project?.id"
      @close="showInviteModal = false"
      @invite="sendInvite"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, watchEffect } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useProjectsStore } from '@/stores/projects';
import { useAuthStore } from '@/stores/auth';
import { useUsersStore } from '@/stores/users';
import ThemeToggle from '@/components/ThemeToggle.vue';
import CommentsSection from '@/components/CommentsSection.vue';
import SuggestionsSection from '@/components/SuggestionsSection.vue';
import InviteModal from '@/components/InviteModal.vue';
import type { Project, User, Task, Comment, ProjectRole, Suggestion, JoinRequest } from '@/types';
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';

import githubIcon from '@/assets/icons/icons8-github-30.png';
import driveIcon from '@/assets/icons/icons8-google-drive-48.png';

const baseUrl = 'http://localhost:8000';

const route = useRoute();
const router = useRouter();
const projectsStore = useProjectsStore();
const authStore = useAuthStore();
const usersStore = useUsersStore();

const project = ref<Project | null>(null);
const loading = ref(true);
const error = ref('');
const showProjectComments = ref(false);
const showSuggestions = ref(false);
const showJoinRequests = ref(false);
const responding = ref(false);

// Состояния для ввода ссылок
const showGithubInput = ref(false);
const githubInput = ref('');
const showDriveInput = ref(false);
const driveInput = ref('');
const showEditGithub = ref(false);
const githubEditValue = ref('');
const showEditDrive = ref(false);
const driveEditValue = ref('');
const deleteInProgress = ref(false);
const isAdminOrCurator = computed(() => isAdmin.value || isCurator.value);

const projectId = Number(route.params.projectId);
const taskIndex = Number(route.params.taskIndex);

// Роль текущего пользователя в проекте (только если он участник)
const userRole = computed<ProjectRole | null>(() => {
  if (!authStore.userId || !project.value) return null;
  const participant = project.value.participants?.find(p => p.user_id === authStore.userId);
  return participant?.role || null;
});

// Глобальные роли
const isAdmin = computed(() => authStore.user?.is_admin === true);
const isCurator = computed(() => authStore.user?.is_teacher && authStore.user?.teacher_info?.curator === true);

// Полный доступ (участник, админ или куратор)
const hasFullAccess = computed(() => !!userRole.value || isAdmin.value || isCurator.value);

// Права на управление проектом (редактирование, удаление)
const canEdit = computed(() => 
  userRole.value === 'customer' || 
  isAdmin.value || 
  isCurator.value
);

// Право предлагать изменения
const canSuggest = computed(() => 
  ['expert', 'supervisor', 'executor'].includes(userRole.value) || 
  isAdmin.value || 
  isCurator.value
);
const handleProjectDelete = async () => {
  if (!project.value) return;
  
  deleteInProgress.value = true;
  
  // Админ или куратор - полное удаление
  if (isAdminOrCurator.value) {
    if (confirm('Вы уверены, что хотите полностью удалить проект? Это действие необратимо.')) {
      try {
        await axios.delete(`${baseUrl}/projects/${project.value.id}`);
        showNotification('Проект успешно удалён', 'success');
        router.push('/main');
      } catch (error) {
        console.error('Ошибка при удалении проекта:', error);
        showNotification('Не удалось удалить проект', 'error');
      } finally {
        deleteInProgress.value = false;
      }
    } else {
      deleteInProgress.value = false;
    }
    return;
  }
  
  // Заказчик или исполнитель - скрытие проекта
  if (confirm('Скрыть проект из списка? Вы сможете снова его увидеть, если администратор или куратор вернёт его.')) {
    try {
      await axios.patch(`${baseUrl}/projects/${project.value.id}/hide`);
      showNotification('Проект скрыт', 'success');
      router.push('/main');
    } catch (error) {
      console.error('Failed to hide project', error);
      showNotification('Ошибка при скрытии проекта', 'error');
    } finally {
      deleteInProgress.value = false;
    }
  } else {
    deleteInProgress.value = false;
  }
};

// Право скрывать комментарии (научрук, админ, куратор)
const canHideComments = computed(() => 
  userRole.value === 'supervisor' || 
  isAdmin.value || 
  isCurator.value
);

// Право приглашать
const canInvite = computed(() => 
  userRole.value === 'customer' || 
  userRole.value === 'supervisor' || 
  isAdmin.value || 
  isCurator.value
);

// Право управлять запросами на вступление
const canManageJoinRequests = computed(() => 
  userRole.value === 'customer' || 
  userRole.value === 'curator' || 
  isAdmin.value || 
  isCurator.value
);

// Право скрывать проект (исполнитель, куратор в проекте, админ, куратор)
const canHide = computed(() => 
  userRole.value === 'executor' || 
  userRole.value === 'curator' || 
  isAdmin.value || 
  isCurator.value
);

// Общее право на отображение блока управления проектом
const hasManagementRights = computed(() => 
  canEdit.value || canHide.value
);

// Количество непрочитанных комментариев
const unreadProjectCommentsCount = computed(() => {
  const comments = project.value?.comments || [];
  if (canHideComments.value) {
    return comments.filter(c => !c.isRead).length;
  }
  return comments.filter(c => !c.hidden && !c.isRead).length;
});

// Количество ожидающих предложений
const pendingSuggestionsCount = computed(() => {
  return (project.value?.suggestions || []).filter(s => s.status === 'pending').length;
});

// --- ЗАПРОСЫ НА ВСТУПЛЕНИЕ ---
const pendingJoinRequests = computed<JoinRequest[]>(() => {
  return (project.value?.join_requests?.filter(r => r.status === 'pending') || []) as JoinRequest[];
});
const pendingJoinRequestsCount = computed(() => pendingJoinRequests.value.length);

// Есть ли исполнители в проекте
const hasExecutors = computed(() => {
  return project.value?.participants?.some(p => p.role === 'executor') || false;
});

// Является ли текущий пользователь учеником
const isStudent = computed(() => authStore.user && !authStore.user.is_teacher);

// Есть ли у текущего пользователя ожидающий запрос
const userPendingRequest = computed(() => {
  if (!authStore.userId || !project.value?.join_requests) return false;
  return project.value.join_requests.some(r => r.user_id === authStore.userId && r.status === 'pending');
});
const restoreProjectComment = async (commentId: string) => {
  if (!project.value) return;
  try {
    await axios.post(`${baseUrl}/projects/${project.value.id}/comments/${commentId}/restore`);
    showNotification('Комментарий восстановлен', 'success');
    await loadProject();
  } catch (error) {
    console.error('Failed to restore comment', error);
    showNotification('Ошибка при восстановлении комментария', 'error');
  }
};

const restoreTaskComment = async (commentId: string) => {
  if (!project.value) return;
  try {
    await axios.post(`${baseUrl}/projects/${project.value.id}/tasks/${taskIndex}/comments/${commentId}/restore`);
    showNotification('Комментарий восстановлен', 'success');
    await loadProject();
  } catch (error) {
    console.error('Failed to restore comment', error);
    showNotification('Ошибка при восстановлении комментария', 'error');
  }
};
// Модальное окно приглашения
const showInviteModal = ref(false);

// Загрузка данных пользователей
async function loadParticipants() {
  if (usersStore.users.length === 0) {
    await usersStore.fetchAllUsers();
  }
}

// Загрузка проекта
async function loadProject() {
  const id = Number(route.params.id);
  if (isNaN(id)) {
    error.value = 'Неверный ID проекта';
    loading.value = false;
    return;
  }

  try {
    project.value = await projectsStore.fetchProjectById(id);
    await loadParticipants();
  } catch (err) {
    error.value = 'Ошибка загрузки проекта';
    console.error(err);
  } finally {
    loading.value = false;
  }
}

// --- ДЕЙСТВИЯ С ЗАПРОСАМИ ---
async function respondToProject() {
  if (!project.value) return;
  responding.value = true;
  try {
    await axios.post(`${baseUrl}/projects/${project.value.id}/join-requests`);
    showNotification('Запрос отправлен!', 'success');
    await loadProject();
  } catch (err: any) {
    console.error('Failed to respond to project', err);
    const msg = err.response?.data?.detail || 'Ошибка при отправке запроса';
    showNotification(msg, 'error');
  } finally {
    responding.value = false;
  }
}

async function acceptJoinRequest(requestId: string) {
  if (!project.value) return;
  try {
    await axios.put(`${baseUrl}/projects/${project.value.id}/join-requests/${requestId}/accept`);
    showNotification('Запрос принят', 'success');
    await loadProject();
  } catch (err) {
    console.error('Failed to accept request', err);
    showNotification('Ошибка при принятии запроса', 'error');
  }
}

async function rejectJoinRequest(requestId: string) {
  if (!project.value) return;
  try {
    await axios.put(`${baseUrl}/projects/${project.value.id}/join-requests/${requestId}/reject`);
    showNotification('Запрос отклонён', 'success');
    await loadProject();
  } catch (err) {
    console.error('Failed to reject request', err);
    showNotification('Ошибка при отклонении запроса', 'error');
  }
}

onMounted(loadProject);
watch(() => route.params.id, loadProject);

// Вспомогательные функции для пользователей
function getUserNickname(id: number): string {
  const user = usersStore.users.find(u => u.id === id);
  return user ? user.nickname : `ID: ${id}`;
}

function getUserAvatar(id: number): string | undefined {
  const user = usersStore.users.find(u => u.id === id);
  return user?.avatar ? `${baseUrl}/avatars/${user.avatar}` : undefined;
}

function getUserInitials(id: number): string {
  const user = usersStore.users.find(u => u.id === id);
  return user?.nickname?.charAt(0).toUpperCase() || '?';
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

// --- Функции для работы со ссылками ---
async function updateProjectLinks(updates: Partial<NonNullable<Project['links']>>) {
  if (!project.value) return;
  try {
    const newLinks = { ...(project.value.links || {}), ...updates };
    await axios.put(`${baseUrl}/projects/${project.value.id}`, { links: newLinks });
    project.value.links = newLinks;
  } catch (err) {
    console.error('Failed to update links', err);
    alert('Ошибка при сохранении ссылки');
  }
}
function saveGithubLink() {
  if (githubInput.value.trim()) {
    updateProjectLinks({ github: githubInput.value.trim() });
  }
  showGithubInput.value = false;
  githubInput.value = '';
}
function cancelGithub() { showGithubInput.value = false; githubInput.value = ''; }
function startEditGithub() {
  githubEditValue.value = project.value?.links?.github || '';
  showEditGithub.value = true;
}
function saveEditGithub() {
  if (githubEditValue.value.trim()) {
    updateProjectLinks({ github: githubEditValue.value.trim() });
  }
  showEditGithub.value = false;
  githubEditValue.value = '';
}
function cancelEditGithub() { showEditGithub.value = false; githubEditValue.value = ''; }
async function deleteGithubLink() {
  if (!project.value?.links?.github) return;
  if (confirm('Удалить ссылку на GitHub?')) {
    const newLinks = { ...project.value.links };
    delete newLinks.github;
    await updateProjectLinks(newLinks as Partial<NonNullable<Project['links']>>);
  }
}
function saveDriveLink() {
  if (driveInput.value.trim()) {
    updateProjectLinks({ google_drive: driveInput.value.trim() });
  }
  showDriveInput.value = false;
  driveInput.value = '';
}
function cancelDrive() { showDriveInput.value = false; driveInput.value = ''; }
function startEditDrive() {
  driveEditValue.value = project.value?.links?.google_drive || '';
  showEditDrive.value = true;
}
function saveEditDrive() {
  if (driveEditValue.value.trim()) {
    updateProjectLinks({ google_drive: driveEditValue.value.trim() });
  }
  showEditDrive.value = false;
  driveEditValue.value = '';
}
function cancelEditDrive() { showEditDrive.value = false; driveEditValue.value = ''; }
async function deleteDriveLink() {
  if (!project.value?.links?.google_drive) return;
  if (confirm('Удалить ссылку на Google Диск?')) {
    const newLinks = { ...project.value.links };
    delete newLinks.google_drive;
    await updateProjectLinks(newLinks as Partial<NonNullable<Project['links']>>);
  }
}

// --- Работа с комментариями проекта ---
const addProjectComment = async (content: string) => {
  if (!project.value || !authStore.user) return;
  // Проверка прав уже выполнена через canComment в шаблоне, но для надёжности:
  if (!hasFullAccess.value) {
    showNotification('У вас нет прав для комментирования', 'info');
    return;
  }
  const newComment: Comment = {
    id: uuidv4(),
    authorId: authStore.user.id,
    content,
    createdAt: new Date().toISOString(),
    isRead: false,
    hidden: false,
  };
  try {
    const response = await axios.post(`${baseUrl}/projects/${project.value.id}/comments`, newComment);
    project.value = response.data;
    showProjectComments.value = true;
  } catch (error) {
    console.error('Failed to add comment:', error);
    alert('Ошибка при добавлении комментария');
  }
};

const markProjectCommentAsRead = async (commentId: string) => {
  if (!project.value) return;
  try {
    await axios.put(`${baseUrl}/projects/${project.value.id}/comments/${commentId}/read`);
    if (project.value.comments) {
      const updatedComments = project.value.comments.map(c =>
        c.id === commentId ? { ...c, isRead: true } : c
      );
      project.value.comments = updatedComments;
    }
  } catch (error) {
    console.error('Failed to mark comment as read:', error);
    alert('Ошибка при отметке комментария');
  }
};

const hideProjectComment = async (commentId: string) => {
  if (!project.value) return;
  try {
    const response = await axios.delete(`${baseUrl}/projects/${project.value.id}/comments/${commentId}`);
    project.value = response.data;
  } catch (error) {
    console.error('Failed to hide comment:', error);
    alert('Ошибка при скрытии комментария');
  }
};

const permanentDeleteComment = async (commentId: string) => {
  if (!project.value) return;
  try {
    await axios.delete(`${baseUrl}/admin/comments/${commentId}`);
    showNotification('Комментарий удалён навсегда', 'success');
    await loadProject();
  } catch (error) {
    console.error('Failed to delete comment permanently', error);
    showNotification('Ошибка при удалении комментария', 'error');
  }
};

// --- Работа с предложениями ---
const suggestions = computed(() => project.value?.suggestions || []);

const acceptSuggestion = async (suggestionId: string) => {
  if (!project.value) return;
  try {
    const response = await axios.put(`${baseUrl}/projects/${project.value.id}/suggestions/${suggestionId}/accept`);
    project.value = response.data;
  } catch (error) {
    console.error('Failed to accept suggestion:', error);
    alert('Ошибка при принятии предложения');
  }
};

const rejectSuggestion = async (suggestionId: string) => {
  if (!project.value) return;
  try {
    const response = await axios.put(`${baseUrl}/projects/${project.value.id}/suggestions/${suggestionId}/reject`);
    project.value = response.data;
  } catch (error) {
    console.error('Failed to reject suggestion:', error);
    alert('Ошибка при отклонении предложения');
  }
};

const addSuggestionComment = async (suggestionId: string, content: string) => {
  alert('Функция комментариев к предложениям пока не реализована');
};

const markSuggestionCommentRead = async () => {};
const deleteSuggestionComment = async () => {};
const hideSuggestionComment = async () => {};

// --- Приглашения ---
const sendInvite = async (email: string, role: ProjectRole) => {
  if (!project.value) return;
  try {
    const response = await axios.post(`${baseUrl}/projects/${project.value.id}/invite`, { email, role });
    alert(`Приглашение создано, токен: ${response.data.token}`);
  } catch (error) {
    console.error('Failed to create invite:', error);
    alert('Ошибка при создании приглашения');
  }
};

// --- Функции для задач ---
function parseDate(dateStr: string): Date | null {
  if (!dateStr) return null;
  const parts = dateStr.split('.');
  if (parts.length !== 3) return null;
  const [day, month, year] = parts.map(Number);
  return new Date(year, month - 1, day);
}
function formatTaskDates(task: Task): string {
  if (task.timelinend) return `${task.timeline || '?'} – ${task.timelinend}`;
  else if (task.timeline && task.timeline.includes('-')) {
    const parts = task.timeline.split('-');
    return `${parts[0]} – ${parts[1]}`;
  }
  return task.timeline || '?';
}
function isTaskOverdue(task: Task): boolean {
  const today = new Date(); today.setHours(0, 0, 0, 0);
  let endStr = task.timelinend;
  if (!endStr && task.timeline && task.timeline.includes('-')) {
    const parts = task.timeline.split('-');
    endStr = parts[1] || '';
  }
  const endDate = parseDate(endStr || '');
  if (!endDate) return false;
  return today > endDate && task.status !== 'выполнена';
}
function isTaskInvalid(task: Task): boolean {
  let startStr = task.timeline, endStr = task.timelinend;
  if (!endStr && startStr && startStr.includes('-')) {
    const parts = startStr.split('-');
    startStr = parts[0] || '';
    endStr = parts[1] || '';
  }
  const start = parseDate(startStr || '');
  const end = parseDate(endStr || '');
  if (!start || !end) return true;
  return start > end;
}
function isTaskNotStarted(task: Task): boolean {
  if (isTaskInvalid(task) || isTaskOverdue(task)) return false;
  let startStr = task.timeline;
  if (!task.timelinend && startStr && startStr.includes('-')) startStr = startStr.split('-')[0] || '';
  const start = parseDate(startStr || '');
  if (!start) return false;
  const today = new Date(); today.setHours(0, 0, 0, 0);
  return today < start;
}
function isTaskUrgent(task: Task): boolean {
  if (isTaskInvalid(task) || isTaskOverdue(task) || isTaskNotStarted(task)) return false;
  let startStr = task.timeline, endStr = task.timelinend;
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
  const progress = elapsed / totalDuration;
  return progress > 2 / 3 && task.status !== 'выполнена';
}
function taskStatusClass(task: Task): string {
  if (isTaskInvalid(task)) return 'task-invalid';
  if (isTaskOverdue(task)) return 'task-overdue';
  if (isTaskNotStarted(task)) return 'task-not-started';
  if (isTaskUrgent(task)) return 'task-urgent';
  return '';
}

const activeTasks = computed<Task[]>(() => project.value?.tasks?.filter(t => t.status !== 'выполнена') || []);
const completedTasks = computed<Task[]>(() => project.value?.tasks?.filter(t => t.status === 'выполнена') || []);
const inProgressTasks = computed<Task[]>(() => project.value?.tasks?.filter(t => t.status === 'в работе') || []);
const waitingTasks = computed<Task[]>(() => project.value?.tasks?.filter(t => t.status === 'ожидает') || []);

const activeTasksProgress = computed(() => {
  if (!project.value || !activeTasks.value) return [];
  const today = new Date(); today.setHours(0, 0, 0, 0);
  return activeTasks.value.map(task => {
    let startStr = task.timeline || '';
    let endStr = task.timelinend || '';
    if (!endStr && startStr.includes('-')) {
      const parts = startStr.split('-');
      startStr = parts[0] || '';
      endStr = parts[1] || '';
    }
    const startDate = parseDate(startStr);
    const endDate = parseDate(endStr);
    let progress = 0, invalid = false, overdue = false, urgent = false, notStarted = false;
    if (!startDate || !endDate) invalid = true;
    else if (startDate > endDate) invalid = true;
    else {
      if (today < startDate) { notStarted = true; progress = 0; }
      else if (today > endDate) { overdue = true; progress = 100; }
      else {
        const totalDuration = (endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24);
        if (totalDuration > 0) {
          const elapsed = (today.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24);
          progress = (elapsed / totalDuration) * 100;
        } else progress = today >= startDate ? 100 : 0;
        if (progress > 66.6) urgent = true;
      }
    }
    if (isNaN(progress)) progress = 0;
    let barColor = '#42b983';
    if (invalid) barColor = '#9e9e9e';
    else if (overdue) barColor = '#f44336';
    else if (notStarted) barColor = '#bdbdbd';
    else if (urgent) barColor = '#ff9800';
    else {
      const hue = 120 * (1 - progress / 100);
      barColor = `hsl(${Math.max(0, Math.min(120, hue))}, 80%, 50%)`;
    }
    return { title: task.title, startStr, endStr, progress: Math.min(100, Math.max(0, progress)), barColor };
  });
});

const goToTask = (task: Task) => {
  if (!project.value || !project.value.tasks) return;
  const index = project.value.tasks.findIndex(t => t === task);
  if (index !== -1) router.push(`/project/${route.params.id}/task/${index}`);
};

const deleteProject = async () => {
  if (!project.value) return;
  if (confirm('Вы уверены, что хотите удалить проект? Это действие необратимо.')) {
    try {
      await projectsStore.deleteProject(project.value.id);
      router.push('/main');
    } catch (err) {
      console.error('Ошибка при удалении проекта:', err);
      alert('Не удалось удалить проект');
    }
  }
};

const hideProject = async () => {
  if (!project.value) return;
  if (confirm('Скрыть проект из списка? Вы сможете снова его увидеть, если заказчик или куратор вернёт его.')) {
    try {
      await axios.patch(`${baseUrl}/projects/${project.value.id}/hide`);
      showNotification('Проект скрыт', 'success');
      router.push('/main'); // или на список проектов
    } catch (error) {
      console.error('Failed to hide project', error);
      showNotification('Ошибка при скрытии проекта', 'error');
    }
  }
};

const goToEdit = () => router.push(`/project/edit/${route.params.id}`);
const goToSuggest = () => router.push(`/project/edit/${route.params.id}?mode=suggest`);
const goHome = () => router.push('/main');
const goToUser = (userId: number) => router.push(`/user/${userId}`);
const openInviteModal = () => { showInviteModal.value = true; };

const handleAuthorImageError = (id: number) => {
  if (!avatarError.value) avatarError.value = {};
  avatarError.value[id] = true;
};

const avatarError = ref<Record<number, boolean>>({});

function formatDate(dateStr: string) {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  if (diffMins < 1) return 'только что';
  if (diffMins < 60) return `${diffMins} мин назад`;
  if (diffHours < 24) return `${diffHours} ч назад`;
  if (diffDays === 1) return 'вчера';
  if (diffDays < 7) return `${diffDays} дн назад`;
  return date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

const notification = ref({ show: false, message: '', type: 'error' as 'error' | 'info' | 'success' });
let notificationTimeout: number | null = null;
function showNotification(message: string, type: 'error' | 'info' | 'success' = 'error', duration = 5000) {
  if (notificationTimeout) clearTimeout(notificationTimeout);
  notification.value = { show: true, message, type };
  notificationTimeout = window.setTimeout(() => { notification.value.show = false; }, duration);
}
</script>

<style scoped>
.already-responded {
  text-align: center;
  padding: 12px 24px;
  background: rgba(76, 175, 80, 0.1);
  border-radius: 30px;
  border: 2px solid #4caf50;
  color: #4caf50;
  font-weight: 600;
  font-size: 1.1rem;
  margin-bottom: 20px;
}
.responded-message {
  display: inline-block;
}
.project-details-page {
  min-height: 100vh;
  background: var(--bg-page);
  padding: 20px;
  box-sizing: border-box;
  transition: background 0.3s;
}
.details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto 20px;
  flex-wrap: wrap;
  gap: 10px;
}
.author-header {
  justify-content: flex-end;
}
.page-title {
  color: var(--heading-color);
  font-size: 2rem;
  margin: 0;
}
.header-buttons {
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
/* Общие стили */
.project-section {
  margin-bottom: 28px;
}
.project-section h3 {
  color: var(--heading-color);
  margin-bottom: 10px;
  font-weight: 500;
}
.project-section p {
  color: var(--text-primary);
  line-height: 1.6;
}
.participants-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.participant-link {
  cursor: pointer;
  color: var(--link-color);
  text-decoration: underline;
  margin-right: 8px;
  display: inline-block;
}
.participant-link:hover {
  color: var(--link-hover);
}
.role-badge {
  font-size: 0.8rem;
  background: var(--accent-color);
  color: white;
  padding: 2px 6px;
  border-radius: 12px;
  margin-left: 4px;
}
/* Макеты */
.non-author-layout {
  max-width: 800px;
  margin: 0 auto;
}
.project-card {
  background: var(--bg-card);
  border-radius: 24px;
  box-shadow: var(--shadow-strong);
  padding: 30px;
  transition: background 0.3s;
}
.author-layout {
  max-width: 1200px;
  margin: 0 auto;
}
.project-title-center {
  text-align: center;
  color: var(--heading-color);
  font-size: 2.5rem;
  margin-bottom: 30px;
}
.two-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 40px;
}
.info-column, .tasks-column {
  background: var(--bg-column);
  backdrop-filter: blur(4px);
  border-radius: 24px;
  padding: 30px;
  box-shadow: var(--shadow);
  transition: background 0.3s;
}
/* Заголовок и кнопки в правой колонке */
.tasks-section-title {
  color: var(--heading-color);
  font-weight: 500;
  font-size: 1.5rem;
  margin: 0 0 15px 0;
}
.task-header-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}
.suggestions-btn,
.suggest-btn,
.invite-btn,
.comments-header-btn,
.requests-btn {
  background: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 30px;
  padding: 8px 16px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: var(--shadow);
  display: inline-flex;
  align-items: center;
}
.suggestions-btn:hover,
.suggest-btn:hover,
.invite-btn:hover,
.comments-header-btn:hover,
.requests-btn:hover {
  background: var(--accent-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-strong);
}
.btn-content {
  display: flex;
  align-items: center;
  gap: 6px;
}
.suggestions-icon,
.comment-icon,
.requests-icon {
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
/* Контейнеры для комментариев и предложений */
.comments-container,
.suggestions-container,
.requests-container {
  margin-bottom: 25px;
  border: 1px solid var(--border-color);
  border-radius: 16px;
  overflow: hidden;
  width: 100%;
  box-sizing: border-box;
  background: var(--bg-card);
  padding: 15px;
}
/* Специфично для запросов */
.requests-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--border-color);
}
.requests-header h3 {
  color: var(--heading-color);
  font-size: 1.2rem;
  font-weight: 500;
  margin: 0;
}
.pending-badge {
  background: var(--accent-color);
  color: white;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.9rem;
}
.requests-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.request-item {
  background: var(--bg-page);
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  border-left: 4px solid #ff9800;
}
.request-info {
  flex: 1;
  min-width: 200px;
}
.request-user {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.user-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--accent-color);
  color: var(--button-text);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
  overflow: hidden;
}
.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.user-name {
  font-weight: 600;
  color: var(--heading-color);
}
.request-task {
  font-size: 0.9rem;
  color: var(--text-primary);
  margin-bottom: 2px;
}
.request-actions {
  display: flex;
  gap: 8px;
}
.accept-request-btn, .reject-request-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.accept-request-btn {
  background: #4caf50;
  color: white;
}
.accept-request-btn:hover {
  background: #45a049;
}
.reject-request-btn {
  background: #f44336;
  color: white;
}
.reject-request-btn:hover {
  background: #da190b;
}
.no-requests {
  text-align: center;
  color: var(--text-secondary);
  padding: 20px;
  font-style: italic;
}
/* Кнопка отклика на проект */
.respond-project-section {
  margin-bottom: 20px;
  text-align: center;
}
.respond-project-btn {
  background: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 30px;
  padding: 12px 24px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: var(--shadow);
}
.respond-project-btn:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-strong);
}
.respond-project-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
/* Группы задач */
.task-group {
  margin-bottom: 30px;
}
.task-group-title {
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 15px;
  padding-bottom: 5px;
  border-bottom: 2px solid;
}
.task-group-title.in-progress-title {
  color: var(--accent-color);
  border-bottom-color: var(--accent-color);
}
.task-group-title.waiting-title {
  color: #ff9800;
  border-bottom-color: #ff9800;
}
.task-tree {
  display: flex;
  flex-direction: column;
  gap: 15px;
}
.task-node {
  display: flex;
  align-items: flex-start;
  gap: 15px;
  padding: 15px;
  background: var(--bg-card);
  border-radius: 12px;
  box-shadow: var(--shadow);
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  border-left: 4px solid var(--accent-color);
}
.task-node:hover {
  transform: translateX(5px);
  box-shadow: var(--shadow-strong);
}
.task-node.task-overdue {
  background-color: var(--overdue-bg);
  border-left-color: #f44336;
}
.task-node.task-urgent {
  background-color: var(--urgent-bg);
  border-left-color: #ff9800;
}
.task-node.task-invalid {
  background-color: var(--invalid-bg);
  border-left-color: #9e9e9e;
  opacity: 0.7;
}
.task-node.task-not-started {
  background-color: var(--not-started-bg);
  border-left-color: #bdbdbd;
  opacity: 0.8;
}
.task-icon {
  font-size: 1.5rem;
  color: var(--accent-color);
}
.task-content {
  flex: 1;
}
.task-content strong {
  color: var(--heading-color);
  display: block;
  margin-bottom: 4px;
}
.task-status {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-left: 8px;
}
.task-content p {
  color: var(--text-primary);
  margin: 8px 0 4px;
}
.task-progress {
  display: inline-block;
  margin-top: 4px;
  margin-right: 8px;
  font-size: 0.9rem;
  color: var(--heading-color);
  background: var(--completed-bg);
  padding: 2px 8px;
  border-radius: 12px;
}
.task-content small {
  color: var(--text-secondary);
}
.overdue-badge,
.invalid-badge,
.not-started-badge {
  display: inline-block;
  margin-left: 8px;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: bold;
  color: white;
}
.overdue-badge {
  background-color: #f44336;
}
.invalid-badge {
  background-color: #9e9e9e;
}
.not-started-badge {
  background-color: #757575;
}
.assigned-info {
  display: inline-block;
  margin-left: 8px;
  font-size: 0.8rem;
  color: var(--text-secondary);
  background: var(--bg-card);
  padding: 2px 8px;
  border-radius: 12px;
}
.respond-btn {
  background: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 20px;
  padding: 4px 12px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  margin-left: 10px;
  transition: background 0.2s;
  white-space: nowrap;
}
.respond-btn:hover {
  background: var(--accent-hover);
}
.respond-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.no-tasks {
  text-align: center;
  color: var(--text-secondary);
  font-style: italic;
  padding: 20px;
}
/* Диаграмма Ганта */
.gantt-section {
  margin-top: 30px;
  border-top: 2px dashed var(--border-color);
  padding-top: 20px;
}
.gantt-section h3 {
  color: var(--heading-color);
  margin-bottom: 15px;
  font-weight: 500;
  text-align: center;
}
.gantt-chart {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.gantt-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.gantt-label {
  width: 120px;
  font-weight: 500;
  color: var(--heading-color);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.gantt-bar-container {
  position: relative;
  flex: 1;
  height: 24px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.gantt-bar {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 12px;
  transition: background-color 0.2s ease;
}
.gantt-text {
  position: relative;
  z-index: 1;
  color: black;
  font-size: 0.85rem;
  font-weight: 500;
  background-color: transparent;
}
/* Выполненные задачи */
.completed-tasks {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 10px;
}
.completed-task {
  cursor: pointer;
  background: var(--completed-bg);
  padding: 10px;
  border-radius: 8px;
  border-left: 4px solid var(--accent-color);
  transition: transform 0.1s, box-shadow 0.1s;
}
.completed-task:hover {
  transform: translateX(4px);
  box-shadow: var(--shadow);
}
.completed-task-title {
  font-weight: 600;
  color: var(--heading-color);
}
.completed-task-date {
  display: block;
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-top: 4px;
}
/* Кнопки управления проектом (левая колонка) */
.project-actions {
  margin-top: 30px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.edit-project-button,
.delete-project-button {
  flex: 1;
  padding: 12px 20px;
  border: none;
  border-radius: 50px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}
.edit-project-button {
  background: var(--accent-color);
  color: var(--button-text);
}
.edit-project-button:hover {
  background: var(--accent-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-strong);
}
.delete-project-button {
  background: var(--danger-bg);
  color: var(--danger-color);
}
.delete-project-button:hover {
  background: var(--danger-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-strong);
}
/* Ссылки проекта */
.project-links {
  margin-bottom: 28px;
}
.project-links h3 {
  color: var(--heading-color);
  margin-bottom: 10px;
  font-weight: 500;
}
.links-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.link-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 16px;
  border-radius: 50px;
  font-size: 0.95rem;
  font-weight: 500;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}
.link-button .icon {
  width: 20px;
  height: 20px;
  margin-right: 6px;
  object-fit: contain;
}
.add-github,
.add-drive {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}
.add-github:hover,
.add-drive:hover {
  background: var(--bg-page);
  transform: translateY(-2px);
  box-shadow: var(--shadow);
}
.link-input-wrapper {
  display: flex;
  gap: 4px;
  align-items: center;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 50px;
  padding: 4px 4px 4px 12px;
}
.link-input {
  flex: 1;
  min-width: 200px;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 0.95rem;
  outline: none;
}
.link-save,
.link-cancel,
.link-edit,
.link-delete {
  background: transparent;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 50%;
  transition: background 0.2s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.link-save {
  color: #4caf50;
}
.link-save:hover {
  background: rgba(76, 175, 80, 0.2);
}
.link-cancel {
  color: #f44336;
}
.link-cancel:hover {
  background: rgba(244, 67, 54, 0.2);
}
.link-edit {
  color: #ff9800;
}
.link-edit:hover {
  background: rgba(255, 152, 0, 0.2);
}
.link-delete {
  color: #f44336;
}
.link-delete:hover {
  background: rgba(244, 67, 54, 0.2);
}
.link-display {
  display: flex;
  align-items: center;
  gap: 8px;
}
.link-actions {
  display: flex;
  gap: 4px;
}
.github-link {
  background: #24292e;
  color: white;
}
.github-link:hover {
  background: #2c3e50;
  transform: translateY(-2px);
  box-shadow: var(--shadow-strong);
}
.drive-link {
  background: #4285f4;
  color: white;
}
.drive-link:hover {
  background: #3367d6;
  transform: translateY(-2px);
  box-shadow: var(--shadow-strong);
}
.loading,
.error {
  text-align: center;
  color: var(--text-primary);
  font-size: 1.2rem;
  padding: 40px;
}
</style>