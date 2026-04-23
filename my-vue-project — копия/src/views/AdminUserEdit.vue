<template>
  <div class="admin-user-edit-page">
    <header class="page-header">
      <h1>{{ $t('adminUserEdit.title') }}</h1>
      <div class="header-actions">
        <ThemeToggle />
        <LanguageSwitcher />
        <HomeButton/>
        <button class="back-button" @click="goBack" :title="$t('common.back')">◀</button>
      </div>
    </header>

    <div v-if="loading" class="loading">{{ $t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="edit-card">
      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label>{{ $t('adminUserEdit.nickname') }}</label>
          <input v-model="form.nickname" type="text" required />
        </div>

        <div class="form-group">
          <label>{{ $t('adminUserEdit.fullname') }}</label>
          <input v-model="form.fullname" type="text" required />
        </div>

        <div class="form-group">
          <label>{{ $t('adminUserEdit.email') }}</label>
          <input v-model="form.email" type="email" required />
        </div>

        <div v-if="!form.is_teacher" class="form-group">
          <label>{{ $t('adminUserEdit.class') }}</label>
          <ClassInput v-model="form.class" />
        </div>

        <div class="form-group">
          <label>{{ $t('adminUserEdit.speciality') }}</label>
          <input v-model="form.speciality" type="text" />
        </div>

        <div class="form-group">
          <label>
            <input type="checkbox" v-model="form.is_active" />
            {{ $t('adminUserEdit.active') }}
          </label>
        </div>

        <div class="form-group">
          <label>
            <input type="checkbox" v-model="form.is_admin" />
            {{ $t('adminUserEdit.admin') }}
          </label>
        </div>

        <div v-if="form.is_teacher" class="form-group">
          <label>{{ $t('adminUserEdit.teacherRoles') }}</label>
          <div class="roles-selector">
            <label>
              <input type="checkbox" v-model="form.teacher_roles" value="customer" />
              {{ $t('roles.customer') }}
            </label>
            <label>
              <input type="checkbox" v-model="form.teacher_roles" value="expert" />
              {{ $t('roles.expert') }}
            </label>
            <label>
              <input type="checkbox" v-model="form.teacher_roles" value="supervisor" />
              {{ $t('roles.supervisor') }}
            </label>
          </div>
          <label>
            <input type="checkbox" v-model="form.curator" />
            {{ $t('roles.curator') }}
          </label>
        </div>

        <div class="form-actions">
          <button type="submit" class="save-btn" :disabled="saving">
            {{ saving ? $t('common.saving') : $t('common.save') }}
          </button>
          <button type="button" class="cancel-btn" @click="goBack">{{ $t('common.cancel') }}</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import ThemeToggle from '@/components/ThemeToggle.vue';
import ClassInput from '@/components/ClassInput.vue';
import axios from 'axios';
import type { User } from '@/types';
import HomeButton from '@/components/HomeButton.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const userId = Number(route.params.id);
const loading = ref(true);
const error = ref('');
const saving = ref(false);

interface FormData {
  nickname: string;
  fullname: string;
  email: string;
  class: number;
  speciality: string;
  is_active: boolean;
  is_admin: boolean;
  is_teacher: boolean;
  teacher_roles: string[];
  curator: boolean;
}

const form = reactive<FormData>({
  nickname: '',
  fullname: '',
  email: '',
  class: 0,
  speciality: '',
  is_active: true,
  is_admin: false,
  is_teacher: false,
  teacher_roles: [],
  curator: false,
});

onMounted(async () => {
  try {
    const response = await axios.get(`/admin/users/${userId}`);
    const user: User = response.data;
    form.nickname = user.nickname;
    form.fullname = user.fullname;
    form.email = user.email;
    form.class = user.class ?? 0;
    form.speciality = user.speciality || '';
    form.is_active = user.is_active ?? true;
    form.is_admin = user.is_admin ?? false;
    form.is_teacher = user.is_teacher ?? false;
    form.teacher_roles = user.teacher_info?.roles || [];
    form.curator = user.teacher_info?.curator || false;
  } catch (err) {
    error.value = t('adminUserEdit.loadError');
    console.error(err);
  } finally {
    loading.value = false;
  }
});

async function handleSubmit() {
  saving.value = true;
  try {
    const updateData: any = {
      nickname: form.nickname,
      fullname: form.fullname,
      email: form.email,
      class_: form.class,
      speciality: form.speciality,
      is_active: form.is_active,
      is_admin: form.is_admin,
    };
    if (form.is_teacher) {
      updateData.teacher_info = {
        roles: form.teacher_roles,
        curator: form.curator,
      };
    }
    await axios.put(`/admin/users/${userId}`, updateData);
    alert(t('adminUserEdit.saveSuccess'));
    router.push('/admin/users');
  } catch (err) {
    console.error(err);
    alert(t('adminUserEdit.saveError'));
  } finally {
    saving.value = false;
  }
}

function goHome() {
  router.push('/main');
}
function goBack() {
  router.push('/admin/users');
}
</script>

<style scoped>
.admin-user-edit-page {
  min-height: 100vh;
  background: var(--bg-page);
  padding: 20px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 800px;
  margin: 0 auto 20px;
}
.header-actions {
  display: flex;
  gap: 10px;
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
.edit-card {
  max-width: 800px;
  margin: 0 auto;
  background: var(--bg-card);
  border-radius: 24px;
  padding: 30px;
  box-shadow: var(--shadow-strong);
}
.form-group {
  margin-bottom: 20px;
}
label {
  display: block;
  margin-bottom: 6px;
  color: var(--text-secondary);
}
input[type="text"], input[type="email"] {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-primary);
}
input[type="checkbox"] {
  margin-right: 8px;
}
.roles-selector {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 10px;
}
.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 30px;
}
.save-btn {
  background: var(--accent-color);
  color: white;
  border: none;
  border-radius: 30px;
  padding: 12px 24px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
}
.cancel-btn {
  background: var(--bg-page);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  border-radius: 30px;
  padding: 12px 24px;
  cursor: pointer;
}
.loading, .error {
  text-align: center;
  padding: 40px;
  font-size: 1.2rem;
}
</style>