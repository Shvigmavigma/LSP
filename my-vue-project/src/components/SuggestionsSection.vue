<!-- src/components/SuggestionsSection.vue (обновлённый) -->
<template>
  <div class="suggestions-section">
    <div class="suggestions-header">
      <h3>Предложения по проекту</h3>
      <span v-if="pendingCount > 0" class="pending-badge">{{ pendingCount }} новых</span>
    </div>

    <div v-if="loading" class="loading">Загрузка предложений...</div>
    <div v-else-if="pendingSuggestions.length === 0" class="no-suggestions">
      Нет ожидающих предложений
    </div>
    <div v-else class="suggestions-list">
      <div
        v-for="suggestion in pendingSuggestions"
        :key="suggestion.id"
        class="suggestion-item"
        @click="openSuggestionModal(suggestion)"
      >
        <div class="suggestion-header">
          <div class="suggestion-author">
            <div class="author-avatar">
              <img
                v-if="getAuthorAvatar(suggestion.author_id)"
                :src="getAuthorAvatar(suggestion.author_id)"
                :alt="getAuthorNickname(suggestion.author_id)"
                @error="handleAuthorImageError(suggestion.author_id)"
              />
              <span v-else>{{ getAuthorInitials(suggestion.author_id) }}</span>
            </div>
            <span class="author-name">{{ getAuthorNickname(suggestion.author_id) }}</span>
          </div>
          <div class="suggestion-meta">
            <span class="suggestion-date">{{ formatDate(suggestion.created_at) }}</span>
            <span class="suggestion-target-type">{{ getTargetTypeLabel(suggestion.target_type) }}</span>
          </div>
        </div>

        <div class="suggestion-preview">
          <div class="suggestion-changes-preview">
            <div v-for="(value, key) in getPreviewChanges(suggestion.changes)" :key="key" class="change-preview-item">
              <span class="change-key">{{ formatKey(key) }}:</span>
              <span class="change-value">{{ formatPreviewValue(value) }}</span>
            </div>
          </div>
        </div>

        <div class="suggestion-actions" @click.stop>
          <button
            class="accept-btn"
            @click="applySuggestion(suggestion)"
            :disabled="actionInProgress"
          >✎ Редактировать и принять</button>
          <button
            class="reject-btn"
            @click="rejectSuggestion(suggestion.id)"
            :disabled="actionInProgress"
          >❌ Отклонить</button>
        </div>
      </div>
    </div>

    <!-- Модальное окно с деталями предложения -->
    <Teleport to="body">
      <div v-if="selectedSuggestion" class="suggestion-modal-overlay" @click.self="closeModal">
        <div class="suggestion-modal">
          <div class="modal-header">
            <h3>Детали предложения</h3>
            <button class="close-btn" @click="closeModal">✕</button>
          </div>
          <div class="modal-body">
            <div class="suggestion-info">
              <div class="info-row">
                <span class="info-label">Автор:</span>
                <span class="info-value">{{ getAuthorNickname(selectedSuggestion.author_id) }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">Дата:</span>
                <span class="info-value">{{ formatDate(selectedSuggestion.created_at) }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">Тип:</span>
                <span class="info-value">{{ getTargetTypeLabel(selectedSuggestion.target_type) }}</span>
              </div>
              <div v-if="selectedSuggestion.target_id" class="info-row">
                <span class="info-label">Цель:</span>
                <span class="info-value">
                  <router-link :to="getTargetLink(selectedSuggestion)" class="target-link">
                    {{ getTargetName(selectedSuggestion) }}
                  </router-link>
                </span>
              </div>
            </div>

            <div class="suggestion-changes-full">
              <h4>Предлагаемые изменения</h4>
              <div v-for="(value, key) in selectedSuggestion.changes" :key="key" class="change-item">
                <div class="change-key">{{ formatKey(key) }}</div>
                <div class="change-value">{{ formatValue(value) }}</div>
              </div>
            </div>
          </div>
          <div class="modal-actions">
            <button
              class="accept-btn"
              @click="applySuggestion(selectedSuggestion)"
              :disabled="actionInProgress"
            >✎ Редактировать и принять</button>
            <button
              class="reject-btn"
              @click="rejectSuggestion(selectedSuggestion.id)"
              :disabled="actionInProgress"
            >❌ Отклонить</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import type { Suggestion } from '@/types';
import { useUsersStore } from '@/stores/users';
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';

const props = defineProps<{
  projectId: number;
  suggestions: Suggestion[];
  isProjectParticipant: boolean;
  canEdit: boolean; // true для заказчика
  canHideComments?: boolean;
  onReject?: (suggestionId: string) => Promise<void>;
}>();

const usersStore = useUsersStore();
const authStore = useAuthStore();
const router = useRouter();

const loading = ref(false);
const actionInProgress = ref(false);
const selectedSuggestion = ref<Suggestion | null>(null);
const authorImageErrors = ref<Record<number, boolean>>({});

const baseUrl = 'http://localhost:8000';

// Логируем полученные предложения
watch(() => props.suggestions, (newVal) => {
  console.log('📥 SuggestionsSection received suggestions:', JSON.parse(JSON.stringify(newVal)));
}, { deep: true, immediate: true });

// Показываем только ожидающие предложения
const pendingSuggestions = computed(() => {
  const result = props.suggestions.filter(s => s.status === 'pending');
  console.log('🔍 pendingSuggestions computed:', JSON.parse(JSON.stringify(result)));
  return result;
});

const pendingCount = computed(() => pendingSuggestions.value.length);

const getAuthorNickname = (id: number): string => {
  const user = usersStore.users.find(u => u.id === id);
  return user ? user.nickname : `ID: ${id}`;
};

const getAuthorAvatar = (id: number): string | undefined => {
  if (authorImageErrors.value[id]) return undefined;
  const user = usersStore.users.find(u => u.id === id);
  return user?.avatar ? `${baseUrl}/avatars/${user.avatar}` : undefined;
};

const getAuthorInitials = (id: number): string => {
  const user = usersStore.users.find(u => u.id === id);
  return user?.nickname?.charAt(0).toUpperCase() || '?';
};

const handleAuthorImageError = (id: number) => {
  authorImageErrors.value[id] = true;
};

const formatDate = (dateStr: string) => {
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
  return date.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const getTargetTypeLabel = (type: string) => {
  const map: Record<string, string> = {
    project: 'Проект',
    task: 'Задача',
    link: 'Ссылки'
  };
  return map[type] || type;
};

const getTargetLink = (suggestion: Suggestion) => {
  if (suggestion.target_type === 'task') {
    return `/project/${props.projectId}/task/${suggestion.target_id}`;
  }
  return `/project/${props.projectId}`;
};

const getTargetName = (suggestion: Suggestion) => {
  if (suggestion.target_type === 'task') {
    return `Задача #${suggestion.target_id}`;
  }
  return 'Проект';
};

// Для предпросмотра показываем только первые 2-3 изменения
const getPreviewChanges = (changes: Record<string, any>) => {
  const entries = Object.entries(changes).slice(0, 3);
  return Object.fromEntries(entries);
};

const formatPreviewValue = (val: any) => {
  if (val === null || val === undefined) return '';
  if (typeof val === 'object') {
    return JSON.stringify(val).substring(0, 30) + '…';
  }
  return String(val).substring(0, 30) + (String(val).length > 30 ? '…' : '');
};

const formatKey = (key: string) => {
  const map: Record<string, string> = {
    title: 'Название',
    body: 'Описание',
    underbody: 'Дополнительно',
    participants: 'Участники',
    tasks: 'Задачи',
    links: 'Ссылки',
  };
  return map[key] || key;
};

const formatValue = (val: any) => {
  if (val === null || val === undefined) return '';
  if (typeof val === 'object') {
    return JSON.stringify(val, null, 2);
  }
  return String(val);
};

const openSuggestionModal = (suggestion: Suggestion) => {
  selectedSuggestion.value = suggestion;
};

const closeModal = () => {
  selectedSuggestion.value = null;
};

// Вместо немедленного принятия переходим на страницу редактирования с query-параметром
const applySuggestion = (suggestion: Suggestion) => {
  router.push({
    path: `/project/edit/${props.projectId}`,
    query: { suggestion: suggestion.id }
  });
};

const rejectSuggestion = async (id: string) => {
  if (actionInProgress.value || !props.onReject) return;
  actionInProgress.value = true;
  try {
    console.log('🚀 rejectSuggestion called in SuggestionsSection with id:', id);
    await props.onReject(id);
    console.log('✅ rejectSuggestion completed');
  } catch (error) {
    console.error('❌ rejectSuggestion error:', error);
  } finally {
    actionInProgress.value = false;
    closeModal();
  }
};
</script>

<style scoped>
.suggestions-section {
  margin-top: 30px;
  padding: 20px;
  background: var(--bg-card);
  border-radius: 16px;
  box-shadow: var(--shadow);
}
.suggestions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid var(--border-color);
}
.suggestions-header h3 {
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
.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}
.suggestion-item {
  background: var(--bg-page);
  border-radius: 12px;
  padding: 16px;
  border-left: 4px solid #ff9800;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}
.suggestion-item:hover {
  transform: translateX(5px);
  box-shadow: var(--shadow-strong);
}
.suggestion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.suggestion-author {
  display: flex;
  align-items: center;
  gap: 8px;
}
.author-avatar {
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
.author-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.author-name {
  color: var(--heading-color);
  font-weight: 600;
  font-size: 0.95rem;
}
.suggestion-meta {
  display: flex;
  gap: 10px;
  align-items: center;
}
.suggestion-date {
  color: var(--text-secondary);
  font-size: 0.85rem;
}
.suggestion-target-type {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: bold;
  background: var(--accent-color);
  color: white;
}
.suggestion-preview {
  margin-bottom: 12px;
}
.suggestion-changes-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  font-size: 0.9rem;
  color: var(--text-secondary);
}
.change-preview-item {
  display: flex;
  gap: 4px;
  background: var(--bg-card);
  padding: 4px 8px;
  border-radius: 16px;
}
.change-key {
  font-weight: 600;
  color: var(--heading-color);
}
.change-value {
  color: var(--text-primary);
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.suggestion-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}
.accept-btn, .reject-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.accept-btn {
  background: #4caf50;
  color: white;
}
.accept-btn:hover:not(:disabled) {
  background: #45a049;
}
.reject-btn {
  background: #f44336;
  color: white;
}
.reject-btn:hover:not(:disabled) {
  background: #da190b;
}
.accept-btn:disabled,
.reject-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Модальное окно */
.suggestion-modal-overlay {
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
.suggestion-modal {
  background: var(--modal-bg);
  border-radius: 24px;
  padding: 24px;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: var(--shadow-strong);
  color: var(--modal-text);
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.modal-header h3 {
  color: var(--heading-color);
  margin: 0;
  font-weight: 500;
}
.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--text-secondary);
  padding: 4px;
  line-height: 1;
}
.close-btn:hover {
  color: var(--heading-color);
}
.modal-body {
  margin-bottom: 20px;
}
.suggestion-info {
  background: var(--bg-page);
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 16px;
}
.info-row {
  display: flex;
  gap: 8px;
  margin-bottom: 6px;
}
.info-label {
  font-weight: 600;
  color: var(--text-secondary);
  min-width: 60px;
}
.info-value {
  color: var(--text-primary);
}
.target-link {
  color: var(--link-color);
  text-decoration: underline;
}
.target-link:hover {
  color: var(--link-hover);
}
.suggestion-changes-full {
  background: var(--bg-page);
  padding: 12px;
  border-radius: 8px;
}
.suggestion-changes-full h4 {
  margin-top: 0;
  margin-bottom: 12px;
  color: var(--heading-color);
  font-weight: 500;
}
.change-item {
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
}
.change-item:last-child {
  border-bottom: none;
}
.change-key {
  font-weight: 600;
  color: var(--heading-color);
  margin-bottom: 4px;
}
.change-value {
  color: var(--text-primary);
  white-space: pre-wrap;
  font-family: monospace;
  font-size: 0.9rem;
  background: var(--bg-card);
  padding: 8px;
  border-radius: 4px;
  overflow-x: auto;
}
.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}
.loading, .no-suggestions {
  text-align: center;
  color: var(--text-secondary);
  padding: 20px;
}
</style>