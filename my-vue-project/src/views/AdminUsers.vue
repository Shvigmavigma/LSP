<template>
  <div class="admin-users-page">
    <header class="page-header">
      <h1>Управление пользователями</h1>
      <div class="header-actions">
        <ThemeToggle />
        <button class="home-button" @click="goHome" title="На главную">🏠</button>
        <button class="back-button" @click="goBack" title="Назад">◀</button>
      </div>
    </header>

    <div v-if="loading" class="loading">Загрузка...</div>
    <div v-else>
      <div class="filters">
        <input v-model="search" placeholder="Поиск по имени или email" />
        <select v-model="roleFilter">
          <option value="all">Все</option>
          <option value="student">Ученики</option>
          <option value="teacher">Учителя</option>
          <option value="admin">Администраторы</option>
        </select>
      </div>

      <table class="users-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Никнейм</th>
            <th>Email</th>
            <th>Тип</th>
            <th>Активен</th>
            <th>Админ</th>
            <th>Куратор</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in filteredUsers" :key="user.id">
            <td>{{ user.id }}</td>
            <td>{{ user.nickname }}</td>
            <td>{{ user.email }}</td>
            <td>{{ user.is_teacher ? 'Учитель' : 'Ученик' }}</td>
            <td>
              <input type="checkbox" :checked="user.is_active" @change="toggleActive(user)" />
            </td>
            <td>
              <input type="checkbox" :checked="user.is_admin" @change="toggleAdmin(user)" />
            </td>
            <td>
              <template v-if="user.is_teacher">
                <input type="checkbox" :checked="user.teacher_info?.curator" @change="toggleCurator(user)" />
              </template>
              <span v-else>—</span>
            </td>
            <td>
              <button class="edit-btn" @click="editUser(user.id)">✎</button>
              <button class="delete-btn" @click="confirmDelete(user.id)">🗑</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Модальное подтверждение удаления -->
    <Teleport to="body">
      <div v-if="showDeleteModal" class="modal-overlay" @click.self="closeDeleteModal">
        <div class="modal-content">
          <h3>Удалить пользователя</h3>
          <p>Вы уверены, что хотите удалить этого пользователя?</p>
          <div class="modal-actions">
            <button class="confirm-btn" @click="deleteUser">Удалить</button>
            <button class="cancel-btn" @click="closeDeleteModal">Отмена</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import ThemeToggle from '@/components/ThemeToggle.vue';
import axios from 'axios';
import type { User } from '@/types';

const router = useRouter();
const users = ref<User[]>([]);
const loading = ref(true);
const search = ref('');
const roleFilter = ref('all');

const showDeleteModal = ref(false);
const userToDelete = ref<number | null>(null);

onMounted(async () => {
  await loadUsers();
});

async function loadUsers() {
  try {
    const response = await axios.get('/admin/users');
    users.value = response.data;
  } catch (error) {
    console.error('Failed to load users', error);
  } finally {
    loading.value = false;
  }
}

const filteredUsers = computed(() => {
  let filtered = users.value;
  if (search.value) {
    const q = search.value.toLowerCase();
    filtered = filtered.filter(u => u.nickname.toLowerCase().includes(q) || u.email.toLowerCase().includes(q));
  }
  if (roleFilter.value === 'student') {
    filtered = filtered.filter(u => !u.is_teacher);
  } else if (roleFilter.value === 'teacher') {
    filtered = filtered.filter(u => u.is_teacher);
  } else if (roleFilter.value === 'admin') {
    filtered = filtered.filter(u => u.is_admin);
  }
  return filtered;
});

async function toggleActive(user: User) {
  const newValue = !user.is_active;
  try {
    await axios.put(`/admin/users/${user.id}`, { is_active: newValue });
    user.is_active = newValue;
  } catch (error) {
    console.error('Failed to toggle active status', error);
  }
}

async function toggleAdmin(user: User) {
  const newValue = !user.is_admin;
  try {
    await axios.put(`/admin/users/${user.id}`, { is_admin: newValue });
    user.is_admin = newValue;
  } catch (error) {
    console.error('Failed to toggle admin', error);
  }
}

async function toggleCurator(user: User) {
  const newValue = !user.teacher_info?.curator;
  try {
    await axios.put(`/admin/users/${user.id}`, {
      teacher_info: {
        ...user.teacher_info,
        curator: newValue
      }
    });
    if (!user.teacher_info) user.teacher_info = { roles: [], curator: false };
    user.teacher_info.curator = newValue;
  } catch (error) {
    console.error('Failed to toggle curator', error);
  }
}

function editUser(id: number) {
  router.push(`/admin/users/${id}/edit`);
}

function confirmDelete(id: number) {
  userToDelete.value = id;
  showDeleteModal.value = true;
}

function closeDeleteModal() {
  showDeleteModal.value = false;
  userToDelete.value = null;
}

async function deleteUser() {
  if (!userToDelete.value) return;
  try {
    await axios.delete(`/admin/users/${userToDelete.value}`);
    users.value = users.value.filter(u => u.id !== userToDelete.value);
    closeDeleteModal();
  } catch (error) {
    console.error('Failed to delete user', error);
    alert('Ошибка при удалении');
  }
}

function goHome() {
  router.push('/main');
}
function goBack() {
  router.push('/admin');
}
</script>

<style scoped>
/* стили без изменений */
.admin-users-page {
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
.header-actions {
  display: flex;
  gap: 10px;
}
.home-button, .back-button {
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
.filters {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  max-width: 1200px;
  margin: 0 auto 20px;
}
.filters input {
  flex: 1;
  padding: 10px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-primary);
}
.filters select {
  padding: 10px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-primary);
}
.users-table {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  border-collapse: collapse;
  background: var(--bg-card);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: var(--shadow);
}
.users-table th {
  background: var(--bg-page);
  color: var(--heading-color);
  font-weight: 600;
  padding: 12px;
  text-align: left;
  border-bottom: 2px solid var(--border-color);
}
.users-table td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-primary);
}
input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--accent-color);
}
.edit-btn, .delete-btn {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.2s;
}
.edit-btn:hover {
  background: rgba(33, 150, 243, 0.2);
}
.delete-btn:hover {
  background: rgba(244, 67, 54, 0.2);
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