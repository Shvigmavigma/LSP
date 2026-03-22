<template>
  <div class="register-page">
    <div class="theme-toggle-container">
      <ThemeToggle />
    </div>
    <div class="register-card">
      <h2>Регистрация</h2>
      
      <!-- Выбор типа аккаунта -->
      <div class="account-type-selector">
        <button 
          type="button"
          class="type-btn"
          :class="{ active: accountType === 'student' }"
          @click="accountType = 'student'"
        >
          <span class="type-icon">👨‍🎓</span>
          <span class="type-label">Ученик</span>
        </button>
        <button 
          type="button"
          class="type-btn"
          :class="{ active: accountType === 'teacher' }"
          @click="accountType = 'teacher'"
        >
          <span class="type-icon">👨‍🏫</span>
          <span class="type-label">Учитель / Внешний представитель</span>
        </button>
      </div>

      <form @submit.prevent="handleRegister">
        <!-- Поле для выбора аватарки -->
        <div class="form-group avatar-group">
          <label>Аватар (необязательно)</label>
          <div class="avatar-preview">
            <img
              v-if="avatarPreview"
              :src="avatarPreview"
              alt="Avatar preview"
            />
            <span v-else class="avatar-placeholder">
              {{ form.nickname?.charAt(0)?.toUpperCase() || '?' }}
            </span>
          </div>
          <input
            type="file"
            accept="image/*"
            @change="onFileChange"
            ref="fileInput"
            :disabled="loading"
          />
          <button
            type="button"
            class="clear-avatar"
            v-if="avatarFile"
            @click="clearAvatar"
            :disabled="loading"
          >
            ✕
          </button>
        </div>

        <div class="form-group">
          <label for="nickname">Никнейм</label>
          <input
            id="nickname"
            v-model="form.nickname"
            type="text"
            placeholder="Введите никнейм"
            required
          />
        </div>

        <div class="form-group">
          <label for="fullname">Полное имя</label>
          <input
            id="fullname"
            v-model="form.fullname"
            type="text"
            placeholder="Введите полное имя"
            required
          />
        </div>

        <div class="form-group">
          <label for="email">Email</label>
          <input
            id="email"
            v-model="form.email"
            type="email"
            placeholder="Введите email"
            required
          />
          <!-- Сообщение о проверке email для учителя -->
          <small v-if="accountType === 'teacher'" class="email-note">
            ✉️ Для учителей требуется подтверждение email. 
            Используйте email из списка разрешенных.
          </small>
        </div>

        <!-- Поле класса только для учеников -->
        <div v-if="accountType === 'student'" class="form-group">
          <label for="class">Класс</label>
          <ClassInput
            id="class"
            v-model="form.class_"
            placeholder="3.1 – 11.6"
          />
        </div>

        <!-- Поле выбора ролей для учителя -->
        <div v-if="accountType === 'teacher'" class="form-group">
          <label>Роли (можно выбрать несколько) <span class="required-star">*</span></label>
          <div class="roles-selector">
            <!-- Заказчик -->
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
            
            <!-- Эксперт -->
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
            
            <!-- Научный руководитель -->
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
            :placeholder="accountType === 'teacher' ? 'Например, физика, математика' : 'Например, информатика'"
          />
        </div>

        <div class="form-group">
          <label for="password">Пароль</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            placeholder="Введите пароль"
            required
          />
        </div>

        <div class="form-group">
          <label for="confirmPassword">Подтверждение пароля</label>
          <input
            id="confirmPassword"
            v-model="confirmPassword"
            type="password"
            placeholder="Повторите пароль"
            required
            @input="passwordMatchError = false"
          />
        </div>

        <!-- Информация о подтверждении email -->
        <div v-if="accountType === 'teacher'" class="verification-notice">
          <span class="notice-icon">🔐</span>
          <div class="notice-text">
            <strong>Подтверждение обязательно</strong>
            <p>Для регистрации учителя мы проверим, есть ли ваш email в списке разрешенных.</p>
          </div>
        </div>

        <!-- Отображение ошибки, если пароли не совпадают -->
        <div v-if="passwordMatchError" class="error-message">
          Пароли не совпадают
        </div>

        <!-- Ошибка, если не выбрана ни одна роль учителя -->
        <div v-if="accountType === 'teacher' && selectedRoles.length === 0 && showRoleError" class="error-message">
          Пожалуйста, выберите хотя бы одну роль
        </div>

        <!-- Ошибка для email учителя (если не в списке) -->
        <div v-if="teacherEmailError" class="teacher-email-error">
          <span class="error-icon">⚠️</span>
          <div class="error-content">
            <strong>Email не разрешен для регистрации учителя</strong>
            <p>Этот email не находится в списке разрешенных.</p>
          </div>
        </div>

        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>

        <button type="submit" class="register-button" :disabled="loading">
          {{ loading ? 'Регистрация...' : 'Зарегистрироваться' }}
        </button>
      </form>

      <p class="login-link">
        Уже есть аккаунт? <router-link to="/login">Войти</router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import ThemeToggle from '@/components/ThemeToggle.vue';
import ClassInput from '@/components/ClassInput.vue';
import axios from 'axios';

interface RegisterForm {
  nickname: string;
  fullname: string;
  email: string;
  class_?: number;
  speciality: string;
  password: string;
}

const authStore = useAuthStore();
const router = useRouter();

// Тип аккаунта: 'student' или 'teacher'
const accountType = ref<'student' | 'teacher'>('student');

// Роли учителя (множественный выбор)
type TeacherRole = 'customer' | 'expert' | 'supervisor';
const selectedRoles = ref<TeacherRole[]>([]);
const showRoleError = ref(false);

// Флаг ошибки email учителя
const teacherEmailError = ref(false);

const form = reactive<RegisterForm>({
  nickname: '',
  fullname: '',
  email: '',
  class_: 0,
  speciality: '',
  password: '',
});

const loading = ref(false);
const errorMessage = ref('');

// Данные аватарки
const avatarFile = ref<File | null>(null);
const avatarPreview = ref<string | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);

// Поле подтверждения пароля
const confirmPassword = ref('');
const passwordMatchError = ref(false);

// Функция для переключения роли
const toggleRole = (role: TeacherRole) => {
  if (selectedRoles.value.includes(role)) {
    selectedRoles.value = selectedRoles.value.filter(r => r !== role);
  } else {
    selectedRoles.value = [...selectedRoles.value, role];
  }
  showRoleError.value = false;
};

// Функции для перевода роли на русский
const getRoleDisplay = (role: TeacherRole): string => {
  const roles = {
    customer: 'Заказчик',
    expert: 'Эксперт',
    supervisor: 'Научный руководитель'
  };
  return roles[role];
};

const onFileChange = (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (!input.files || input.files.length === 0) {
    clearAvatar();
    return;
  }

  const file = input.files[0];
  if (file.size > 5 * 1024 * 1024) {
    errorMessage.value = 'Файл слишком большой (макс. 5 МБ)';
    clearAvatar();
    return;
  }

  avatarFile.value = file;
  const reader = new FileReader();
  reader.onload = (e) => {
    avatarPreview.value = e.target?.result as string;
  };
  reader.readAsDataURL(file);
};

const clearAvatar = () => {
  avatarFile.value = null;
  avatarPreview.value = null;
  if (fileInput.value) {
    fileInput.value.value = '';
  }
};

// Функция для проверки email учителя через файл
const checkTeacherEmail = async (email: string): Promise<boolean> => {
  try {
    // Загружаем файл accepted_emails.json
    const response = await fetch('/accepted_emails.json');
    const data = await response.json();
    
    // Проверяем, есть ли email в списке
    return data.accepted_emails?.includes(email) || false;
  } catch (error) {
    console.error('Ошибка при загрузке списка разрешенных email:', error);
    return false;
  }
};

const handleRegister = async () => {
  // Сбрасываем ошибки
  teacherEmailError.value = false;
  
  // Проверка совпадения паролей
  if (form.password !== confirmPassword.value) {
    passwordMatchError.value = true;
    return;
  }
  passwordMatchError.value = false;

  // Проверка email
  if (!form.email) {
    errorMessage.value = 'Email обязателен для регистрации';
    return;
  }

  // Для учителя проверяем, выбрана ли хотя бы одна роль
  if (accountType.value === 'teacher') {
    showRoleError.value = false;
    if (selectedRoles.value.length === 0) {
      showRoleError.value = true;
      errorMessage.value = 'Пожалуйста, выберите хотя бы одну роль';
      return;
    }
    
    // Проверяем, есть ли email в списке разрешенных
    const isEmailAccepted = await checkTeacherEmail(form.email);
    if (!isEmailAccepted) {
      teacherEmailError.value = true;
      return;
    }
  }

  loading.value = true;
  errorMessage.value = '';

  try {
    if (accountType.value === 'teacher') {
      await handleTeacherRegistration();
    } else {
      await handleStudentRegistration();
    }
  } catch (error: any) {
    console.error('Registration error:', error);
    
    if (error.response?.status === 400) {
      const detail = error.response.data?.detail;
      errorMessage.value = typeof detail === 'string' 
        ? detail 
        : 'Ошибка регистрации. Возможно, пользователь с таким никнеймом или email уже существует.';
    } else if (error.code === 'ERR_NETWORK') {
      errorMessage.value = 'Ошибка сети. Проверьте подключение к серверу.';
    } else {
      errorMessage.value = error.response?.data?.detail || 'Произошла ошибка при регистрации';
    }
  } finally {
    loading.value = false;
  }
};

// Регистрация ученика
const handleStudentRegistration = async () => {
  const { class_, ...rest } = form;
  const userData = {
    ...rest,
    class: class_ || 0,
    password: form.password,
    is_teacher: false
  };

  try {
    // Используем общий эндпоинт /users/
    const response = await axios.post('http://localhost:8000/users/', userData);
    const newUser = response.data;
    
    console.log('Student created:', newUser);
    
    // Автоматически логиним ученика
    const loginSuccess = await authStore.login(form.nickname, form.password);
    
    if (!loginSuccess) {
      throw new Error('Не удалось выполнить автоматический вход');
    }

    // Загружаем аватарку, если есть
    if (avatarFile.value && authStore.user?.id) {
      await uploadAvatar(authStore.user.id);
    }
    
    router.push('/main');
  } catch (error) {
    console.error('Student registration error:', error);
    throw error;
  }
};

// Регистрация учителя
const handleTeacherRegistration = async () => {
  // Подготовка данных учителя (без куратора)
  const teacherData = {
    nickname: form.nickname,
    fullname: form.fullname,
    email: form.email,
    speciality: form.speciality,
    password: form.password,
    is_teacher: true,
    teacher_info: {
      roles: selectedRoles.value,  // массив выбранных ролей (customer, expert, supervisor)
      curator: false                // по умолчанию false, админ назначит позже
    }
  };

  try {
    // Запрос кода подтверждения
    await axios.post('http://localhost:8000/auth/request-verification-code', {
      email: form.email,
      is_teacher: true
    });
    
    // Сохраняем данные учителя в sessionStorage
    sessionStorage.setItem('pending_registration', JSON.stringify(teacherData));
    console.log('Teacher data saved:', teacherData);

    // Сохраняем аватарку, если есть
    if (avatarFile.value) {
      const reader = new FileReader();
      reader.onload = () => {
        sessionStorage.setItem('pending_avatar', reader.result as string);
      };
      reader.readAsDataURL(avatarFile.value);
      
      setTimeout(() => {
        router.push(`/verify-email?email=${encodeURIComponent(form.email)}`);
      }, 500);
    } else {
      router.push(`/verify-email?email=${encodeURIComponent(form.email)}`);
    }
    
  } catch (error: any) {
    console.error('Error requesting verification code:', error);
    
    if (error.response?.status === 400) {
      errorMessage.value = 'Ошибка при отправке кода. Проверьте email и попробуйте снова.';
    } else {
      throw error;
    }
  }
};

// Загрузка аватарки
const uploadAvatar = async (userId: number) => {
  if (!avatarFile.value) return;
  
  const formData = new FormData();
  formData.append('file', avatarFile.value);

  const response = await axios.post(
    `http://localhost:8000/users/${userId}/avatar`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  );

  if (authStore.user) {
    authStore.user.avatar = response.data.avatar;
  }
};
</script>

<style scoped>
/* Стили полностью скопированы из исходного файла */
.register-page {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: var(--bg-page);
  margin: -20px;
  padding: 20px;
  position: relative;
  transition: background 0.3s;
}

.theme-toggle-container {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 10;
}

.register-card {
  background: var(--bg-card);
  border-radius: 16px;
  box-shadow: var(--shadow-strong);
  padding: 40px 32px;
  width: 100%;
  max-width: 650px;
  transition: transform 0.2s ease, background 0.3s;
}

.register-card:hover {
  transform: translateY(-4px);
}

h2 {
  text-align: center;
  color: var(--heading-color);
  margin-bottom: 28px;
  font-weight: 500;
}

/* Стили для выбора типа аккаунта */
.account-type-selector {
  display: flex;
  gap: 15px;
  margin-bottom: 30px;
  justify-content: center;
}

.type-btn {
  flex: 1;
  max-width: 150px;
  padding: 15px 10px;
  border: 2px solid var(--border-color);
  border-radius: 12px;
  background: var(--input-bg);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.type-btn.active {
  border-color: var(--accent-color);
  background: rgba(66, 185, 131, 0.1);
  color: var(--accent-color);
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(66, 185, 131, 0.2);
}

.type-icon {
  font-size: 2rem;
}

.type-label {
  font-size: 1rem;
  font-weight: 500;
}

/* Стили для выбора ролей учителя */
.roles-selector {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 8px;
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
  position: relative;
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

/* Стили для отображения выбранных ролей */
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

.required-star {
  color: var(--danger-color);
  margin-left: 4px;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 8px;
  color: var(--text-secondary);
  font-size: 0.95rem;
  font-weight: 500;
}

.email-note {
  display: block;
  margin-top: 6px;
  color: var(--accent-color);
  font-size: 0.85rem;
}

.verification-notice {
  margin: 20px 0;
  padding: 12px 16px;
  background: rgba(66, 185, 131, 0.1);
  border-radius: 8px;
  border-left: 4px solid var(--accent-color);
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.notice-icon {
  font-size: 1.5rem;
}

.notice-text {
  flex: 1;
}

.notice-text strong {
  color: var(--accent-color);
  display: block;
  margin-bottom: 4px;
}

.notice-text p {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin: 0;
}

/* Стиль для ошибки email учителя */
.teacher-email-error {
  background: var(--error-bg);
  border: 2px solid var(--danger-color);
  border-radius: 8px;
  padding: 16px;
  margin: 20px 0;
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.error-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.error-content {
  flex: 1;
}

.error-content strong {
  display: block;
  color: var(--danger-color);
  margin-bottom: 4px;
  font-size: 1rem;
}

.error-content p {
  color: var(--text-secondary);
  font-size: 0.95rem;
  margin: 0;
  line-height: 1.4;
}

input[type="text"],
input[type="email"],
input[type="password"],
input[type="number"] {
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
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.2);
}

.dark-theme input:focus {
  box-shadow: 0 0 0 3px rgba(1, 69, 172, 0.2);
}

.error-message {
  background: var(--error-bg);
  color: var(--danger-color);
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 20px;
  text-align: center;
  border: 1px solid var(--danger-color);
  font-size: 0.95rem;
}

.register-button {
  width: 100%;
  padding: 14px;
  background-color: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.1s;
  margin-top: 20px;
}

.register-button:hover:not(:disabled) {
  background-color: var(--accent-hover);
}

.register-button:active:not(:disabled) {
  transform: scale(0.98);
}

.register-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.login-link {
  text-align: center;
  margin-top: 24px;
  color: var(--text-secondary);
  font-size: 0.95rem;
}

.login-link a {
  color: var(--link-color);
  text-decoration: none;
  font-weight: 500;
}

.login-link a:hover {
  color: var(--link-hover);
  text-decoration: underline;
}

.avatar-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 24px;
}

.avatar-preview {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: var(--accent-color);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
  overflow: hidden;
  color: var(--button-text);
  font-size: 36px;
  font-weight: bold;
}

.avatar-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

input[type="file"] {
  padding: 8px;
  background: var(--input-bg);
  border: 1px solid var(--input-border);
  border-radius: 8px;
  color: var(--text-primary);
  cursor: pointer;
  margin-bottom: 8px;
  width: 100%;
  box-sizing: border-box;
}

input[type="file"]::-webkit-file-upload-button {
  background: var(--accent-color);
  color: var(--button-text);
  border: none;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  margin-right: 10px;
}

.clear-avatar {
  background: none;
  border: none;
  color: var(--danger-color);
  font-size: 1.2rem;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.2s;
}

.clear-avatar:hover:not(:disabled) {
  background: rgba(255, 0, 0, 0.1);
}

.clear-avatar:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 600px) {
  .register-card {
    padding: 30px 20px;
  }
  
  .role-btn {
    padding: 12px;
  }
  
  .role-icon {
    font-size: 1.5rem;
    min-width: 40px;
  }
  
  .role-label {
    font-size: 1rem;
  }
  
  .role-desc {
    font-size: 0.8rem;
  }
  
  .selected-role-tag {
    padding: 4px 10px;
    font-size: 0.85rem;
  }
  
  .teacher-email-error {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
}
</style>