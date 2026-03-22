<template>
  <div class="profile-edit-page">
    <header class="edit-header">
      <h1>Редактирование профиля</h1>
      <div class="header-actions">
        <ThemeToggle />
        <button class="home-button" @click="goHome" title="На главную">🏠</button>
      </div>
    </header>

    <div v-if="loading" class="loading">Загрузка...</div>
    <div v-else class="edit-card">
      <!-- Секция аватарки -->
      <div class="avatar-section">
        <div class="avatar-preview">
          <img
            v-if="previewAvatar || (authStore.user?.avatar && !avatarError)"
            :src="previewAvatar || `http://localhost:8000/avatars/${authStore.user?.avatar}`"
            :alt="authStore.user?.nickname"
            @error="avatarError = true"
          />
          <span v-else>{{ authStore.user?.nickname?.charAt(0).toUpperCase() || '?' }}</span>
        </div>
        <label class="avatar-upload-label">
          <input
            type="file"
            accept="image/*"
            @change="handleAvatarUpload"
            :disabled="uploading"
          />
          <span class="upload-button">{{ uploading ? 'Загрузка...' : 'Загрузить аватар' }}</span>
        </label>
        <div v-if="uploadError" class="upload-error">{{ uploadError }}</div>
      </div>

      <form @submit.prevent="handleSave">
        <div class="form-group">
          <label for="fullname">Полное имя</label>
          <input
            id="fullname"
            v-model="form.fullname"
            type="text"
            required
          />
        </div>

        <div class="form-group">
          <label for="email">Email</label>
          <input
            id="email"
            v-model="form.email"
            type="email"
            required
          />
        </div>

        <!-- Поле класса только для учеников -->
        <div v-if="!isTeacher" class="form-group">
          <label for="class">Класс</label>
          <ClassInput
            id="class"
            v-model="form.class"
            placeholder="3.1 – 11.6"
          />
        </div>

        <!-- Интерфейс редактирования ролей для учителя (без куратора) -->
        <div v-else class="form-group">
          <label>Роли (можно выбрать несколько)</label>
          <div class="roles-selector">
            <button
              type="button"
              class="role-btn"
              :class="{ active: selectedRoles.includes('customer') }"
              @click="toggleRole('customer')"
            >
              <span class="role-checkbox" :class="{ checked: selectedRoles.includes('customer') }">
                <span v-if="selectedRoles.includes('customer')">✓</span>
              </span>
              <span class="role-icon">📋</span>
              <span class="role-label">Заказчик</span>
              <span class="role-desc">Формулирует задачи и требования</span>
            </button>

            <button
              type="button"
              class="role-btn"
              :class="{ active: selectedRoles.includes('expert') }"
              @click="toggleRole('expert')"
            >
              <span class="role-checkbox" :class="{ checked: selectedRoles.includes('expert') }">
                <span v-if="selectedRoles.includes('expert')">✓</span>
              </span>
              <span class="role-icon">🔍</span>
              <span class="role-label">Эксперт</span>
              <span class="role-desc">Оценивает и проверяет работы</span>
            </button>

            <button
              type="button"
              class="role-btn"
              :class="{ active: selectedRoles.includes('supervisor') }"
              @click="toggleRole('supervisor')"
            >
              <span class="role-checkbox" :class="{ checked: selectedRoles.includes('supervisor') }">
                <span v-if="selectedRoles.includes('supervisor')">✓</span>
              </span>
              <span class="role-icon">🎓</span>
              <span class="role-label">Научный руководитель</span>
              <span class="role-desc">Направляет и консультирует</span>
            </button>
          </div>

          <!-- Отображение выбранных ролей -->
          <div v-if="selectedRoles.length > 0" class="selected-roles">
            <span class="selected-roles-label">Выбрано:</span>
            <span class="selected-role-tag" v-for="role in selectedRoles" :key="role">
              {{ getRoleDisplay(role) }}
            </span>
          </div>
        </div>

        <div class="form-group">
          <label for="speciality">Специальность / Предмет</label>
          <input
            id="speciality"
            v-model="form.speciality"
            type="text"
          />
        </div>

        <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>

        <div class="button-group">
          <button type="submit" class="save-button" :disabled="saving">
            {{ saving ? 'Сохранение...' : 'Сохранить' }}
          </button>
          <button type="button" class="cancel-button" @click="goBack">
            Отмена
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';
import ThemeToggle from '@/components/ThemeToggle.vue';
import axios from 'axios';
import ClassInput from '@/components/ClassInput.vue';
import type { TeacherInfo } from '@/types';

const authStore = useAuthStore();
const router = useRouter();

const form = ref({
  fullname: '',
  email: '',
  class: 0,
  speciality: '',
});

const loading = ref(true);
const saving = ref(false);
const errorMessage = ref('');

// Для аватарки
const uploading = ref(false);
const uploadError = ref('');
const previewAvatar = ref<string | null>(null);
const avatarError = ref(false);

// Для ролей учителя (без куратора)
const selectedRoles = ref<string[]>([]);
// Сохраняем текущее значение куратора, чтобы не потерять
const currentCurator = ref(false);

const isTeacher = computed(() => authStore.user?.is_teacher || false);

function getRoleDisplay(role: string): string {
  const roles: Record<string, string> = {
    customer: 'Заказчик',
    expert: 'Эксперт',
    supervisor: 'Научный руководитель'
  };
  return roles[role] || role;
}

function toggleRole(role: string) {
  if (selectedRoles.value.includes(role)) {
    selectedRoles.value = selectedRoles.value.filter(r => r !== role);
  } else {
    selectedRoles.value = [...selectedRoles.value, role];
  }
}

onMounted(() => {
  if (authStore.user) {
    const user = authStore.user;
    form.value = {
      fullname: user.fullname,
      email: user.email,
      class: user.is_teacher ? 0 : (user.class !== 0 ? user.class : 3.1),
      speciality: user.speciality || '',
    };

    // Если учитель, загружаем текущие роли и куратора
    if (user.is_teacher && user.teacher_info) {
      selectedRoles.value = user.teacher_info.roles || [];
      currentCurator.value = user.teacher_info.curator || false;
    }
  }
  loading.value = false;
});

const handleAvatarUpload = async (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (!input.files || input.files.length === 0) return;

  const file = input.files[0];
  if (file.size > 5 * 1024 * 1024) {
    uploadError.value = 'Файл слишком большой (макс. 5 МБ)';
    return;
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    previewAvatar.value = e.target?.result as string;
  };
  reader.readAsDataURL(file);

  uploading.value = true;
  uploadError.value = '';

  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await axios.post(
      `http://localhost:8000/users/${authStore.user!.id}/avatar`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    );
    authStore.user = response.data;
    localStorage.setItem('user', JSON.stringify(response.data));
    previewAvatar.value = null;
    avatarError.value = false;
  } catch (error: any) {
    console.error('Error uploading avatar:', error);
    uploadError.value = error.response?.data?.detail || 'Ошибка загрузки аватарки';
    previewAvatar.value = null;
  } finally {
    uploading.value = false;
  }
};

const handleSave = async () => {
  if (!authStore.user) return;

  saving.value = true;
  errorMessage.value = '';

  try {
    let response;

    if (isTeacher.value) {
      // Для учителя используем эндпоинт /teachers/{id} с сохранением текущего куратора
      const teacherInfo: TeacherInfo = {
        roles: selectedRoles.value,
        curator: currentCurator.value // сохраняем текущее значение куратора
      };
      const updateData = {
        fullname: form.value.fullname,
        email: form.value.email,
        speciality: form.value.speciality,
        teacher_info: teacherInfo
      };
      response = await axios.put(
        `http://localhost:8000/teachers/${authStore.user.id}`,
        updateData
      );
    } else {
      // Для ученика используем эндпоинт /users/{id} с классом
      const { class: classValue, ...rest } = form.value;
      const updateData = {
        ...rest,
        class_: classValue
      };
      response = await axios.put(
        `http://localhost:8000/users/${authStore.user.id}`,
        updateData
      );
    }

    authStore.user = response.data;
    localStorage.setItem('user', JSON.stringify(response.data));

    router.push('/profile');
  } catch (error: any) {
    console.error('Error updating profile:', error);
    errorMessage.value =
      error.response?.data?.detail || 'Ошибка при сохранении данных';
  } finally {
    saving.value = false;
  }
};

const goBack = () => {
  router.push('/profile');
};

const goHome = () => {
  router.push('/main');
};
</script>

<style scoped>
.profile-edit-page {
  min-height: 100vh;
  background: var(--bg-page);
  padding: 20px;
  box-sizing: border-box;
  transition: background 0.3s;
}

.edit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 500px;
  margin: 0 auto 20px;
}

.edit-header h1 {
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
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
  color: var(--text-primary);
}

.home-button:hover {
  background: rgba(255, 255, 255, 0.1);
}

.light-theme .home-button:hover {
  background: rgba(0, 0, 0, 0.05);
}

.edit-card {
  background: var(--bg-card);
  border-radius: 32px;
  box-shadow: var(--shadow);
  padding: 40px;
  max-width: 500px;
  margin: 0 auto;
  transition: background 0.3s;
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 30px;
}

.avatar-preview {
  width: 100px;
  height: 100px;
  background: var(--accent-color);
  color: var(--button-text);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  font-weight: bold;
  margin-bottom: 12px;
  overflow: hidden;
}

.avatar-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.avatar-preview span {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.avatar-upload-label {
  cursor: pointer;
}

.avatar-upload-label input {
  display: none;
}

.upload-button {
  display: inline-block;
  padding: 10px 20px;
  background-color: var(--accent-color);
  color: var(--button-text);
  border-radius: 50px;
  font-size: 0.9rem;
  font-weight: 600;
  transition: background-color 0.2s;
}

.upload-button:hover {
  background-color: var(--accent-hover);
}

.upload-error {
  color: var(--danger-color);
  font-size: 0.9rem;
  margin-top: 8px;
  text-align: center;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 6px;
  color: var(--text-secondary);
  font-weight: 500;
}

input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s, box-shadow 0.2s;
  outline: none;
  box-sizing: border-box;
  background: var(--input-bg);
  color: var(--text-primary);
}

input:focus {
  border-color: var(--accent-color);
  box-shadow: 0 0 0 3px rgba(1, 69, 172, 0.2);
}

.light-theme input:focus {
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.2);
}

/* Стили для выбора ролей (как в регистрации) */
.roles-selector {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 8px;
  margin-bottom: 16px;
}

.role-btn {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 16px;
  border: 2px solid var(--border-color);
  border-radius: 12px;
  background: var(--input-bg);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.3s ease;
  width: 100%;
  text-align: left;
}

.role-btn.active {
  border-color: var(--accent-color);
  background: rgba(66, 185, 131, 0.1);
  color: var(--accent-color);
  transform: scale(1.02);
  box-shadow: 0 4px 12px rgba(66, 185, 131, 0.2);
}

.role-checkbox {
  width: 24px;
  height: 24px;
  border: 2px solid var(--border-color);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
  color: white;
  background: transparent;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.role-checkbox.checked {
  background: var(--accent-color);
  border-color: var(--accent-color);
  color: white;
}

.role-icon {
  font-size: 2rem;
  min-width: 48px;
  text-align: center;
}

.role-label {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 4px;
}

.role-desc {
  font-size: 0.85rem;
  opacity: 0.8;
  display: block;
}

.selected-roles {
  margin-top: 16px;
  padding: 12px;
  background: rgba(66, 185, 131, 0.05);
  border-radius: 8px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.selected-roles-label {
  color: var(--text-secondary);
  font-size: 0.95rem;
  font-weight: 500;
}

.selected-role-tag {
  background: var(--accent-color);
  color: white;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 500;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.error-message {
  background: var(--error-bg);
  color: var(--danger-color);
  padding: 10px;
  border-radius: 8px;
  margin-bottom: 20px;
  text-align: center;
  border: 1px solid var(--danger-color);
}

.button-group {
  display: flex;
  gap: 12px;
  margin-top: 32px;
}

.save-button, .cancel-button {
  flex: 1;
  padding: 14px;
  border: none;
  border-radius: 50px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.save-button {
  background-color: var(--accent-color);
  color: var(--button-text);
}

.save-button:hover:not(:disabled) {
  background-color: var(--accent-hover);
}

.save-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.cancel-button {
  background-color: var(--bg-page);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.cancel-button:hover {
  background-color: var(--bg-card);
}

.loading {
  text-align: center;
  color: var(--text-primary);
  font-size: 1.2rem;
  padding: 40px;
}
</style>