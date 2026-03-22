<template>
  <div class="invite-page">
    <div class="theme-toggle-container">
      <ThemeToggle />
    </div>
    <div class="invite-card">
      <div v-if="loading" class="loading">Загрузка информации...</div>
      <div v-else-if="error" class="error">
        <span class="error-icon">❌</span>
        <h3>Ошибка</h3>
        <p>{{ error }}</p>
        <button class="home-button" @click="goHome">На главную</button>
      </div>
      <div v-else-if="invitation" class="invite-info">
        <div class="invite-icon">✉️</div>
        <h2>Приглашение в проект</h2>
        <p class="project-title">{{ invitation.project_title }}</p>
        <div class="role-info">
          <span class="role-label">Вам предлагается роль:</span>
          <span class="role-badge">{{ getRoleDisplay(invitation.role) }}</span>
        </div>
        <p class="invite-details">
          Приглашение отправил пользователь ID {{ invitation.invited_by }}<br>
          Срок действия: {{ formatDate(invitation.expires_at) }}
        </p>
        <div class="action-buttons">
          <button class="accept-button" @click="acceptInvite" :disabled="accepting">
            {{ accepting ? 'Принятие...' : '✅ Принять приглашение' }}
          </button>
          <button class="cancel-button" @click="goHome">Отмена</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';
import ThemeToggle from '@/components/ThemeToggle.vue';
import type { Invitation, ProjectRole } from '@/types';

const route = useRoute();
const router = useRouter();
const token = route.params.token as string;

const invitation = ref<Invitation | null>(null);
const loading = ref(true);
const error = ref('');
const accepting = ref(false);

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

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString('ru-RU');
}

async function loadInvitation() {
  try {
    const response = await axios.get(`/invite/${token}`);
    invitation.value = response.data;
  } catch (err: any) {
    if (err.response?.status === 404) {
      error.value = 'Приглашение не найдено или истекло';
    } else {
      error.value = 'Ошибка загрузки приглашения';
    }
    console.error(err);
  } finally {
    loading.value = false;
  }
}

async function acceptInvite() {
  accepting.value = true;
  try {
    await axios.post(`/invite/${token}/accept`);
    alert('Вы успешно присоединились к проекту!');
    router.push(`/project/${invitation.value?.project_id}`);
  } catch (err: any) {
    if (err.response?.status === 400) {
      error.value = 'Вы уже являетесь участником этого проекта';
    } else if (err.response?.status === 401) {
      error.value = 'Необходимо войти в систему';
      // можно перенаправить на логин
    } else {
      error.value = 'Ошибка при принятии приглашения';
    }
    console.error(err);
  } finally {
    accepting.value = false;
  }
}

function goHome() {
  router.push('/main');
}

onMounted(loadInvitation);
</script>

<style scoped>
.invite-page {
  min-height: 100vh;
  background: var(--bg-page);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  position: relative;
  padding: 20px;
}
.theme-toggle-container {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 10;
}
.invite-card {
  background: var(--bg-card);
  border-radius: 24px;
  padding: 40px;
  max-width: 500px;
  width: 100%;
  box-shadow: var(--shadow-strong);
  text-align: center;
}
.invite-icon {
  font-size: 4rem;
  margin-bottom: 20px;
}
.project-title {
  font-size: 1.8rem;
  color: var(--heading-color);
  margin-bottom: 20px;
  font-weight: 600;
  word-break: break-word;
}
.role-info {
  margin: 20px 0;
  padding: 15px;
  background: rgba(66, 185, 131, 0.1);
  border-radius: 12px;
}
.role-label {
  color: var(--text-secondary);
  margin-right: 10px;
}
.role-badge {
  background: var(--accent-color);
  color: white;
  padding: 6px 16px;
  border-radius: 30px;
  font-weight: 600;
}
.invite-details {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin: 20px 0;
  line-height: 1.6;
}
.action-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 30px;
}
.accept-button, .cancel-button, .home-button {
  padding: 12px 30px;
  border: none;
  border-radius: 50px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.accept-button {
  background: var(--accent-color);
  color: white;
}
.accept-button:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-2px);
}
.accept-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.cancel-button, .home-button {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}
.cancel-button:hover, .home-button:hover {
  background: var(--bg-page);
}
.loading, .error {
  text-align: center;
  color: var(--text-primary);
  padding: 40px;
}
.error-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 20px;
}
</style>