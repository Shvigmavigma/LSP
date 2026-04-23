<template>
  <Teleport to="body">
    <div v-if="show" class="modal-overlay" @click.self="close">
      <div class="modal-content">
        <h3>{{ $t('inviteModal.title') }}</h3>
        <form @submit.prevent="submit">
          <!-- Поле поиска пользователя -->
          <div class="form-group">
            <label for="search">{{ $t('inviteModal.userSearchLabel') }}</label>
            <input
              id="search"
              v-model="searchQuery"
              type="text"
              :placeholder="$t('inviteModal.userSearchPlaceholder')"
              @input="searchUsers"
              autocomplete="off"
            />
            <div v-if="searchResults.length > 0" class="search-results">
              <div
                v-for="user in searchResults"
                :key="user.id"
                class="search-result-item"
                @click="selectUser(user)"
              >
                <div class="result-info">
                  <div class="user-nickname">{{ user.nickname }}</div>
                  <div class="user-email">{{ user.email }}</div>
                  <div class="user-available-roles">
                    {{ getAvailableRolesHint(user) }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Выбранный пользователь -->
          <div v-if="selectedUser" class="selected-user">
            <span class="selected-label">{{ $t('inviteModal.selectedUser') }}:</span>
            <span class="selected-value">{{ selectedUser.nickname }} ({{ selectedUser.email }})</span>
            <button type="button" class="clear-selection" @click="clearSelection">✕</button>
          </div>

          <!-- Выбор роли (только доступные) -->
          <div class="form-group">
            <label for="role">{{ $t('inviteModal.roleLabel') }}</label>
            <select id="role" v-model="role" required>
              <option
                v-for="availableRole in availableRoles"
                :key="availableRole"
                :value="availableRole"
              >
                {{ getRoleDisplay(availableRole) }}
              </option>
            </select>
            <small v-if="availableRoles.length === 0" class="no-roles-hint">
              {{ $t('inviteModal.noAvailableRoles') }}
            </small>
          </div>

          <div class="modal-actions">
            <button type="submit" class="invite-btn" :disabled="sending || !selectedUser || availableRoles.length === 0">
              {{ sending ? $t('common.sending') : $t('inviteModal.sendButton') }}
            </button>
            <button type="button" class="cancel-btn" @click="close">{{ $t('common.cancel') }}</button>
          </div>
        </form>

        <!-- Сообщение об ошибке -->
        <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '@/stores/auth';
import type { ProjectRole, User } from '@/types';
import axios from 'axios';

const { t } = useI18n();
const authStore = useAuthStore();

const props = defineProps<{
  show: boolean;
  projectId?: number;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'invite', userId: number, role: ProjectRole): void;
}>();

const searchQuery = ref('');
const searchResults = ref<User[]>([]);
const selectedUser = ref<User | null>(null);
const role = ref<ProjectRole>('executor');
const sending = ref(false);
const errorMessage = ref('');

let searchTimer: ReturnType<typeof setTimeout> | null = null;

// Функция для получения доступных ролей пользователя
function getAvailableRolesForUser(user: User): ProjectRole[] {
  if (!user.is_teacher) {
    // Ученики могут быть только исполнителями
    return ['executor'];
  }

  const roles: ProjectRole[] = [];

  // Роли из teacher_info
  const teacherRoles = user.teacher_info?.roles || [];
  if (teacherRoles.includes('customer')) roles.push('customer');
  if (teacherRoles.includes('expert')) roles.push('expert');
  if (teacherRoles.includes('supervisor')) roles.push('supervisor');

  // Все учителя могут быть исполнителями (если не добавлена роль executor, добавляем)
  if (!roles.includes('executor')) roles.push('executor');

  // Кураторство – отдельная роль
  if (user.teacher_info?.curator) {
    roles.push('curator');
  }

  return roles;
}

// Текстовая подсказка для отображения в результатах поиска
function getAvailableRolesHint(user: User): string {
  const roles = getAvailableRolesForUser(user);
  const roleNames = roles.map(r => getRoleDisplay(r));
  return `${t('inviteModal.availableRoles')}: ${roleNames.join(', ')}`;
}

// Доступные роли для выбранного пользователя
const availableRoles = computed<ProjectRole[]>(() => {
  if (!selectedUser.value) return [];
  return getAvailableRolesForUser(selectedUser.value);
});

// При выборе пользователя сбрасываем роль на первую доступную
watch(selectedUser, (newUser) => {
  if (newUser) {
    const roles = getAvailableRolesForUser(newUser);
    if (roles.length > 0) {
      role.value = roles[0];
    }
  }
});

// Сброс состояния при открытии модалки
watch(() => props.show, (val) => {
  if (val) {
    searchQuery.value = '';
    searchResults.value = [];
    selectedUser.value = null;
    role.value = 'executor';
    sending.value = false;
    errorMessage.value = '';
  }
});

async function searchUsers() {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(async () => {
    const query = searchQuery.value.trim();
    if (!query) {
      searchResults.value = [];
      return;
    }
    try {
      const response = await axios.get('/users/', {
        params: { q: query }
      });
      // Исключаем текущего пользователя из результатов
      const currentUserId = authStore.user?.id;
      searchResults.value = response.data.filter((u: User) => u.id !== currentUserId);
    } catch (err) {
      console.error('Error searching users:', err);
    }
  }, 300);
}

function selectUser(user: User) {
  selectedUser.value = user;
  searchQuery.value = '';
  searchResults.value = [];
  errorMessage.value = '';
}

function clearSelection() {
  selectedUser.value = null;
}

async function submit() {
  if (!selectedUser.value || !role.value || !props.projectId) return;
  sending.value = true;
  errorMessage.value = '';
  try {
    await axios.post('/invitations', {
      project_id: props.projectId,
      invited_user_id: selectedUser.value.id,
      role: role.value
    });
    emit('invite', selectedUser.value.id, role.value);
    close();
  } catch (err: any) {
    console.error('Invite error:', err);
    errorMessage.value = err.response?.data?.detail || t('inviteModal.inviteError');
  } finally {
    sending.value = false;
  }
}

function close() {
  emit('close');
}

function getRoleDisplay(role: ProjectRole): string {
  const map: Record<ProjectRole, string> = {
    customer: t('roles.customer'),
    supervisor: t('roles.supervisor'),
    expert: t('roles.expert'),
    executor: t('roles.executor'),
    curator: t('roles.curator'),
  };
  return map[role];
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(5px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}
.modal-content {
  background: var(--modal-bg);
  border-radius: 32px;
  padding: 30px;
  max-width: 450px;
  width: 90%;
  box-shadow: var(--shadow-strong);
  color: var(--modal-text);
}
.modal-content h3 {
  color: var(--heading-color);
  margin-bottom: 20px;
  font-weight: 500;
}
.form-group {
  margin-bottom: 20px;
  position: relative;
}
.form-group label {
  display: block;
  margin-bottom: 6px;
  color: var(--text-secondary);
  font-weight: 500;
}
.form-group input,
.form-group select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-primary);
  font-size: 1rem;
  outline: none;
}
.form-group input:focus,
.form-group select:focus {
  border-color: var(--accent-color);
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.2);
}
.no-roles-hint {
  display: block;
  margin-top: 6px;
  color: var(--danger-color);
  font-size: 0.8rem;
}
.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  max-height: 200px;
  overflow-y: auto;
  z-index: 10;
  box-shadow: var(--shadow);
  margin-top: 4px;
}
.search-result-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  cursor: pointer;
  border-bottom: 1px solid var(--border-color);
  transition: background 0.2s;
}
.search-result-item:hover {
  background: var(--bg-page);
}
.result-info {
  flex: 1;
}
.user-nickname {
  font-weight: 500;
  color: var(--heading-color);
}
.user-email {
  font-size: 0.75rem;
  color: var(--text-secondary);
}
.user-available-roles {
  font-size: 0.7rem;
  color: var(--accent-color);
  margin-top: 2px;
}
.selected-user {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: rgba(66, 185, 131, 0.1);
  border-radius: 8px;
  margin-bottom: 20px;
}
.selected-label {
  font-weight: 500;
  color: var(--text-secondary);
}
.selected-value {
  flex: 1;
  color: var(--text-primary);
}
.clear-selection {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: var(--danger-color);
  padding: 0 4px;
}
.error-message {
  margin-top: 16px;
  padding: 10px;
  background: rgba(244, 67, 54, 0.1);
  border-radius: 8px;
  color: var(--danger-color);
  text-align: center;
  font-size: 0.9rem;
}
.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 20px;
}
.invite-btn, .cancel-btn {
  padding: 10px 25px;
  border: none;
  border-radius: 30px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.invite-btn {
  background: var(--accent-color);
  color: var(--button-text);
}
.invite-btn:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: scale(1.02);
}
.invite-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.cancel-btn {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}
.cancel-btn:hover {
  background: var(--bg-page);
}
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>