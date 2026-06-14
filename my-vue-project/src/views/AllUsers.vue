<template>
  <div class="all-users-page">
    <header class="users-header">
      <h1>{{ $t('allUsers.title') }}</h1>
      <div class="header-actions">
        <ThemeToggle />
        <HomeButton/>
      </div>
    </header>

    <div class="search-container">
      <input
        v-model="search"
        :placeholder="searchPlaceholder"
        @input="onSearchInput"
      />
      <div class="advanced-filters">
        <select v-model="roleFilter">
          <option value="">{{ $t('allUsers.filterAll') }}</option>
          <option value="student">{{ $t('register.student') }}</option>
          <option value="admin">{{ $t('register.admin') }}</option>
          <option value="curator">{{ $t('roles.curator') }}</option>
          <option value="customer">{{ $t('roles.customer') }}</option>
          <option value="supervisor">{{ $t('roles.supervisor') }}</option>
          <option value="expert">{{ $t('roles.expert') }}</option>
          <option value="executor">{{ $t('roles.executor') }}</option>
        </select>
        <input v-model.number="parallelFilter" type="number" min="1" max="11" :placeholder="$t('adminDirections.parallel')" />
        <input v-model.number="classFilter" type="number" min="0" max="9" :placeholder="$t('adminDirections.class')" />
        <select v-model="directionFilter">
          <option value="">{{ $t('adminDirections.all') }}</option>
          <option v-for="direction in directions" :key="direction.key" :value="direction.key">{{ direction.label }}</option>
        </select>
        <select v-model="sortBy">
          <option value="fullname">{{ $t('adminDirections.sort') }}: {{ $t('adminUsers.table.fullname') }}</option>
          <option value="role">{{ $t('adminUsers.table.type') }}</option>
          <option value="parallel">{{ $t('adminDirections.parallel') }}</option>
          <option value="class">{{ $t('adminDirections.class') }}</option>
          <option value="direction">{{ $t('adminDirections.direction') }}</option>
        </select>
        <select v-model="sortOrder">
          <option value="asc">A-Z</option>
          <option value="desc">Z-A</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="loading">{{ $t('common.loading') }}</div>
    <div v-else-if="users.length === 0" class="no-users">{{ $t('allUsers.noUsers') }}</div>
    <div v-else class="users-grid">
      <div
        v-for="user in users"
        :key="user.id"
        class="user-card"
        @click="goToUser(user.id)"
      >
        <div class="user-avatar">
          <img
            v-if="user.avatar && !imageError[user.id]"
            :src="avatarUrl(user.avatar)"
            :alt="displayUserName(user)"
            @error="imageError[user.id] = true"
          />
          <span v-else>{{ displayUserInitial(user) }}</span>
        </div>
        <h3 class="user-display-name">{{ displayUserName(user) }}</h3>
        <p class="user-fullname">{{ user.fullname }}</p>
        <p class="user-email">{{ user.email }}</p>
        <p v-if="user.direction_key" class="user-speciality">{{ directionLabel(user.direction_key) }}</p>

        <template v-if="!user.is_teacher">
          <div class="user-class">{{ $t('allUsers.classLabel') }}: {{ user.class }}</div>
          <div v-if="user.speciality" class="user-speciality">{{ user.speciality }}</div>
        </template>

        <template v-else>
          <div v-if="user.teacher_info" class="user-roles">
            {{ getRolesText(user) }}
          </div>
          <div v-if="user.speciality" class="user-speciality">{{ $t('allUsers.subjectLabel') }}: {{ user.speciality }}</div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { getUserDisplayName as displayUserName, getUserInitial as displayUserInitial } from '@/utils/userDisplay';
import { ref, onMounted, watch, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useUsersStore } from '@/stores/users';
import { useI18n } from 'vue-i18n';
import ThemeToggle from '@/components/ThemeToggle.vue';
import type { User } from '@/types';
import HomeButton from '@/components/HomeButton.vue';

const { t } = useI18n();
const router = useRouter();
const usersStore = useUsersStore();
const users = ref<User[]>([]);
const search = ref('');
const loading = ref(true);
const imageError = ref<Record<number, boolean>>({});
const roleFilter = ref('');
const classFilter = ref<number | null>(null);
const parallelFilter = ref<number | null>(null);
const directionFilter = ref('');
const sortBy = ref('fullname');
const sortOrder = ref('asc');
const directions = ref<Array<{ key: string; label: string }>>([]);

let searchTimer: ReturnType<typeof setTimeout> | null = null;

const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const avatarUrl = (avatar: string) => `${baseUrl}/avatars/${avatar}`;

const searchPlaceholder = computed(() => t('allUsers.searchAll'));

async function loadUsers() {
  loading.value = true;
  try {
    const role = roleFilter.value || undefined;
    await usersStore.fetchUsers(role, search.value || undefined, {
      class_grade: classFilter.value ?? undefined,
      parallel: parallelFilter.value || undefined,
      direction_key: directionFilter.value || undefined,
      sort_by: sortBy.value,
      sort_order: sortOrder.value,
    });
    users.value = usersStore.users;
    imageError.value = {};
  } catch (error) {
    console.error('Ошибка загрузки пользователей:', error);
  } finally {
    loading.value = false;
  }
}

watch([search, roleFilter, classFilter, parallelFilter, directionFilter, sortBy, sortOrder], () => {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    loadUsers();
  }, 300);
});

onMounted(async () => {
  const response = await fetch(`${baseUrl}/user-directions`);
  directions.value = (await response.json()).directions || [];
  loadUsers();
});

function onSearchInput() {
  imageError.value = {};
}

function goToUser(id: number) {
  router.push(`/user/${id}`);
}

function goHome() {
  router.push('/main');
}

function getRolesText(user: User): string {
  if (!user.is_teacher || !user.teacher_info) return '';
  const roles = user.teacher_info.roles.map(role => t(`roles.${role}`));
  if (user.teacher_info.curator) roles.push(t('roles.curator'));
  return roles.join(', ');
}

function directionLabel(key: string): string {
  return directions.value.find(item => item.key === key)?.label || key;
}
</script>

<style scoped>
.all-users-page {
  min-height: 100vh;
  background: var(--bg-page);
  padding: 20px;
  box-sizing: border-box;
  transition: background 0.3s;
}

.users-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto 20px;
}

.users-header h1 {
  color: var(--heading-color);
  font-size: 2.5rem;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}



.filter-tabs {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-bottom: 30px;
}

.tab-button {
  padding: 10px 30px;
  border: 2px solid var(--border-color);
  border-radius: 50px;
  background: var(--bg-card);
  color: var(--text-secondary);
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tab-button.active {
  border-color: var(--accent-color);
  background: rgba(66, 185, 131, 0.1);
  color: var(--accent-color);
  box-shadow: 0 4px 12px rgba(66, 185, 131, 0.2);
}

.tab-button:hover {
  background: rgba(66, 185, 131, 0.15);
  color: var(--accent-color);
  border-color: rgba(66, 185, 131, 0.3);
}

.tab-button.active:hover {
  background: rgba(66, 185, 131, 0.2);
  box-shadow: 0 4px 12px rgba(66, 185, 131, 0.3);
}

.search-container {
  max-width: 600px;
  margin: 0 auto 30px;
}

.search-container input {
  width: 100%;
  padding: 12px 20px;
  border: 1px solid var(--input-border);
  border-radius: 50px;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
  background: var(--input-bg);
  color: var(--text-primary);
}
.advanced-filters { display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 8px; margin-top: 10px; }
.advanced-filters input, .advanced-filters select { padding: 10px; border: 1px solid var(--input-border); border-radius: 8px; background: var(--input-bg); color: var(--text-primary); }

.search-container input::placeholder {
  color: var(--text-secondary);
}

.search-container input:focus {
  border-color: var(--accent-color);
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.2);
}

.dark-theme .search-container input:focus {
  box-shadow: 0 0 0 3px rgba(1, 69, 172, 0.2);
}

.users-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.user-card {
  background: var(--bg-card);
  border-radius: 16px;
  padding: 20px;
  box-shadow: var(--shadow);
  transition: all 0.2s;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  border: 1px solid var(--border-color);
  animation: fadeIn 0.3s ease;
}

.user-card:hover {
  outline: 1px solid var(--accent-color);
  outline-offset: 1px;
  border-color: var(--accent-color);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-avatar {
  position: relative;
  width: 60px;
  height: 60px;
  background: var(--accent-color);
  color: var(--button-text);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 12px;
  overflow: hidden;
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.user-avatar span {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.user-display-name {
  color: var(--heading-color);
  margin-bottom: 4px;
  font-size: 1.2rem;
  font-weight: 600;
}

.user-fullname {
  color: var(--text-primary);
  font-size: 0.95rem;
  margin-bottom: 6px;
}

.user-email {
  color: var(--text-secondary);
  font-size: 0.85rem;
  margin-bottom: 8px;
}

.user-class, .user-speciality {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-top: 4px;
}

.user-roles {
  margin-top: 6px;
  font-size: 0.9rem;
  color: var(--text-secondary);
  max-width: 100%;
  word-break: break-word;
}

.loading, .no-users {
  text-align: center;
  color: var(--text-primary);
  font-size: 1.2rem;
  padding: 40px;
}
</style>
