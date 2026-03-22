<template>
  <div class="comments-section">
    <div class="comments-header">
      <h3>Комментарии</h3>
      <button v-if="canComment && onAddComment" class="add-comment-button" @click="showAddComment = true">
        + Добавить комментарий
      </button>
    </div>

    <!-- Форма добавления комментария -->
    <div v-if="showAddComment" class="add-comment-form">
      <textarea
        v-model="newComment"
        placeholder="Введите комментарий..."
        rows="3"
      ></textarea>
      <div class="form-actions">
        <button @click="saveComment" :disabled="!newComment.trim()" class="save-btn">Отправить</button>
        <button @click="cancelAddComment" class="cancel-btn">Отмена</button>
      </div>
    </div>

    <!-- Список комментариев -->
    <div v-if="sortedComments.length > 0" class="comments-list">
      <div
        v-for="comment in sortedComments"
        :key="comment.id"
        class="comment-item"
        :class="{ 'unread': !comment.isRead && isAuthor, 'hidden': comment.hidden }"
      >
        <div class="comment-header">
          <div class="comment-author">
            <div class="author-avatar">
              <img
                v-if="getAuthorAvatar(comment.authorId)"
                :src="getAuthorAvatar(comment.authorId)"
                :alt="getAuthorNickname(comment.authorId)"
                @error="handleAuthorImageError(comment.authorId)"
              />
              <span v-else>{{ getAuthorInitials(comment.authorId) }}</span>
            </div>
            <div class="author-info">
              <span class="author-name">{{ getAuthorNickname(comment.authorId) }}</span>
              <span v-if="comment.authorRole" class="author-role">{{ comment.authorRole }}</span>
            </div>
          </div>
          <div class="comment-meta">
            <span class="comment-date">{{ formatDate(comment.createdAt) }}</span>
            <span v-if="!comment.isRead && isAuthor" class="unread-badge">Новый</span>

            <!-- Кнопка скрытия для всех, у кого есть права (автор, заказчик, админ, куратор) -->
            <button
              v-if="canHide(comment) && !comment.hidden && onHideComment"
              class="delete-comment-btn"
              @click="confirmHideComment(comment)"
              title="Скрыть комментарий"
            >
              <span class="delete-icon">🗑️</span>
            </button>

            <!-- Кнопка окончательного удаления для скрытых комментариев (только админ/куратор) -->
            <button
              v-if="comment.hidden && (isAdmin || isCurator) && onPermanentDelete"
              class="permanent-delete-btn"
              @click="confirmPermanentDelete(comment)"
              title="Удалить навсегда"
            >
              <span class="delete-icon">🔥</span>
            </button>
          </div>
        </div>
        <div class="comment-content" :class="{ 'hidden-content': comment.hidden }">
          {{ comment.content }}
        </div>
        <!-- Кнопка "Отметить как прочитанное" -->
        <div v-if="!comment.isRead && canComment && onMarkAsRead" class="comment-actions">
          <button @click="markAsRead(comment.id)" class="mark-read-btn">Отметить как прочитанное</button>
        </div>
      </div>
    </div>
    <div v-else class="no-comments">Пока нет комментариев</div>

    <!-- Модальное окно подтверждения скрытия -->
    <div v-if="showHideModal" class="hide-modal-overlay" @click.self="closeHideModal">
      <div class="hide-modal-content">
        <div class="hide-modal-icon">🗑️</div>
        <h3>Скрыть комментарий</h3>
        <p>Вы уверены, что хотите скрыть этот комментарий?</p>
        <p class="comment-preview">"{{ commentToHide?.content.substring(0, 50) }}..."</p>
        <div class="hide-modal-actions">
          <button class="hide-modal-confirm" @click="hideComment">Да, скрыть</button>
          <button class="hide-modal-cancel" @click="closeHideModal">Отмена</button>
        </div>
      </div>
    </div>

    <!-- Модальное окно подтверждения окончательного удаления -->
    <div v-if="showPermanentDeleteModal" class="hide-modal-overlay" @click.self="closePermanentDeleteModal">
      <div class="hide-modal-content">
        <div class="hide-modal-icon">🔥</div>
        <h3>Удалить комментарий навсегда</h3>
        <p>Вы уверены, что хотите полностью удалить этот комментарий? Это действие необратимо.</p>
        <p class="comment-preview">"{{ commentToDeletePermanently?.content.substring(0, 50) }}..."</p>
        <div class="hide-modal-actions">
          <button class="hide-modal-confirm" @click="permanentDeleteComment">Да, удалить</button>
          <button class="hide-modal-cancel" @click="closePermanentDeleteModal">Отмена</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import type { Comment } from '@/types';
import { useUsersStore } from '@/stores/users';
import { useAuthStore } from '@/stores/auth';

const props = defineProps<{
  comments: Comment[];
  canComment: boolean;
  isAuthor: boolean;
  canHideComments?: boolean;
  isAdmin?: boolean;
  isCurator?: boolean;
  onAddComment?: (content: string) => Promise<void>;
  onMarkAsRead?: (commentId: string) => Promise<void>;
  onHideComment?: (commentId: string) => Promise<void>;
  onPermanentDelete?: (commentId: string) => Promise<void>;
}>();

const usersStore = useUsersStore();
const authStore = useAuthStore();

const showAddComment = ref(false);
const newComment = ref('');
const authorImageErrors = ref<Record<number, boolean>>({});
const showHideModal = ref(false);
const commentToHide = ref<Comment | null>(null);
const showPermanentDeleteModal = ref(false);
const commentToDeletePermanently = ref<Comment | null>(null);

const baseUrl = 'http://localhost:8000';

const filteredComments = computed(() => {
  const result = props.isAdmin || props.isCurator
    ? props.comments
    : props.comments.filter(c => !c.hidden);
  return result;
});

const sortedComments = computed(() => {
  return [...filteredComments.value].sort((a, b) =>
    new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  );
});

const canHide = (comment: Comment): boolean => {
  if (props.isAdmin || props.isCurator) return true;
  return props.isAuthor || authStore.user?.id === comment.authorId;
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

const saveComment = async () => {
  if (!newComment.value.trim() || !props.onAddComment) return;
  try {
    await props.onAddComment(newComment.value);
    newComment.value = '';
    showAddComment.value = false;
  } catch (error) {
    console.error('Error saving comment:', error);
    alert('Не удалось отправить комментарий');
  }
};

const cancelAddComment = () => {
  newComment.value = '';
  showAddComment.value = false;
};

const markAsRead = async (commentId: string) => {
  if (props.onMarkAsRead) {
    try {
      await props.onMarkAsRead(commentId);
    } catch (error) {
      console.error('Error marking comment as read:', error);
    }
  }
};

const confirmHideComment = (comment: Comment) => {
  commentToHide.value = comment;
  showHideModal.value = true;
};

const closeHideModal = () => {
  showHideModal.value = false;
  commentToHide.value = null;
};

const hideComment = async () => {
  if (!commentToHide.value || !props.onHideComment) return;
  try {
    await props.onHideComment(commentToHide.value.id);
  } catch (error) {
    console.error('hideComment error', error);
    alert('Не удалось скрыть комментарий');
  } finally {
    closeHideModal();
  }
};

const confirmPermanentDelete = (comment: Comment) => {
  commentToDeletePermanently.value = comment;
  showPermanentDeleteModal.value = true;
};

const closePermanentDeleteModal = () => {
  showPermanentDeleteModal.value = false;
  commentToDeletePermanently.value = null;
};

const permanentDeleteComment = async () => {
  if (!commentToDeletePermanently.value || !props.onPermanentDelete) return;
  try {
    await props.onPermanentDelete(commentToDeletePermanently.value.id);
  } catch (error) {
    console.error('permanentDelete error', error);
    alert('Не удалось удалить комментарий');
  } finally {
    closePermanentDeleteModal();
  }
};
</script>

<style scoped>
.comments-section {
  margin-top: 30px;
  padding: 20px;
  background: var(--bg-card);
  border-radius: 16px;
  box-shadow: var(--shadow);
  position: relative;
  max-width: 100%;
  overflow-x: hidden;
}

.comments-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid var(--border-color);
}

.comments-header h3 {
  color: var(--heading-color);
  font-size: 1.2rem;
  font-weight: 500;
  margin: 0;
}

.add-comment-button {
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

.add-comment-button:hover {
  background: var(--accent-hover);
}

.add-comment-form {
  margin-bottom: 20px;
  padding: 15px;
  background: var(--bg-page);
  border-radius: 12px;
}

.add-comment-form textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-primary);
  font-size: 0.95rem;
  resize: vertical;
  margin-bottom: 10px;
  box-sizing: border-box;
}

.add-comment-form textarea:focus {
  outline: none;
  border-color: var(--accent-color);
}

.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.save-btn, .cancel-btn {
  padding: 8px 20px;
  border: none;
  border-radius: 30px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.save-btn {
  background: var(--accent-color);
  color: var(--button-text);
}

.save-btn:hover:not(:disabled) {
  background: var(--accent-hover);
}

.save-btn:disabled {
  opacity: 0.5;
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

.comments-list {
  max-height: 400px;
  overflow-y: auto;
  padding-right: 5px;
}

.comment-item {
  padding: 15px;
  margin-bottom: 10px;
  background: var(--bg-page);
  border-radius: 12px;
  transition: all 0.2s;
  border-left: 4px solid transparent;
  position: relative;
}

.comment-item.unread {
  border-left-color: var(--accent-color);
  background: rgba(66, 185, 131, 0.05);
}

.comment-item.hidden {
  opacity: 0.5;
  background: var(--bg-card);
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.comment-author {
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

.author-info {
  display: flex;
  flex-direction: column;
}

.author-name {
  color: var(--heading-color);
  font-weight: 600;
  font-size: 0.95rem;
}

.author-role {
  font-size: 0.8rem;
  color: var(--text-secondary);
  font-style: italic;
}

.comment-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.comment-date {
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.unread-badge {
  background: var(--accent-color);
  color: var(--button-text);
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.hide-comment-btn,
.delete-comment-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 6px;
  border-radius: 50%;
  transition: all 0.2s;
  opacity: 0.6;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hide-comment-btn:hover,
.delete-comment-btn:hover {
  opacity: 1;
  background: rgba(128, 128, 128, 0.1);
}

.hide-icon,
.delete-icon {
  font-size: 1.1rem;
}

.comment-content {
  color: var(--text-primary);
  font-size: 0.95rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
  padding-right: 30px;
}

.comment-content.hidden-content {
  font-style: italic;
  color: var(--text-secondary);
}

.comment-actions {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
}

.mark-read-btn {
  background: transparent;
  color: var(--accent-color);
  border: 1px solid var(--accent-color);
  border-radius: 20px;
  padding: 4px 12px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s;
}

.mark-read-btn:hover {
  background: var(--accent-color);
  color: var(--button-text);
}

.no-comments {
  text-align: center;
  color: var(--text-secondary);
  padding: 30px;
  font-style: italic;
}

/* Модальное окно подтверждения скрытия */
.hide-modal-overlay {
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
  animation: fadeIn 0.2s ease;
}

.hide-modal-content {
  background: var(--modal-bg);
  border-radius: 32px;
  padding: 40px;
  max-width: 450px;
  width: 90%;
  box-shadow: var(--shadow-strong);
  animation: slideUp 0.3s ease;
  color: var(--modal-text);
  text-align: center;
  position: relative;
  top: -5vh;
}

.hide-modal-icon {
  font-size: 4rem;
  margin-bottom: 20px;
}

.hide-modal-content h3 {
  color: var(--heading-color);
  margin-bottom: 15px;
  font-weight: 600;
  font-size: 1.8rem;
}

.hide-modal-content p {
  color: var(--text-primary);
  margin-bottom: 10px;
  font-size: 1.1rem;
}

.comment-preview {
  background: var(--bg-page);
  padding: 15px;
  border-radius: 12px;
  margin: 20px 0;
  font-style: italic;
  color: var(--text-secondary);
  border-left: 4px solid var(--accent-color);
  text-align: left;
  max-height: 100px;
  overflow-y: auto;
}

.hide-modal-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 30px;
}

.hide-modal-confirm {
  padding: 12px 30px;
  border: none;
  border-radius: 50px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 140px;
  background: #ff9800;
  color: white;
  box-shadow: 0 4px 10px rgba(255, 152, 0, 0.3);
}

.hide-modal-confirm:hover {
  background: #f57c00;
  transform: translateY(-2px);
  box-shadow: 0 6px 15px rgba(255, 152, 0, 0.4);
}

.hide-modal-cancel {
  padding: 12px 30px;
  border: none;
  border-radius: 50px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 140px;
  background: linear-gradient(135deg, #6b7280, #4b5563);
  color: white;
  box-shadow: 0 4px 10px rgba(75, 85, 99, 0.3);
}

.hide-modal-cancel:hover {
  background: linear-gradient(135deg, #4b5563, #374151);
  transform: translateY(-2px);
  box-shadow: 0 6px 15px rgba(55, 65, 81, 0.4);
}

.permanent-delete-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 6px;
  border-radius: 50%;
  transition: all 0.2s;
  opacity: 0.6;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--danger-color);
}
.permanent-delete-btn:hover {
  opacity: 1;
  background: rgba(244, 67, 54, 0.2);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(30px); opacity: 0; }
  to { transform: translateY(-5vh); opacity: 1; }
}
</style>