<template>
  <div class="admin-users-page">
    <header class="page-header">
      <h1>{{ $t('adminUsers.title') }}</h1>
      <div class="header-actions">
        <button class="create-user-btn" @click="goToCreateUser" :title="$t('adminUsers.createUser')">
          {{ $t('adminUsers.createUser') }}
        </button>
        <ThemeToggle />
        <LanguageSwitcher />
        <HomeButton/>
        <button class="back-button" @click="goBack" :title="$t('common.back')">◀</button>
      </div>
    </header>

    <div v-if="loading" class="loading">{{ $t('common.loading') }}</div>
    <div v-else>
      <div class="filters">
        <input v-model="search" :placeholder="$t('adminUsers.searchPlaceholder')" />
        <select v-model="roleFilter">
          <option value="all">{{ $t('adminUsers.filterAll') }}</option>
          <option value="student">{{ $t('adminUsers.filterStudents') }}</option>
          <option value="teacher">{{ $t('adminUsers.filterTeachers') }}</option>
          <option value="admin">{{ $t('adminUsers.filterAdmins') }}</option>
          <option value="curator">{{ $t('adminUsers.filterCurators') }}</option>
        </select>
      </div>

      <table class="users-table">
        <thead>
          <tr>
            <th>{{ $t('adminUsers.table.id') }}</th>
            <th>{{ $t('adminUsers.table.fullname') }}</th>
            <th>{{ $t('adminUsers.table.email') }}</th>
            <th>{{ $t('adminUsers.table.type') }}</th>
            <th>{{ $t('adminUsers.table.active') }}</th>
            <th>{{ $t('adminUsers.table.isTeacher') }}</th>
            <th>{{ $t('adminUsers.table.admin') }}</th>
            <th>{{ $t('adminUsers.table.curator') }}</th>
            <th>{{ $t('adminUsers.table.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in filteredUsers" :key="user.id">
            <td>{{ user.id }}</td>
            <td>
              <router-link :to="`/user/${user.id}`" class="user-link">
                {{ displayUserName(user) }}
              </router-link>
            </td>
            <td>{{ user.email }}</td>
            <td>{{ user.is_teacher ? $t('adminUsers.userType.teacher') : $t('adminUsers.userType.student') }}</td>
            <td>
              <input type="checkbox" :checked="user.is_active === true" @change="toggleActive(user)" />
            </td>
            <td>
              <input 
                type="checkbox" 
                :checked="user.is_teacher === true" 
                @change="toggleTeacher(user)"
                :title="$t('adminUsers.toggleTeacherTitle')"
              />
            </td>
            <td>
              <input type="checkbox" :checked="user.is_admin === true" @change="toggleAdmin(user)" />
            </td>
            <td>
              <!-- Куратором можно сделать любого пользователя -->
              <input 
                type="checkbox" 
                :checked="user.teacher_info?.curator === true" 
                @change="toggleCurator(user)"
                :title="$t('adminUsers.toggleCuratorTitle')"
              />
            </td>
            <td>
              <button class="edit-btn" @click="editUser(user.id)" :title="$t('common.edit')">✎</button>
              <button class="delete-btn" @click="confirmDelete(user.id)" :title="$t('common.delete')">🗑</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Модальное подтверждение удаления -->
    <Teleport to="body">
      <div v-if="showDeleteModal" class="modal-overlay" @click.self="closeDeleteModal">
        <div class="modal-content">
          <h3>{{ $t('adminUsers.deleteConfirmTitle') }}</h3>
          <p>{{ $t('adminUsers.deleteConfirmMessage') }}</p>
          <div class="modal-actions">
            <button class="confirm-btn" @click="deleteUser">{{ $t('common.delete') }}</button>
            <button class="cancel-btn" @click="closeDeleteModal">{{ $t('common.cancel') }}</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { getUserDisplayName as displayUserName } from '@/utils/userDisplay';
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import ThemeToggle from '@/components/ThemeToggle.vue';
import type { User } from '@/types';
import HomeButton from '@/components/HomeButton.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';
import api from '@/utils/api'

const { t } = useI18n();
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
    const response = await api.get('/admin/users');
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
    filtered = filtered.filter(u => (displayUserName(u).toLowerCase().includes(q) || u.email.toLowerCase().includes(q)));
  }
  if (roleFilter.value === 'student') {
    filtered = filtered.filter(u => !u.is_teacher);
  } else if (roleFilter.value === 'teacher') {
    filtered = filtered.filter(u => u.is_teacher === true);
  } else if (roleFilter.value === 'admin') {
    filtered = filtered.filter(u => u.is_admin === true);
  } else if (roleFilter.value === 'curator') {
    filtered = filtered.filter(u => u.teacher_info?.curator === true);
  }
  return filtered;
});

async function toggleActive(user: User) {
  const newValue = !user.is_active;
  try {
    await api.put(`/admin/users/${user.id}`, { is_active: newValue });
    user.is_active = newValue;
  } catch (error) {
    console.error('Failed to toggle active status', error);
  }
}

// Переключение типа пользователя (ученик/учитель) - без подтверждения
async function toggleTeacher(user: User) {
  const newIsTeacher = !user.is_teacher;
  
  try {
    const response = await api.put(`/admin/users/${user.id}/toggle-teacher`, { is_teacher: newIsTeacher });
    
    user.is_teacher = response.data.is_teacher;
    user.teacher_info = response.data.teacher_info;
    
    // Если переключаем обратно в ученика, сбрасываем curator (так как ученик не может быть куратором)
    if (!newIsTeacher) {
      if (user.teacher_info) {
        user.teacher_info.curator = false;
      }
    }
  } catch (error) {
    console.error('Failed to toggle teacher status', error);
  }
}

async function toggleAdmin(user: User) {
  const newValue = !user.is_admin;
  try {
    await api.put(`/admin/users/${user.id}/toggle-role`, { is_admin: newValue });
    user.is_admin = newValue;
  } catch (error) {
    console.error('Failed to toggle admin', error);
  }
}

// Куратором можно сделать любого пользователя
async function toggleCurator(user: User) {
  const newValue = !(user.teacher_info?.curator === true);
  
  try {
    await api.put(`/admin/users/${user.id}/toggle-role`, { is_curator: newValue });
    
    if (!user.teacher_info) {
      user.teacher_info = { roles: [], curator: false };
    }
    user.teacher_info.curator = newValue;
  } catch (error) {
    console.error('Failed to toggle curator', error);
  }
}

function editUser(id: number) {
  router.push(`/admin/users/${id}/edit`);
}

function goToCreateUser() {
  router.push('/admin/create-users');
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
    await api.delete(`/admin/users/${userToDelete.value}`);
    users.value = users.value.filter(u => u.id !== userToDelete.value);
    closeDeleteModal();
  } catch (error) {
    console.error('Failed to delete user', error);
    alert(t('adminUsers.deleteError'));
  }
}

function goBack() {
  router.push('/admin');
}
</script>

<style scoped>
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
  align-items: center;
}

.create-user-btn {
  background: var(--accent-color);
  color: white;
  border: none;
  border-radius: 30px;
  padding: 8px 16px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.create-user-btn:hover {
  background: var(--accent-hover);
}

.back-button {
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

.back-button:hover {
  background: var(--hover-bg);
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
  cursor: pointer;
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
  vertical-align: middle;
}

.user-link {
  color: var(--link-color);
  text-decoration: none;
  font-weight: 500;
}

.user-link:hover {
  color: var(--link-hover);
  text-decoration: underline;
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

.loading {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
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

@media (max-width: 768px) {
  .users-table {
    font-size: 0.85rem;
    display: block;
    overflow-x: auto;
  }
  
  .users-table th,
  .users-table td {
    padding: 8px;
    white-space: nowrap;
  }
  
  .edit-btn, .delete-btn {
    padding: 2px 4px;
    font-size: 1rem;
  }
}
</style>