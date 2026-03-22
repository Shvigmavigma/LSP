<template>
  <div class="admin-panel">
    <header class="page-header">
      <h1>Административная панель</h1>
      <div class="header-actions">
        <ThemeToggle />
        <button class="home-button" @click="goHome" title="На главную">🏠</button>
      </div>
    </header>

    <div class="admin-menu">
      <div class="menu-grid">
        <router-link to="/admin/users" class="menu-card">
          <span class="card-icon">👥</span>
          <span class="card-title">Управление пользователями</span>
          <span class="card-desc">Просмотр, редактирование, удаление, выдача прав</span>
        </router-link>

        <router-link to="/admin/projects" class="menu-card">
          <span class="card-icon">📁</span>
          <span class="card-title">Управление проектами</span>
          <span class="card-desc">Просмотр, редактирование, удаление проектов и задач</span>
        </router-link>

        <div class="menu-card danger" @click="confirmDeleteAllUsers">
          <span class="card-icon">⚠️</span>
          <span class="card-title">Удалить всех пользователей</span>
          <span class="card-desc">Необратимое удаление всех аккаунтов</span>
        </div>

        <div class="menu-card danger" @click="confirmDeleteAllProjects">
          <span class="card-icon">⚠️</span>
          <span class="card-title">Удалить все проекты</span>
          <span class="card-desc">Необратимое удаление всех проектов</span>
        </div>
      </div>
    </div>

    <!-- Модальное подтверждение -->
    <Teleport to="body">
      <div v-if="showConfirmModal" class="modal-overlay" @click.self="closeModal">
        <div class="modal-content">
          <h3>{{ confirmTitle }}</h3>
          <p>{{ confirmMessage }}</p>
          <div class="modal-actions">
            <button class="confirm-btn" @click="executeAction">Подтвердить</button>
            <button class="cancel-btn" @click="closeModal">Отмена</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import ThemeToggle from '@/components/ThemeToggle.vue';
import axios from 'axios';

const router = useRouter();
const showConfirmModal = ref(false);
const confirmTitle = ref('');
const confirmMessage = ref('');
let action: 'deleteUsers' | 'deleteProjects' | null = null;

function goHome() {
  router.push('/main');
}

function confirmDeleteAllUsers() {
  confirmTitle.value = 'Удаление всех пользователей';
  confirmMessage.value = 'Вы уверены, что хотите удалить ВСЕХ пользователей? Это действие необратимо.';
  action = 'deleteUsers';
  showConfirmModal.value = true;
}

function confirmDeleteAllProjects() {
  confirmTitle.value = 'Удаление всех проектов';
  confirmMessage.value = 'Вы уверены, что хотите удалить ВСЕ проекты? Это действие необратимо.';
  action = 'deleteProjects';
  showConfirmModal.value = true;
}

function closeModal() {
  showConfirmModal.value = false;
  action = null;
}

async function executeAction() {
  if (action === 'deleteUsers') {
    try {
      await axios.delete('/admin/users/all');
      alert('Все пользователи удалены');
    } catch (error) {
      console.error(error);
      alert('Ошибка при удалении');
    }
  } else if (action === 'deleteProjects') {
    try {
      await axios.delete('/admin/projects/all');
      alert('Все проекты удалены');
    } catch (error) {
      console.error(error);
      alert('Ошибка при удалении');
    }
  }
  closeModal();
}
</script>

<style scoped>
.admin-panel {
  min-height: 100vh;
  background: var(--bg-page);
  padding: 20px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto 20px;
}
.page-header h1 {
  color: var(--heading-color);
  font-size: 2rem;
  margin: 0;
}
.header-actions {
  display: flex;
  gap: 10px;
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
.admin-menu {
  max-width: 1200px;
  margin: 0 auto;
}
.menu-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}
.menu-card {
  background: var(--bg-card);
  border-radius: 16px;
  padding: 20px;
  box-shadow: var(--shadow);
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
  text-decoration: none;
  color: inherit;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border-color);
}
.menu-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-strong);
}
.menu-card.danger {
  border-color: var(--danger-color);
}
.menu-card.danger .card-icon {
  color: var(--danger-color);
}
.card-icon {
  font-size: 2.5rem;
  margin-bottom: 10px;
}
.card-title {
  font-size: 1.3rem;
  font-weight: 600;
  color: var(--heading-color);
  margin-bottom: 5px;
}
.card-desc {
  color: var(--text-secondary);
  font-size: 0.9rem;
}
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}
.modal-content {
  background: var(--modal-bg);
  border-radius: 24px;
  padding: 30px;
  max-width: 400px;
  width: 90%;
  box-shadow: var(--shadow-strong);
}
.modal-content h3 {
  color: var(--heading-color);
  margin-bottom: 10px;
}
.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}
.confirm-btn {
  background: var(--danger-color);
  color: white;
  border: none;
  border-radius: 30px;
  padding: 10px 20px;
  cursor: pointer;
}
.cancel-btn {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  border-radius: 30px;
  padding: 10px 20px;
  cursor: pointer;
}
</style>