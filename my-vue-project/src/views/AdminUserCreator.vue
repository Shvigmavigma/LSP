<template>
  <div class="admin-user-creator-page">
    <div class="theme-toggle-container">
      <ThemeToggle />
      <LanguageSwitcher />
      <HomeButton />
    </div>

    <div class="admin-user-creator">
      <div class="creator-header">
        <button class="back-btn" @click="goBack">
          ← {{ $t('common.back') }}
        </button>
        <h2>{{ $t('admin.createUsers.title') }}</h2>
        <div class="placeholder"></div>
      </div>

      <!-- Форма для одного пользователя -->
      <div class="single-user-form">
        <div class="account-type-selector">
          <button 
            type="button"
            class="type-btn"
            :class="{ active: userType === 'student' }"
            @click="userType = 'student'"
          >
            <span class="type-label">{{ $t('register.student') }}</span>
          </button>
          <button 
            type="button"
            class="type-btn"
            :class="{ active: userType === 'teacher' }"
            @click="userType = 'teacher'"
          >
            <span class="type-label">{{ $t('register.teacher') }}</span>
          </button>
          <button 
            type="button"
            class="type-btn"
            :class="{ active: userType === 'admin' }"
            @click="userType = 'admin'"
          >
            <span class="type-label">{{ $t('register.admin') }}</span>
          </button>
        </div>

        <form @submit.prevent="createUser">
          <!-- ФИО -->
          <div class="form-group">
            <label>{{ $t('register.fullName') }} <span class="required">*</span></label>
            <div class="name-fields">
              <input
                v-model="form.lastName"
                type="text"
                :placeholder="$t('register.lastName')"
                required
              />
              <input
                v-model="form.firstName"
                type="text"
                :placeholder="$t('register.firstName')"
                required
              />
              <input
                v-model="form.patronymic"
                type="text"
                :placeholder="$t('register.patronymic')"
              />
            </div>
          </div>

          <!-- Email -->
          <div class="form-group">
            <label>{{ $t('register.email') }} <span class="required">*</span></label>
            <input
              v-model="form.email"
              type="email"
              :placeholder="$t('register.emailPlaceholder')"
              required
            />
          </div>

          <!-- Пароль -->
          <div class="form-group">
            <label>{{ $t('register.password') }} <span class="required">*</span></label>
            <input
              v-model="form.password"
              type="password"
              :placeholder="$t('register.passwordPlaceholder')"
              required
            />
          </div>

          <!-- Класс (только для учеников) -->
          <div v-if="userType === 'student'" class="form-group">
            <label>{{ $t('register.class') }}</label>
            <ClassInput
              v-model="form.class_"
              :placeholder="$t('register.classPlaceholder')"
            />
          </div>

          <!-- Специальность -->
          <div class="form-group">
            <label>{{ $t('register.speciality') }}</label>
            <input
              v-model="form.speciality"
              type="text"
              :placeholder="userType === 'teacher' ? $t('register.teacherSpecialityPlaceholder') : $t('register.studentSpecialityPlaceholder')"
            />
          </div>

          <!-- Роли учителя -->
          <div v-if="userType === 'teacher'" class="form-group">
            <label>{{ $t('register.rolesLabel') }}</label>
            <div class="roles-selector">
              <label class="role-checkbox-label">
                <input type="checkbox" v-model="teacherRoles.customer" value="customer" />
                <span class="role-checkbox-custom"></span>
                <span class="role-label">{{ $t('roles.customer') }}</span>
              </label>
              <label class="role-checkbox-label">
                <input type="checkbox" v-model="teacherRoles.expert" value="expert" />
                <span class="role-checkbox-custom"></span>
                <span class="role-label">{{ $t('roles.expert') }}</span>
              </label>
              <label class="role-checkbox-label">
                <input type="checkbox" v-model="teacherRoles.supervisor" value="supervisor" />
                <span class="role-checkbox-custom"></span>
                <span class="role-label">{{ $t('roles.supervisor') }}</span>
              </label>
            </div>
          </div>

          <!-- Куратор (только для учителей) -->
          <div v-if="userType === 'teacher'" class="form-group checkbox-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="form.isCurator" />
              <span class="checkbox-text">{{ $t('admin.createUsers.isCurator') }}</span>
            </label>
          </div>

          <!-- Флаг администратора (для админов) -->
          <div v-if="userType === 'admin'" class="form-group checkbox-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="form.isAdmin" checked disabled />
              <span class="checkbox-text">{{ $t('admin.createUsers.isAdmin') }}</span>
            </label>
            <small class="help-text">{{ $t('admin.createUsers.adminHelpText') }}</small>
          </div>

          <!-- Мастер-пароль для создания админа -->
          <div v-if="userType === 'admin'" class="form-group">
            <label>{{ $t('admin.createUsers.masterPassword') }} <span class="required">*</span></label>
            <input
              v-model="form.masterPassword"
              type="password"
              :placeholder="$t('admin.createUsers.masterPasswordPlaceholder')"
              required
            />
            <small class="help-text">{{ $t('admin.createUsers.masterPasswordHelp') }}</small>
          </div>

          <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
          <div v-if="successMessage" class="success-message">{{ successMessage }}</div>

          <button type="submit" class="submit-btn" :disabled="loading">
            {{ loading ? $t('common.creating') : $t('admin.createUsers.createUser') }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import ClassInput from '@/components/ClassInput.vue';
import ThemeToggle from '@/components/ThemeToggle.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';
import HomeButton from '@/components/HomeButton.vue';
import api from '@/utils/api';

const { t } = useI18n();
const router = useRouter();

// Props
const props = defineProps<{
  onUserCreated?: () => void;
}>();

// State
const userType = ref<'student' | 'teacher' | 'admin'>('student');
const loading = ref(false);
const errorMessage = ref('');
const successMessage = ref('');

// Форма для одного пользователя
const form = ref({
  lastName: '',
  firstName: '',
  patronymic: '',
  email: '',
  password: '',
  class_: 0,
  speciality: '',
  isCurator: false,
  isAdmin: true,
  masterPassword: ''
});

const teacherRoles = ref({
  customer: false,
  expert: false,
  supervisor: false
});

// Методы
const goBack = () => {
  router.push('/admin');
};

const getFullName = () => {
  const parts = [form.value.lastName.trim(), form.value.firstName.trim()];
  if (form.value.patronymic.trim()) {
    parts.push(form.value.patronymic.trim());
  }
  return parts.join(' ');
};

const getSelectedRoles = () => {
  const roles = [];
  if (teacherRoles.value.customer) roles.push('customer');
  if (teacherRoles.value.expert) roles.push('expert');
  if (teacherRoles.value.supervisor) roles.push('supervisor');
  return roles;
};

const createUser = async () => {
  errorMessage.value = '';
  successMessage.value = '';
  loading.value = true;

  try {
    const fullname = getFullName();
    
    if (!fullname) {
      errorMessage.value = t('register.fillNameFields');
      return;
    }

    if (!form.value.email) {
      errorMessage.value = t('register.emailRequired');
      return;
    }

    if (!form.value.password) {
      errorMessage.value = t('register.passwordRequired');
      return;
    }

    // Для админа проверяем мастер-пароль
    if (userType.value === 'admin') {
      if (!form.value.masterPassword) {
        errorMessage.value = t('admin.createUsers.masterPasswordRequired');
        return;
      }
    }

    const userData: any = {
      fullname,
      email: form.value.email.trim().toLowerCase(),
      password: form.value.password,
      speciality: form.value.speciality
    };

    let endpoint = '';
    
    if (userType.value === 'student') {
      userData.class_ = form.value.class_ || 0;
      endpoint = '/admin/users/create-student';
    } else if (userType.value === 'teacher') {
      endpoint = '/admin/users/create-teacher';
      userData.teacher_info = {
        roles: getSelectedRoles(),
        curator: form.value.isCurator
      };
    } else if (userType.value === 'admin') {
      endpoint = '/admin/users/create-admin';
      userData.master_password = form.value.masterPassword;
      userData.teacher_info = {
        roles: ['customer', 'expert', 'supervisor'],
        curator: true
      };
    }

    const response = await api.post(endpoint, userData);
    
    if (response.data) {
      successMessage.value = t('admin.createUsers.userCreated', { name: response.data.fullname });
      
      // Очищаем форму
      form.value = {
        lastName: '',
        firstName: '',
        patronymic: '',
        email: '',
        password: '',
        class_: 0,
        speciality: '',
        isCurator: false,
        isAdmin: true,
        masterPassword: ''
      };
      teacherRoles.value = { customer: false, expert: false, supervisor: false };
      
      if (props.onUserCreated) props.onUserCreated();
      
      // Автоматически скрываем сообщение через 3 секунды
      setTimeout(() => {
        successMessage.value = '';
      }, 3000);
    }
  } catch (error: any) {
    console.error('Create user error:', error);
    errorMessage.value = error.response?.data?.detail || t('admin.createUsers.createError');
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.admin-user-creator-page {
  min-height: 100vh;
  background: var(--bg-page);
  padding: 20px;
  position: relative;
}

.theme-toggle-container {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 10;
  display: flex;
  gap: 10px;
}

.admin-user-creator {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
  background: var(--bg-card);
  border-radius: 16px;
  box-shadow: var(--shadow-strong);
  margin-top: 60px;
}

.creator-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.creator-header h2 {
  margin: 0;
  color: var(--heading-color);
  text-align: center;
}

.back-btn {
  padding: 8px 16px;
  background: var(--input-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
}

.back-btn:hover {
  background: var(--hover-bg);
  border-color: var(--accent-color);
}

.placeholder {
  width: 80px;
  visibility: hidden;
}

.account-type-selector {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  justify-content: center;
}

.type-btn {
  padding: 12px 24px;
  border: 2px solid var(--border-color);
  border-radius: 12px;
  background: var(--input-bg);
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.type-btn.active {
  border-color: var(--accent-color);
  background: rgba(66, 185, 131, 0.1);
  color: var(--accent-color);
}

.type-label {
  font-size: 1rem;
  font-weight: 500;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: var(--text-secondary);
  font-weight: 500;
}

.required {
  color: var(--danger-color);
}

.name-fields {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 12px;
}

input[type="text"],
input[type="email"],
input[type="password"] {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-primary);
  font-size: 1rem;
}

input:focus {
  outline: none;
  border-color: var(--accent-color);
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.1);
}

/* Роли учителя */
.roles-selector {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.role-checkbox-label {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 8px 16px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  transition: background 0.2s;
  vertical-align: middle;
}

.role-checkbox-label:hover {
  background: var(--hover-bg);
}

.role-checkbox-label input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
  margin: 0;
}

.role-checkbox-custom {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-color);
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 0.2s, border-color 0.2s;
}

.role-checkbox-label input:checked + .role-checkbox-custom {
  background: var(--accent-color);
  border-color: var(--accent-color);
}

.role-checkbox-label input:checked + .role-checkbox-custom::after {
  content: '✓';
  color: white;
  font-size: 12px;
}

.role-label {
  font-size: 0.95rem;
  color: var(--text-primary);
  line-height: 1.4;
  margin-left: 10px;
}

/* Чекбокс группа */
.checkbox-group {
  margin-top: 8px;
}

.checkbox-label {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  vertical-align: middle;
}

.checkbox-label input {
  width: 18px;
  height: 18px;
  margin: 0;
  cursor: pointer;
  flex-shrink: 0;
}

.checkbox-text {
  font-size: 0.95rem;
  color: var(--text-primary);
  line-height: 1.4;
  margin-left: 10px;
}

.help-text {
  display: block;
  margin-top: 6px;
  margin-left: 28px;
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.submit-btn {
  width: 100%;
  padding: 14px;
  background: var(--accent-color);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
  margin-top: 20px;
}

.submit-btn:hover:not(:disabled) {
  background: var(--accent-hover);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-message {
  background: var(--error-bg);
  color: var(--danger-color);
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 16px;
  border: 1px solid var(--danger-color);
}

.success-message {
  background: rgba(66, 185, 131, 0.1);
  color: var(--accent-color);
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 16px;
  border: 1px solid var(--accent-color);
}

@media (max-width: 768px) {
  .name-fields {
    grid-template-columns: 1fr;
    gap: 8px;
  }
  
  .creator-header {
    flex-direction: column;
  }
  
  .placeholder {
    display: none;
  }
  
  .account-type-selector {
    flex-direction: column;
  }
  
  .type-btn {
    justify-content: center;
  }
  
  .roles-selector {
    flex-direction: column;
  }
  
  .role-checkbox-label {
    width: 100%;
  }
  
  .theme-toggle-container {
    position: relative;
    justify-content: flex-end;
    margin-bottom: 16px;
  }
  
  .admin-user-creator {
    margin-top: 0;
  }
}
</style>