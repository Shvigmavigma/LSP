<template>
  <div class="admin-creator-page">
    <div class="theme-toggle-container">
      <ThemeToggle />
      <LanguageSwitcher />
      <HomeButton />
    </div>

    <div class="admin-creator">
      <div class="creator-header">
        <button class="back-btn" @click="goBack">
          ← {{ $t('common.back') }}
        </button>
      </div>

      <div class="admin-form">
        <form @submit.prevent="createAdmin">
          <!-- ФИО -->
          <div class="form-group">
            <label>{{ $t('register.fullname') }} <span class="required">*</span></label>
            <div class="name-fields">
              <input
                v-model="form.lastName"
                type="text"
                :placeholder="$t('register.lastNamePlaceholder')"
                required
              />
              <input
                v-model="form.firstName"
                type="text"
                :placeholder="$t('register.firstNamePlaceholder')"
                required
              />
              <input
                v-model="form.patronymic"
                type="text"
                :placeholder="$t('register.patronymicPlaceholder')"
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

          <!-- Специальность -->
          <div class="form-group">
            <label>{{ $t('register.speciality') }}</label>
            <input
              v-model="form.speciality"
              type="text"
              :placeholder="$t('register.teacherSpecialityPlaceholder')"
            />
          </div>

          <!-- Роли администратора (информационные) -->
          
          <!-- Куратор -->
          <div class="form-group checkbox-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="form.isCurator" />
              <span class="checkbox-text">{{ $t('admin.createUsers.isCurator') }}</span>
            </label>
          </div>

          <!-- Мастер-пароль -->
          <div class="form-group">
            <label>{{ $t('admin.createUsers.masterPassword') }} <span class="required">*</span></label>
            <input
              v-model="form.masterPassword"
              type="password"
              :placeholder="$t('admin.createUsers.masterPasswordPlaceholder')"
              required
            />
            <small class="help-text">{{ $t('admin.createUsers.masterPasswordHelp') }}</small>
          </div>

          <!-- Информационная карточка -->
          <div class="info-card">
            <div class="info-icon">ℹ️</div>
            <div class="info-content">
              <p>{{ $t('admin.createUsers.adminHelpText') }}</p>
            </div>
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
import ThemeToggle from '@/components/ThemeToggle.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';
import HomeButton from '@/components/HomeButton.vue';
import api from '@/utils/api';

const { t } = useI18n();
const router = useRouter();

const props = defineProps<{
  onAdminCreated?: () => void;
}>();

const loading = ref(false);
const errorMessage = ref('');
const successMessage = ref('');

const form = ref({
  lastName: '',
  firstName: '',
  patronymic: '',
  email: '',
  password: '',
  speciality: '',
  isCurator: true,
  masterPassword: ''
});

const goBack = () => {
  router.push('/admin');
};

const getFullName = (): string => {
  const parts = [form.value.lastName.trim(), form.value.firstName.trim()];
  if (form.value.patronymic.trim()) {
    parts.push(form.value.patronymic.trim());
  }
  return parts.join(' ');
};

const validateForm = (): boolean => {
  if (!getFullName()) {
    errorMessage.value = t('register.fillNameFields');
    return false;
  }
  
  if (!form.value.email) {
    errorMessage.value = t('register.emailRequired');
    return false;
  }
  
  if (!form.value.password) {
    errorMessage.value = t('register.passwordRequired');
    return false;
  }
  
  if (!form.value.masterPassword) {
    errorMessage.value = t('admin.createUsers.masterPasswordRequired');
    return false;
  }
  
  return true;
};

const createAdmin = async () => {
  errorMessage.value = '';
  successMessage.value = '';
  
  if (!validateForm()) {
    return;
  }
  
  loading.value = true;

  try {
    const fullname = getFullName();
    
    const adminData = {
      fullname,
      email: form.value.email.trim().toLowerCase(),
      password: form.value.password,
      speciality: form.value.speciality,
      master_password: form.value.masterPassword,
      teacher_info: {
        roles: ['customer', 'expert', 'supervisor'],
        curator: form.value.isCurator
      }
    };

    const response = await api.post('/admin/users/create-admin', adminData);
    
    if (response.data) {
      successMessage.value = t('admin.createUsers.userCreated', { name: response.data.fullname });
      
      form.value = {
        lastName: '',
        firstName: '',
        patronymic: '',
        email: '',
        password: '',
        speciality: '',
        isCurator: true,
        masterPassword: ''
      };
      
      if (props.onAdminCreated) props.onAdminCreated();
      
      setTimeout(() => {
        successMessage.value = '';
      }, 3000);
    }
  } catch (error: any) {
    console.error('Create admin error:', error);
    if (error.response?.data?.detail) {
      errorMessage.value = error.response.data.detail;
    } else {
      errorMessage.value = t('admin.createUsers.createError');
    }
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.admin-creator-page {
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

.admin-creator {
  max-width: 700px;
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
  margin-bottom: 28px;
  flex-wrap: wrap;
  gap: 16px;
}

.creator-header h2 {
  margin: 0;
  color: var(--heading-color);
  text-align: center;
  font-size: 1.5rem;
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

.admin-form {
  margin-top: 8px;
}

.form-group {
  margin-bottom: 24px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 0.95rem;
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
  border: 2px solid var(--input-border);
  border-radius: 10px;
  background: var(--input-bg);
  color: var(--text-primary);
  font-size: 1rem;
  transition: all 0.2s;
}

input:focus {
  outline: none;
  border-color: var(--accent-color);
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.1);
}

.roles-info {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 12px;
}

.role-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
}

.role-badge.customer {
  background: rgba(52, 152, 219, 0.15);
  color: #3498db;
  border: 1px solid rgba(52, 152, 219, 0.3);
}

.role-badge.expert {
  background: rgba(155, 89, 182, 0.15);
  color: #9b59b6;
  border: 1px solid rgba(155, 89, 182, 0.3);
}

.role-badge.supervisor {
  background: rgba(241, 196, 15, 0.15);
  color: #f1c40f;
  border: 1px solid rgba(241, 196, 15, 0.3);
}

.role-badge.curator {
  background: rgba(230, 126, 34, 0.15);
  color: #e67e22;
  border: 1px solid rgba(230, 126, 34, 0.3);
}

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
}

.help-text {
  display: block;
  margin-top: 6px;
  color: var(--text-secondary);
  font-size: 0.8rem;
}

.info-card {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: rgba(66, 185, 131, 0.08);
  border-radius: 12px;
  border-left: 4px solid var(--accent-color);
  margin: 20px 0;
}

.info-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.info-content p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.9rem;
  line-height: 1.4;
}

.submit-btn {
  width: 100%;
  padding: 14px;
  background: var(--accent-color);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 20px;
}

.submit-btn:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-1px);
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
  font-size: 0.9rem;
}

.success-message {
  background: rgba(66, 185, 131, 0.1);
  color: var(--accent-color);
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 16px;
  border: 1px solid var(--accent-color);
  font-size: 0.9rem;
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
  
  .theme-toggle-container {
    position: relative;
    justify-content: flex-end;
    margin-bottom: 16px;
  }
  
  .admin-creator {
    margin-top: 0;
    padding: 20px;
  }
  
  .roles-info {
    gap: 8px;
  }
  
  .role-badge {
    font-size: 0.75rem;
    padding: 4px 10px;
  }
  
  .info-card {
    flex-direction: column;
  }
  
  .info-icon {
    text-align: center;
  }
}
</style>