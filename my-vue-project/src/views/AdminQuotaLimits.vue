<template>
  <div class="admin-quota-limits">
    <header class="page-header">
      <h1>{{ $t('adminQuotaLimits.title') }}</h1>
      <div class="header-actions">
        <ThemeToggle />
        <LanguageSwitcher />
        <HomeButton />
      </div>
    </header>

    <main class="limits-layout">
      <section class="limit-section">
        <h2>{{ $t('adminQuotaLimits.globalTitle') }}</h2>
        <div class="limit-grid">
          <label>
            <span>{{ $t('adminQuotaLimits.projectLimit') }}</span>
            <input v-model.number="globalProjectMb" type="number" min="0" />
          </label>
          <label>
            <span>{{ $t('adminQuotaLimits.userLimit') }}</span>
            <input v-model.number="globalUserMb" type="number" min="0" />
          </label>
        </div>
        <button class="primary-btn" @click="saveGlobalLimits">{{ $t('common.save') }}</button>
      </section>

      <section class="limit-section">
        <h2>{{ $t('adminQuotaLimits.projectPersonalTitle') }}</h2>
        <label>
          <span>{{ $t('adminQuotaLimits.project') }}</span>
          <select v-model.number="selectedProjectId" @change="applySelectedProject">
            <option :value="0">{{ $t('common.notSelected') }}</option>
            <option v-for="project in projects" :key="project.id" :value="project.id">
              {{ project.title }}
            </option>
          </select>
        </label>
        <div class="limit-grid">
          <label>
            <span>{{ $t('adminQuotaLimits.projectLimit') }}</span>
            <input v-model.number="projectOverrideMb" type="number" min="0" />
          </label>
          <label>
            <span>{{ $t('adminQuotaLimits.userLimit') }}</span>
            <input v-model.number="projectUserOverrideMb" type="number" min="0" />
          </label>
        </div>
        <button class="primary-btn" :disabled="!selectedProjectId" @click="saveProjectLimits">
          {{ $t('adminQuotaLimits.saveProject') }}
        </button>
      </section>

      <section class="limit-section">
        <h2>{{ $t('adminQuotaLimits.userPersonalTitle') }}</h2>
        <label>
          <span>{{ $t('adminQuotaLimits.user') }}</span>
          <select v-model.number="selectedUserId" @change="applySelectedUser">
            <option :value="0">{{ $t('common.notSelected') }}</option>
            <option v-for="user in users" :key="user.id" :value="user.id">
              {{ displayUserName(user) }} · {{ user.fullname }}
            </option>
          </select>
        </label>
        <label>
          <span>{{ $t('adminQuotaLimits.userLimit') }}</span>
          <input v-model.number="userOverrideMb" type="number" min="0" />
        </label>
        <button class="primary-btn" :disabled="!selectedUserId" @click="saveUserLimits">
          {{ $t('adminQuotaLimits.saveUser') }}
        </button>
      </section>

      <section class="limit-section role-section">
        <h2>{{ $t('adminQuotaLimits.roleTitle') }}</h2>
        <p class="section-hint">{{ $t('adminQuotaLimits.roleHint') }}</p>
        <div v-for="role in roles" :key="role" class="role-limit-row">
          <div class="role-name">{{ $t(`roles.${role}`) }}</div>
          <label>
            <span>{{ $t('adminQuotaLimits.userLimit') }}</span>
            <input v-model.number="roleLimitsMb[role]" type="number" min="0" />
          </label>
          <label class="checkbox-label">
            <input v-model="applyToCustom[role]" type="checkbox" />
            <span>{{ $t('adminQuotaLimits.applyToCustom') }}</span>
          </label>
          <button class="primary-btn" @click="saveRoleLimit(role)">
            {{ $t('common.save') }}
          </button>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { getUserDisplayName as displayUserName, getUserInitial as displayUserInitial } from '@/utils/userDisplay';
import { onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import ThemeToggle from '@/components/ThemeToggle.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';
import HomeButton from '@/components/HomeButton.vue';
import api from '@/utils/api';
import type { Project, User } from '@/types';

const { t } = useI18n();
const bytesInMb = 1024 * 1024;

const projects = ref<Project[]>([]);
const users = ref<User[]>([]);
const userOverrides = ref<Record<string, number>>({});
const globalProjectMb = ref(0);
const globalUserMb = ref(0);
const selectedProjectId = ref(0);
const selectedUserId = ref(0);
const projectOverrideMb = ref(0);
const projectUserOverrideMb = ref(0);
const userOverrideMb = ref(0);
const roles = ['customer', 'supervisor', 'expert', 'executor', 'curator'] as const;
const roleLimitsMb = ref<Record<string, number>>({});
const applyToCustom = ref<Record<string, boolean>>({});

function toMb(bytes?: number | null) {
  return Math.round((bytes || 0) / bytesInMb);
}

function toBytes(mb: number) {
  return Math.max(0, Number(mb || 0)) * bytesInMb;
}

function applySelectedProject() {
  const project = projects.value.find(item => item.id === selectedProjectId.value);
  const overrides = project?.file_quota_overrides || {};
  projectOverrideMb.value = toMb(overrides.project_limit ?? null);
  projectUserOverrideMb.value = toMb(overrides.user_limit ?? null);
}

function applySelectedUser() {
  userOverrideMb.value = toMb(userOverrides.value[String(selectedUserId.value)] ?? null);
}

async function loadData() {
  const [quotasResponse, projectsResponse, usersResponse, userQuotasResponse] = await Promise.all([
    api.get('/admin/file-quotas'),
    api.get('/admin/projects'),
    api.get('/users/'),
    api.get('/admin/user-file-quotas'),
  ]);
  globalProjectMb.value = toMb(quotasResponse.data.project_limit);
  globalUserMb.value = toMb(quotasResponse.data.user_limit);
  projects.value = projectsResponse.data || [];
  users.value = usersResponse.data || [];
  userOverrides.value = userQuotasResponse.data.user_overrides || {};
  roleLimitsMb.value = Object.fromEntries(
    roles.map(role => [role, toMb(userQuotasResponse.data.role_overrides?.[role] ?? quotasResponse.data.user_limit)]),
  );
  applyToCustom.value = Object.fromEntries(roles.map(role => [role, false]));
  applySelectedProject();
  applySelectedUser();
}

async function saveGlobalLimits() {
  await api.put('/admin/file-quotas', {
    project_limit: toBytes(globalProjectMb.value),
    user_limit: toBytes(globalUserMb.value),
  });
  alert(t('adminQuotaLimits.saved'));
  await loadData();
}

async function saveProjectLimits() {
  await api.put(`/admin/projects/${selectedProjectId.value}/file-quota`, {
    project_limit: toBytes(projectOverrideMb.value),
    user_limit: toBytes(projectUserOverrideMb.value),
  });
  alert(t('adminQuotaLimits.saved'));
  await loadData();
}

async function saveUserLimits() {
  await api.put(`/admin/users/${selectedUserId.value}/file-quota`, {
    user_limit: toBytes(userOverrideMb.value),
  });
  alert(t('adminQuotaLimits.saved'));
  await loadData();
}

async function saveRoleLimit(role: string) {
  const response = await api.put(`/admin/file-quotas/roles/${role}`, {
    user_limit: toBytes(roleLimitsMb.value[role]),
    apply_to_custom_limits: applyToCustom.value[role] || false,
  });
  const cleared = response.data.cleared_user_ids?.length || 0;
  alert(t('adminQuotaLimits.roleSaved', { count: cleared }));
  await loadData();
}

onMounted(loadData);
</script>

<style scoped>
.admin-quota-limits {
  min-height: 100vh;
  background: var(--bg-page);
  color: var(--text-primary);
  padding: 20px;
}
.page-header {
  max-width: 1200px;
  margin: 0 auto 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.page-header h1 { margin: 0; color: var(--heading-color); }
.header-actions { display: flex; gap: 10px; align-items: center; }
.limits-layout {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 18px;
}
.limit-section {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  box-shadow: var(--shadow);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.limit-section h2 {
  margin: 0;
  color: var(--heading-color);
  font-size: 1.1rem;
}
.limit-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
}
label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: var(--text-secondary);
  font-weight: 600;
}
input,
select {
  width: 100%;
  box-sizing: border-box;
  background: var(--input-bg);
  color: var(--input-text);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 10px 12px;
}
.primary-btn {
  align-self: flex-start;
  border: none;
  border-radius: 8px;
  background: var(--accent-color);
  color: var(--button-text);
  padding: 10px 16px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: var(--shadow);
}
.primary-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.role-section { grid-column: 1 / -1; }
.section-hint { margin: 0; color: var(--text-secondary); }
.role-limit-row {
  display: grid;
  grid-template-columns: minmax(150px, 1fr) minmax(180px, 1fr) minmax(240px, 1.5fr) auto;
  gap: 14px;
  align-items: end;
  padding: 12px 0;
  border-top: 1px solid var(--border-color);
}
.role-name { align-self: center; font-weight: 700; color: var(--heading-color); }
.checkbox-label { flex-direction: row; align-items: center; align-self: center; font-weight: 500; }
.checkbox-label input { width: auto; }
@media (max-width: 800px) {
  .role-limit-row { grid-template-columns: 1fr; align-items: stretch; }
}
</style>
