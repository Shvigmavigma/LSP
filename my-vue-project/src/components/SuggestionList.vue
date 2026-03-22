<template>
  <div class="suggestions-section">
    <div class="suggestions-header">
      <h3>Предложения по проекту</h3>
      <span v-if="pendingCount > 0" class="pending-badge">{{ pendingCount }} новых</span>
    </div>

    <div v-if="loading" class="loading">Загрузка предложений...</div>
    <div v-else-if="suggestions.length === 0" class="no-suggestions">
      Пока нет предложений
    </div>
    <div v-else class="suggestions-list">
      <div
        v-for="suggestion in sortedSuggestions"
        :key="suggestion.id"
        class="suggestion-item"
        :class="suggestion.status"
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
            <span class="suggestion-status" :class="suggestion.status">
              {{ getStatusText(suggestion.status) }}
            </span>
          </div>
        </div>

        <div class="suggestion-target">
          <span class="target-label">Изменение:</span>
          <span class="target-value">{{ getTargetDisplay(suggestion) }}</span>
        </div>

        <div class="suggestion-changes">
          <pre>{{ formatChanges(suggestion.changes) }}</pre>
        </div>

        <div class="suggestion-actions" v-if="canActOnSuggestion(suggestion)">
          <button
            v-if="suggestion.status === 'pending'"
            class="accept-btn"
            @click="acceptSuggestion(suggestion.id)"
          >✅ Принять</button>
          <button
            v-if="suggestion.status === 'pending'"
            class="reject-btn"
            @click="rejectSuggestion(suggestion.id)"
          >❌ Отклонить</button>
        </div>

        <!-- Комментарии к предложению -->
        <div class="suggestion-comments">
          <button
            class="toggle-comments-btn"
            @click="toggleComments(suggestion.id)"
          >
            💬 Комментарии ({{ suggestion.comments?.length || 0 }})
          </button>
          <div v-if="expandedComments === suggestion.id" class="comments-container">
            <CommentsSection
              :comments="suggestion.comments || []"
              :can-comment="isProjectParticipant"
              :is-author="canEdit"
              :can-hide-comments="canHideComments"
              :on-add-comment="(content) => addSuggestionComment(suggestion.id, content)"
              :on-mark-as-read="(commentId) => markSuggestionCommentRead(suggestion.id, commentId)"
              :on-delete-comment="(commentId) => deleteSuggestionComment(suggestion.id, commentId)"
              :on-hide-comment="(commentId) => hideSuggestionComment(suggestion.id, commentId)"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import type { Suggestion, ProjectRole } from '@/types';
import { useUsersStore } from '@/stores/users';
import { useAuthStore } from '@/stores/auth';
import CommentsSection from './CommentsSection.vue';

const props = defineProps<{
  suggestions: Suggestion[];
  isProjectParticipant: boolean;
  canEdit: boolean; // true для заказчика
  canHideComments: boolean; // true для научрука
  onAccept?: (suggestionId: string) => Promise<void>;
  onReject?: (suggestionId: string) => Promise<void>;
  onAddComment?: (suggestionId: string, content: string) => Promise<void>;
  onMarkCommentRead?: (suggestionId: string, commentId: string) => Promise<void>;
  onDeleteComment?: (suggestionId: string, commentId: string) => Promise<void>;
  onHideComment?: (suggestionId: string, commentId: string) => Promise<void>;
}>();

const usersStore = useUsersStore();
const authStore = useAuthStore();
const loading = ref(false);
const expandedComments = ref<string | null>(null);
const authorImageErrors = ref<Record<number, boolean>>({});

const baseUrl = 'http://localhost:8000';

const pendingCount = computed(() => props.suggestions.filter(s => s.status === 'pending').length);

const sortedSuggestions = computed(() => {
  return [...props.suggestions].sort((a, b) =>
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );
});

// Проверка, может ли текущий пользователь принять/отклонить предложение
const canActOnSuggestion = (suggestion: Suggestion) => {
  if (suggestion.status !== 'pending') return false;
  // Автор предложения может отклонить своё, принять может заказчик
  if (authStore.user?.id === suggestion.author_id) return true;
  if (props.canEdit) return true; // заказчик
  return false;
};

// Получение данных автора
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

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: 'Ожидает',
    accepted: 'Принято',
    rejected: 'Отклонено',
  };
  return map[status] || status;
};

const getTargetDisplay = (suggestion: Suggestion) => {
  switch (suggestion.target_type) {
    case 'project': return 'Проект';
    case 'task': return `Задача #${suggestion.target_id}`;
    case 'link': return 'Ссылки';
    default: return suggestion.target_type;
  }
};

const formatChanges = (changes: any) => {
  return JSON.stringify(changes, null, 2);
};

const toggleComments = (id: string) => {
  expandedComments.value = expandedComments.value === id ? null : id;
};

const acceptSuggestion = async (id: string) => {
  if (props.onAccept) await props.onAccept(id);
};

const rejectSuggestion = async (id: string) => {
  if (props.onReject) await props.onReject(id);
};

const addSuggestionComment = async (suggestionId: string, content: string) => {
  if (props.onAddComment) await props.onAddComment(suggestionId, content);
};

const markSuggestionCommentRead = async (suggestionId: string, commentId: string) => {
  if (props.onMarkCommentRead) await props.onMarkCommentRead(suggestionId, commentId);
};

const deleteSuggestionComment = async (suggestionId: string, commentId: string) => {
  if (props.onDeleteComment) await props.onDeleteComment(suggestionId, commentId);
};

const hideSuggestionComment = async (suggestionId: string, commentId: string) => {
  if (props.onHideComment) await props.onHideComment(suggestionId, commentId);
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
  gap: 20px;
}
.suggestion-item {
  background: var(--bg-page);
  border-radius: 12px;
  padding: 16px;
  border-left: 4px solid;
}
.suggestion-item.pending {
  border-left-color: #ff9800;
}
.suggestion-item.accepted {
  border-left-color: #4caf50;
  opacity: 0.8;
}
.suggestion-item.rejected {
  border-left-color: #f44336;
  opacity: 0.6;
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
.suggestion-status {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: bold;
  color: white;
}
.suggestion-status.pending {
  background: #ff9800;
}
.suggestion-status.accepted {
  background: #4caf50;
}
.suggestion-status.rejected {
  background: #f44336;
}
.suggestion-target {
  margin-bottom: 10px;
  font-size: 0.9rem;
}
.target-label {
  color: var(--text-secondary);
  margin-right: 6px;
}
.target-value {
  font-weight: 500;
  color: var(--heading-color);
}
.suggestion-changes {
  background: var(--bg-card);
  padding: 10px;
  border-radius: 8px;
  overflow-x: auto;
  margin-bottom: 10px;
}
.suggestion-changes pre {
  margin: 0;
  color: var(--text-primary);
  font-family: monospace;
  font-size: 0.85rem;
  white-space: pre-wrap;
  word-wrap: break-word;
}
.suggestion-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
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
.accept-btn:hover {
  background: #45a049;
}
.reject-btn {
  background: #f44336;
  color: white;
}
.reject-btn:hover {
  background: #da190b;
}
.toggle-comments-btn {
  background: none;
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: 6px 12px;
  font-size: 0.9rem;
  cursor: pointer;
  color: var(--text-primary);
  transition: all 0.2s;
}
.toggle-comments-btn:hover {
  background: var(--bg-card);
}
.comments-container {
  margin-top: 15px;
  border-top: 1px solid var(--border-color);
  padding-top: 15px;
}
.loading, .no-suggestions {
  text-align: center;
  color: var(--text-secondary);
  padding: 20px;
}
</style>