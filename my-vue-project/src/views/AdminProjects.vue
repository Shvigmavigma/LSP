<template>
  <div class="admin-projects-page">
    <header class="page-header">
      <h1>{{ $t('adminProjects.title') }}</h1>
      <div class="header-actions">
        <ThemeToggle />
        <LanguageSwitcher />
        <button class="home-button" @click="goHome" :title="$t('common.home')">🏠</button>
        <button class="back-button" @click="goBack" :title="$t('common.back')">◀</button>
      </div>
    </header>

    <div v-if="loading" class="loading">{{ $t('common.loading') }}</div>
    <div v-else>
      <div class="filters">
        <input v-model="search" :placeholder="$t('adminProjects.searchPlaceholder')" />
        <select v-model="statusFilter">
          <option value="all">{{ $t('adminProjects.filterAll') }}</option>
          <option value="active">{{ $t('adminProjects.filterActive') }}</option>
          <option value="hidden">{{ $t('adminProjects.filterHidden') }}</option>
          <option value="old">{{ $t('adminProjects.filterOld') }}</option>
        </select>
      </div>

      <table class="projects-table">
        <thead>
          <tr>
            <th>{{ $t('adminProjects.table.id') }}</th>
            <th>{{ $t('adminProjects.table.title') }}</th>
            <th>{{ $t('adminProjects.table.description') }}</th>
            <th>{{ $t('adminProjects.table.participants') }}</th>
            <th>{{ $t('adminProjects.table.tasks') }}</th>
            <th>{{ $t('adminProjects.table.status') }}</th>
            <th>{{ $t('adminProjects.table.old') }}</th>
            <th>{{ $t('adminProjects.table.hiddenBy') }}</th>
            <th>{{ $t('adminProjects.table.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="project in filteredProjects" :key="project.id">
            <td>{{ project.id }}</td>
            <td>
              <router-link :to="`/project/${project.id}`" class="project-link">
                {{ project.title }}
              </router-link>
            </td>
            <td>{{ project.body.slice(0, 50) }}...</td>
            <td>{{ project.participants?.length || 0 }}</td>
            <td>{{ project.tasks?.length || 0 }}</td>
            <td class="status-cell">
              <span :class="project.is_hidden ? 'hidden-status' : 'active-status'">
                {{ project.is_hidden ? $t('adminProjects.status.hidden') : $t('adminProjects.status.active') }}
              </span>
              <button
                class="toggle-visibility-btn"
                @click="toggleHide(project)"
                :title="project.is_hidden ? $t('adminProjects.toggleShowTitle') : $t('adminProjects.toggleHideTitle')"
              >
                {{ project.is_hidden ? '👁️‍🗨️' : '🙈' }}
              </button>
            </td>
            <td class="old-cell">
              <span :class="project.is_old ? 'old-status' : 'not-old-status'">
                {{ project.is_old ? $t('adminProjects.old') : $t('adminProjects.notOld') }}
              </span>
              <button
                v-if="!project.is_old"
                class="mark-old-btn"
                @click="markAsOld(project.id)"
                :title="$t('adminProjects.markAsOldTitle')"
              >
                📦
              </button>
              <button
                v-else
                class="unmark-old-btn"
                @click="unmarkAsOld(project.id)"
                :title="$t('adminProjects.unmarkAsOldTitle')"
              >
                🔄
              </button>
            </td>
            <td>
              <span v-if="project.hidden_by">{{ getUserNickname(project.hidden_by) }}</span>
              <span v-else>—</span>
            </td>
            <td class="actions-cell">
              <button class="edit-btn" @click="editProject(project.id)" :title="$t('common.edit')">✎</button>
              <button class="delete-btn" @click="confirmDelete(project.id)" :title="$t('common.delete')">🗑</button>
            </td>
          </tr>
        </tbody>
       </table>
    </div>

    <!-- Модальное подтверждение удаления -->
    <Teleport to="body">
      <div v-if="showDeleteModal" class="modal-overlay" @click.self="closeDeleteModal">
        <div class="modal-content">
          <h3>{{ $t('adminProjects.deleteConfirmTitle') }}</h3>
          <p>{{ $t('adminProjects.deleteConfirmMessage') }}</p>
          <div class="modal-actions">
            <button class="confirm-btn" @click="deleteProject">{{ $t('common.delete') }}</button>
            <button class="cancel-btn" @click="closeDeleteModal">{{ $t('common.cancel') }}</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useUsersStore } from '@/stores/users';
import ThemeToggle from '@/components/ThemeToggle.vue';
import axios from 'axios';
import type { Project } from '@/types';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';

const { t } = useI18n();
const router = useRouter();
const usersStore = useUsersStore();
const projects = ref<Project[]>([]);
const loading = ref(true);
const search = ref('');
const statusFilter = ref<'all' | 'active' | 'hidden' | 'old'>('all');
const showDeleteModal = ref(false);
const projectToDelete = ref<number | null>(null);

onMounted(async () => {
  await usersStore.fetchAllUsers();
  await loadProjects();
});

async function loadProjects() {
  try {
    const response = await axios.get('/admin/projects');
    projects.value = response.data;
  } catch (error) {
    console.error('Failed to load projects', error);
  } finally {
    loading.value = false;
  }
}

function getUserNickname(id: number): string {
  const user = usersStore.users.find(u => u.id === id);
  return user ? user.nickname : `ID: ${id}`;
}

const filteredProjects = computed(() => {
  let filtered = projects.value;
  if (search.value) {
    const q = search.value.toLowerCase();
    filtered = filtered.filter(p => p.title.toLowerCase().includes(q));
  }
  if (statusFilter.value === 'active') {
    filtered = filtered.filter(p => !p.is_hidden);
  } else if (statusFilter.value === 'hidden') {
    filtered = filtered.filter(p => p.is_hidden);
  } else if (statusFilter.value === 'old') {
    filtered = filtered.filter(p => p.is_old === true);
  }
  return filtered;
});

async function toggleHide(project: Project) {
  try {
    await axios.patch(`/projects/${project.id}/hide`);
    project.is_hidden = !project.is_hidden;
    if (project.is_hidden) {
      const response = await axios.get(`/admin/projects/${project.id}`);
      Object.assign(project, response.data);
    } else {
      project.hidden_by = undefined;
    }
  } catch (error) {
    console.error('Failed to toggle hide', error);
    alert(t('adminProjects.toggleError'));
  }
}

async function markAsOld(projectId: number) {
  try {
    await axios.put(`/projects/${projectId}/mark-old`);
    const project = projects.value.find(p => p.id === projectId);
    if (project) project.is_old = true;
  } catch (error) {
    console.error('Failed to mark as old', error);
    alert(t('adminProjects.markOldError'));
  }
}

async function unmarkAsOld(projectId: number) {
  try {
    await axios.put(`/projects/${projectId}/unmark-old`);
    const project = projects.value.find(p => p.id === projectId);
    if (project) project.is_old = false;
  } catch (error) {
    console.error('Failed to unmark as old', error);
    alert(t('adminProjects.unmarkOldError'));
  }
}

function editProject(id: number) {
  router.push(`/admin/projects/${id}/edit`);
}

function confirmDelete(id: number) {
  projectToDelete.value = id;
  showDeleteModal.value = true;
}

function closeDeleteModal() {
  showDeleteModal.value = false;
  projectToDelete.value = null;
}

async function deleteProject() {
  if (!projectToDelete.value) return;
  try {
    await axios.delete(`/admin/projects/${projectToDelete.value}`);
    projects.value = projects.value.filter(p => p.id !== projectToDelete.value);
    closeDeleteModal();
  } catch (error) {
    console.error('Failed to delete project', error);
    alert(t('adminProjects.deleteError'));
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
/* Существующие стили */
.admin-projects-page {
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
  flex: 2;
  padding: 10px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-primary);
}
.filters select {
  flex: 1;
  padding: 10px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-primary);
}
.projects-table {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  border-collapse: collapse;
  background: var(--bg-card);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: var(--shadow);
}
.projects-table th {
  background: var(--bg-page);
  color: var(--heading-color);
  font-weight: 600;
  padding: 12px;
  text-align: left;
  border-bottom: 2px solid var(--border-color);
}
.projects-table td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-primary);
  vertical-align: middle;
}
.project-link {
  color: var(--link-color);
  text-decoration: none;
  font-weight: 500;
}
.project-link:hover {
  color: var(--link-hover);
  text-decoration: underline;
}
.status-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}
.old-cell {
  white-space: nowrap;
}
.hidden-status {
  color: #f44336;
  font-weight: 600;
}
.active-status {
  color: #4caf50;
  font-weight: 600;
}
.old-status {
  color: #ff9800;
  font-weight: 600;
}
.not-old-status {
  color: var(--text-secondary);
}
.toggle-visibility-btn,
.mark-old-btn,
.unmark-old-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.2rem;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.2s;
  color: var(--text-secondary);
}
.toggle-visibility-btn:hover {
  background: rgba(33, 150, 243, 0.2);
}
.mark-old-btn:hover {
  background: rgba(255, 152, 0, 0.2);
}
.unmark-old-btn:hover {
  background: rgba(33, 150, 243, 0.2);
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
.loading, .error {
  text-align: center;
  color: var(--text-primary);
  font-size: 1.2rem;
  padding: 40px;
}
</style>