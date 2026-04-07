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
                <span class="user-nickname">{{ user.nickname }}</span>
                <span class="user-email">{{ user.email }}</span>
              </div>
            </div>
          </div>

          <!-- Выбранный пользователь -->
          <div v-if="selectedUser" class="selected-user">
            <span class="selected-label">{{ $t('inviteModal.selectedUser') }}:</span>
            <span class="selected-value">{{ selectedUser.nickname }} ({{ selectedUser.email }})</span>
            <button type="button" class="clear-selection" @click="clearSelection">✕</button>
          </div>

          <!-- Выбор роли -->
          <div class="form-group">
            <label for="role">{{ $t('inviteModal.roleLabel') }}</label>
            <select id="role" v-model="role" required>
              <option value="executor">{{ $t('roles.executor') }}</option>
              <option value="customer">{{ $t('roles.customer') }}</option>
              <option value="supervisor">{{ $t('roles.supervisor') }}</option>
              <option value="expert">{{ $t('roles.expert') }}</option>
              <option value="curator">{{ $t('roles.curator') }}</option>
            </select>
          </div>

          <div class="modal-actions">
            <button type="submit" class="invite-btn" :disabled="sending || !selectedUser">
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
import { ref, watch } from 'vue'; // computed не нужен, но если ошибка остаётся, добавьте его
import { useI18n } from 'vue-i18n';
import type { ProjectRole, User } from '@/types';
import axios from 'axios';

const { t } = useI18n();

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
    if (!searchQuery.value.trim()) {
      searchResults.value = [];
      return;
    }
    try {
      const response = await axios.get('/users/', {
        params: { q: searchQuery.value }
      });
      // Исключаем текущего пользователя из результатов
      searchResults.value = response.data.filter((u: User) => u.id !== props.projectId);
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
.search-wrapper {
  position: relative;
}
.search-spinner {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  border: 2px solid var(--text-secondary);
  border-top-color: var(--accent-color);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin {
  to { transform: translateY(-50%) rotate(360deg); }
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
.result-avatar {
  width: 32px;
  height: 32px;
  background: var(--accent-color);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 0.9rem;
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
.no-results {
  padding: 8px 12px;
  color: var(--text-secondary);
  font-size: 0.85rem;
  text-align: center;
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
.btn-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid white;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
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