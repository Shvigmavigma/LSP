<template>
  <div class="admin-project-creator-page">
    <div class="theme-toggle-container">
      <ThemeToggle />
      <LanguageSwitcher />
      <HomeButton />
    </div>

    <div class="admin-project-creator">
      <div class="creator-header">
        <button class="back-btn" @click="goBack">
          ← {{ $t('common.back') }}
        </button>
        <h2>{{ $t('admin.createProject.title') }}</h2>
        <div class="placeholder"></div>
      </div>

      <!-- Информационная подсказка -->
      <div class="admin-hint">
        <span class="hint-icon">⚙️</span>
        <span class="hint-text">{{ $t('admin.createProject.adminHint') }}</span>
      </div>

      <form @submit.prevent="handleSubmit">
        <!-- Основная информация -->
        <div class="form-section">
          <h2>{{ $t('projectEdit.basicInfo') }}</h2>
          
          <div class="form-group">
            <label for="title">{{ $t('projectEdit.projectTitle') }} <span class="required">*</span></label>
            <input id="title" v-model="form.title" type="text" required />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="class_key">{{ $t('projectEdit.classKey') }}</label>
              <select id="class_key" v-model="form.class_key">
                <option value="">{{ $t('common.notSelected') }}</option>
                <option value="8">8</option>
                <option value="9">9</option>
                <option value="10">10</option>
                <option value="11">11</option>
              </select>
            </div>
            <div class="form-group">
              <label for="direction_key">{{ $t('projectEdit.directionKey') }}</label>
              <input id="direction_key" v-model="form.direction_key" type="text" :placeholder="$t('projectEdit.directionPlaceholder')" />
            </div>
          </div>

          <div class="form-group">
            <label for="body">{{ $t('projectEdit.description') }} <span class="required">*</span></label>
            <textarea id="body" v-model="form.body" rows="4" required></textarea>
          </div>

          <div class="form-group">
            <label for="underbody">{{ $t('projectEdit.additionalInfo') }}</label>
            <textarea id="underbody" v-model="form.underbody" rows="2"></textarea>
          </div>
        </div>

        <!-- Обязательный заказчик -->
        <div class="form-section required-customer-section">
          <h2>
            {{ $t('admin.createProject.requiredCustomer') }}
            <span class="required-badge">{{ $t('common.required') }}</span>
          </h2>
          <p class="section-hint">{{ $t('admin.createProject.customerRequiredHint') }}</p>

          <div class="customer-selector">
            <div class="form-group">
              <label for="customerSearch">{{ $t('admin.createProject.searchCustomer') }}</label>
              <input
                id="customerSearch"
                v-model="customerSearchQuery"
                type="text"
                :placeholder="$t('admin.createProject.searchCustomerPlaceholder')"
                @input="searchCustomers"
              />
              <UserSearchFilters v-model="userFilters" @change="refreshUserSearches" />
              <div v-if="customerSearchResults.length > 0 && !selectedCustomer" class="search-results">
                <div
                  v-for="user in customerSearchResults"
                  :key="user.id"
                  class="search-result-item"
                  @click="selectCustomer(user)"
                >
                  <span class="result-name">{{ getUserDisplayName(user) }}</span>
                  <span class="result-email">{{ user.email }}</span>
                  <span class="result-type">{{ user.is_teacher ? $t('register.teacher') : $t('register.student') }}</span>
                </div>
              </div>
            </div>

            <div v-if="selectedCustomer" class="selected-customer">
              <div class="customer-info">
                <div class="customer-avatar">
                  <img v-if="selectedCustomer.avatar" :src="`${baseUrl}/avatars/${selectedCustomer.avatar}`" alt="Avatar" />
                  <span v-else class="avatar-placeholder">{{ getInitial(selectedCustomer.fullname) }}</span>
                </div>
                <div class="customer-details">
                  <div class="customer-name">{{ getUserDisplayName(selectedCustomer) }}</div>
                  <div class="customer-email">{{ selectedCustomer.email }}</div>
                  <div class="customer-type">
                    {{ selectedCustomer.is_teacher ? $t('register.teacher') : $t('register.student') }}
                  </div>
                </div>
                <button type="button" class="remove-customer" @click="removeCustomer">✕</button>
              </div>
            </div>

            <div v-if="customerError" class="error-message">{{ customerError }}</div>
          </div>
        </div>

        <!-- Остальные участники (опционально) -->
        <div class="form-section">
          <h2>{{ $t('projectEdit.participants') }}</h2>
          <p class="section-hint">{{ $t('admin.createProject.otherParticipantsHint') }}</p>

          <div class="participants-section">
            <div v-if="otherParticipants.length > 0" class="participants-list">
              <div
                v-for="(p, index) in otherParticipants"
                :key="p.user_id"
                class="participant-item"
              >
                <div class="participant-info">
                  <div class="participant-avatar">
                    <img v-if="p.avatar" :src="`${baseUrl}/avatars/${p.avatar}`" alt="Avatar" />
                    <span v-else class="avatar-placeholder small">{{ getInitial(p.fullname) }}</span>
                  </div>
                  <div class="participant-details">
                    <span class="participant-name">{{ p.fullname }}</span>
                    <span class="participant-email">{{ p.email }}</span>
                  </div>
                </div>
                <div class="participant-role-selector">
                  <select v-model="p.role">
                    <option value="executor">{{ $t('roles.executor') }}</option>
                    <option value="supervisor">{{ $t('roles.supervisor') }}</option>
                    <option value="expert">{{ $t('roles.expert') }}</option>
                    <option value="curator">{{ $t('roles.curator') }}</option>
                  </select>
                </div>
                <button type="button" class="remove-participant" @click="removeOtherParticipant(index)">✕</button>
              </div>
            </div>

            <div class="add-participant-section">
              <div class="add-participant-input">
                <input
                  v-model="participantSearchQuery"
                  type="text"
                  :placeholder="$t('admin.createProject.addParticipantPlaceholder')"
                  @input="searchParticipants"
                />
                <button type="button" @click="showParticipantSearch = !showParticipantSearch" class="toggle-search-btn">
                  {{ showParticipantSearch ? '−' : '+' }}
                </button>
              </div>

              <div v-if="showParticipantSearch && participantSearchResults.length > 0" class="participant-search-results">
                <div
                  v-for="user in participantSearchResults"
                  :key="user.id"
                  class="search-result-item"
                  @click="addParticipant(user)"
                >
                  <span class="result-name">{{ getUserDisplayName(user) }}</span>
                  <span class="result-email">{{ user.email }}</span>
                  <button class="add-btn">+</button>
                </div>
              </div>
            </div>

            <p v-if="otherParticipants.length === 0 && !showParticipantSearch" class="no-participants">
              {{ $t('admin.createProject.noOtherParticipants') }}
            </p>
          </div>
        </div>

        <!-- Необходимые роли -->
        <div class="form-section">
          <h2>{{ $t('projectEdit.requiredRoles') }}</h2>
          <div class="required-roles-table">
            <div class="role-row header-row">
              <div class="role-name">{{ $t('projectEdit.role') }}</div>
              <div class="role-target">{{ $t('projectEdit.roleTarget') }}</div>
            </div>
            <div v-for="role in allRoles" :key="role" class="role-row">
              <div class="role-name">{{ getRoleDisplay(role) }}</div>
              <div class="role-target">
                <input
                  type="number"
                  min="0"
                  step="1"
                  v-model.number="requiredRolesValue[role]"
                  class="target-input"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Задачи -->
        <div class="form-section">
          <div class="tasks-header">
            <h2>{{ $t('projectEdit.tasks') }}</h2>
            <button type="button" class="add-task-button" @click="addTask">
              + {{ $t('projectEdit.addTask') }}
            </button>
          </div>

          <div v-if="tasks.length === 0" class="no-tasks">
            {{ $t('projectEdit.noTasks') }}
          </div>

          <div v-else class="tasks-list">
            <div
              v-for="(task, index) in tasks"
              :key="index"
              class="task-item"
              :class="{ expanded: task.expanded }"
            >
              <div v-if="!task.expanded" class="task-compact" @click="toggleTaskExpand(index)">
                <span class="task-title">{{ task.title || $t('projectEdit.untitled') }}</span>
                <button
                  type="button"
                  class="delete-task-button"
                  @click.stop="removeTask(index)"
                >✕</button>
              </div>

              <div v-else class="task-form">
                <div class="task-form-header">
                  <h3>{{ task.id ? $t('projectEdit.editTask') : $t('projectEdit.newTask') }}</h3>
                  <button type="button" class="close-task-form" @click="toggleTaskExpand(index)">✕</button>
                </div>

                <div class="form-group">
                  <label>{{ $t('projectEdit.taskTitle') }} <span class="required">*</span></label>
                  <input v-model="task.title" type="text" required />
                </div>

                <div class="form-group">
                  <label>{{ $t('projectEdit.taskStatus') }}</label>
                  <select v-model="task.status">
                    <option value="в работе">{{ $t('projectEdit.status.inProgress') }}</option>
                    <option value="ожидает">{{ $t('projectEdit.status.waiting') }}</option>
                    <option value="выполнена">{{ $t('projectEdit.status.completed') }}</option>
                  </select>
                </div>

                <div class="form-group">
                  <label>{{ $t('projectEdit.taskDescription') }} <span class="required">*</span></label>
                  <textarea v-model="task.body" rows="2" required></textarea>
                </div>

                <div class="form-row">
                  <div class="form-group">
                    <label>{{ $t('projectEdit.startDate') }}</label>
                    <input
                      :value="task.timeline"
                      @input="updateTaskDate(index, 'timeline', $event)"
                      type="text"
                      :placeholder="$t('projectEdit.datePlaceholder')"
                    />
                  </div>
                  <div class="form-group">
                    <label>{{ $t('projectEdit.endDate') }}</label>
                    <input
                      :value="task.timelinend"
                      @input="updateTaskDate(index, 'timelinend', $event)"
                      type="text"
                      :placeholder="$t('projectEdit.datePlaceholder')"
                    />
                  </div>
                </div>

                <div class="task-form-actions">
                  <button type="button" class="save-task-button" @click="saveTask(index)">✓ {{ $t('common.save') }}</button>
                  <button type="button" class="cancel-task-button" @click="toggleTaskExpand(index)">{{ $t('common.cancel') }}</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Кнопки отправки -->
        <div class="form-actions">
          <button type="submit" class="save-button" :disabled="saving || !isValid">
            {{ saving ? $t('common.creating') : $t('admin.createProject.createProject') }}
          </button>
          <button type="button" class="cancel-button" @click="goBack">{{ $t('common.cancel') }}</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '@/stores/auth';
import { useUsersStore } from '@/stores/users';
import ThemeToggle from '@/components/ThemeToggle.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';
import HomeButton from '@/components/HomeButton.vue';
import api from '@/utils/api';
import UserSearchFilters, { type UserSearchFilterValue } from '@/components/UserSearchFilters.vue';

const { t } = useI18n();
const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const router = useRouter();
const authStore = useAuthStore();
const usersStore = useUsersStore();

// State
const saving = ref(false);
const showParticipantSearch = ref(false);
const customerSearchQuery = ref('');
const participantSearchQuery = ref('');
const selectedCustomer = ref<any>(null);
const customerSearchResults = ref<any[]>([]);
const participantSearchResults = ref<any[]>([]);
const customerError = ref('');
const userFilters = ref<UserSearchFilterValue>({});

// Тип для участника
interface OtherParticipant {
  user_id: number;
  email: string;
  fullname: string;
  avatar: string | null;
  role: string;
}

// Форма проекта
const form = reactive({
  title: '',
  class_key: '',
  direction_key: '',
  body: '',
  underbody: '',
});

// Участники (кроме заказчика)
const otherParticipants = ref<OtherParticipant[]>([]);

// Необходимые роли
const requiredRolesValue = ref<Record<string, number>>({
  customer: 1,
  executor: 0,
  supervisor: 0,
  expert: 0,
  curator: 0
});

// Все возможные роли
const allRoles: string[] = ['customer', 'supervisor', 'expert', 'executor', 'curator'];

// Задачи
type EditableTask = {
  id?: string;
  title: string;
  status: string;
  body: string;
  timeline: string;
  timelinend: string;
  expanded: boolean;
};

const tasks = ref<EditableTask[]>([]);

// Валидация
const isValid = computed(() => {
  if (!form.title.trim()) return false;
  if (!form.body.trim()) return false;
  if (!selectedCustomer.value) return false;
  return true;
});

// Вспомогательная функция для получения инициалов
const getInitial = (fullname: string): string => {
  if (!fullname) return '?';
  const parts = fullname.split(' ');
  if (parts.length >= 2) {
    return (parts[0].charAt(0) + parts[1].charAt(0)).toUpperCase();
  }
  return fullname.charAt(0).toUpperCase();
};

// Методы
const getUserDisplayName = (user: any): string => {
  if (!user) return '';
  return user.fullname || `${user.lastName || ''} ${user.firstName || ''}`.trim();
};

const getRoleDisplay = (role: string): string => {
  return t(`roles.${role}`);
};

const searchCustomers = async () => {
  if (!customerSearchQuery.value.trim()) {
    customerSearchResults.value = [];
    return;
  }
  try {
    const response = await api.get('/users/', { params: { q: customerSearchQuery.value, ...userFilters.value } });
    customerSearchResults.value = response.data;
  } catch (error) {
    console.error('Error searching users:', error);
  }
};

const searchParticipants = async () => {
  if (!participantSearchQuery.value.trim()) {
    participantSearchResults.value = [];
    return;
  }
  try {
    const response = await api.get('/users/', { params: { q: participantSearchQuery.value, ...userFilters.value } });
    participantSearchResults.value = response.data.filter(
      (u: any) => 
        (!selectedCustomer.value || u.id !== selectedCustomer.value.id) &&
        !otherParticipants.value.some(p => p.user_id === u.id)
    );
  } catch (error) {
    console.error('Error searching users:', error);
  }
};

const refreshUserSearches = () => {
  if (customerSearchQuery.value.trim()) searchCustomers();
  if (participantSearchQuery.value.trim()) searchParticipants();
};

const selectCustomer = (user: any) => {
  selectedCustomer.value = user;
  customerSearchQuery.value = '';
  customerSearchResults.value = [];
  customerError.value = '';
};

const removeCustomer = () => {
  selectedCustomer.value = null;
  customerError.value = '';
};

const addParticipant = (user: any) => {
  if (otherParticipants.value.some(p => p.user_id === user.id)) return;
  if (selectedCustomer.value && selectedCustomer.value.id === user.id) return;
  
  otherParticipants.value.push({
    user_id: user.id,
    email: user.email,
    fullname: user.fullname,
    avatar: user.avatar,
    role: 'executor'
  });
  
  participantSearchQuery.value = '';
  participantSearchResults.value = [];
  showParticipantSearch.value = false;
};

const removeOtherParticipant = (index: number) => {
  otherParticipants.value.splice(index, 1);
};

// Функции для задач
const formatDateInput = (value: string): string => {
  let digits = value.replace(/\D/g, '');
  if (digits.length > 8) digits = digits.slice(0, 8);
  let formatted = '';
  if (digits.length > 0) {
    formatted = digits.slice(0, 2);
    if (digits.length > 2) formatted += '.' + digits.slice(2, 4);
    if (digits.length > 4) formatted += '.' + digits.slice(4, 8);
  }
  return formatted;
};

const updateTaskDate = (index: number, field: 'timeline' | 'timelinend', event: Event) => {
  const task = tasks.value[index];
  if (!task) return;
  const input = event.target as HTMLInputElement;
  task[field] = formatDateInput(input.value);
};

const addTask = () => {
  tasks.value.push({
    title: '',
    status: 'ожидает',
    body: '',
    timeline: '',
    timelinend: '',
    expanded: true,
  });
};

const saveTask = (index: number) => {
  const task = tasks.value[index];
  if (!task.title.trim()) {
    return;
  }
  if (!task.body.trim()) {
    return;
  }
  task.expanded = false;
};

const removeTask = (index: number) => {
  tasks.value.splice(index, 1);
};

const toggleTaskExpand = (index: number) => {
  tasks.value[index].expanded = !tasks.value[index].expanded;
};

// Создание проекта
const handleSubmit = async () => {
  if (!isValid.value) {
    if (!selectedCustomer.value) {
      customerError.value = t('admin.createProject.customerRequired');
    }
    return;
  }

  saving.value = true;

  try {
    // Формируем список участников - ТОЛЬКО заказчик и добавленные участники
    // Админ НЕ добавляется автоматически!
    const participants = [
      {
        user_id: selectedCustomer.value.id,
        role: 'customer',
        joined_at: new Date().toISOString(),
      },
      ...otherParticipants.value.map(p => ({
        user_id: p.user_id,
        role: p.role,
        joined_at: new Date().toISOString(),
      }))
    ];

    const projectData = {
      title: form.title,
      class_key: form.class_key || null,
      direction_key: form.direction_key || null,
      body: form.body,
      underbody: form.underbody || '',
      participants: participants,
      required_roles: requiredRolesValue.value,
      tasks: tasks.value.map(({ expanded, ...task }) => task),
    };

    const response = await api.post('/projects/', projectData);
    
    if (response.data) {
      router.push(`/project/${response.data.id}`);
    }
  } catch (error: any) {
    console.error('Error creating project:', error);
  } finally {
    saving.value = false;
  }
};

const goBack = () => {
  router.push('/admin');
};

// Загрузка пользователей при монтировании
onMounted(async () => {
  if (usersStore.users.length === 0) {
    await usersStore.fetchAllUsers();
  }
});
</script>

<style scoped>
.admin-project-creator-page {
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

.admin-project-creator {
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

.admin-hint {
  background: rgba(255, 193, 7, 0.1);
  border-left: 4px solid #ffc107;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.hint-icon {
  font-size: 1.2rem;
}

.hint-text {
  color: var(--text-primary);
  font-size: 0.95rem;
}

.form-section {
  margin-bottom: 32px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border-color);
}

.form-section h2 {
  color: var(--heading-color);
  margin-bottom: 16px;
  font-size: 1.3rem;
}

.required {
  color: var(--danger-color);
}

.required-badge {
  background: var(--danger-color);
  color: white;
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 12px;
  margin-left: 8px;
  vertical-align: middle;
}

.section-hint {
  color: var(--text-secondary);
  font-size: 0.85rem;
  margin-bottom: 16px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  color: var(--text-secondary);
  font-weight: 500;
}

input, select, textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-primary);
  font-size: 0.95rem;
}

input:focus, select:focus, textarea:focus {
  outline: none;
  border-color: var(--accent-color);
}

/* Customer selector */
.required-customer-section {
  background: rgba(66, 185, 131, 0.05);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid var(--accent-color);
}

.search-results, .participant-search-results {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-card);
  margin-top: 8px;
}

.search-result-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  cursor: pointer;
  border-bottom: 1px solid var(--border-color);
  transition: background 0.2s;
}

.search-result-item:hover {
  background: var(--hover-bg);
}

.result-name {
  font-weight: 500;
  color: var(--text-primary);
}

.result-email {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.result-type {
  font-size: 0.8rem;
  padding: 2px 6px;
  border-radius: 12px;
  background: var(--bg-page);
}

.selected-customer {
  margin-top: 16px;
  padding: 12px;
  background: rgba(66, 185, 131, 0.1);
  border-radius: 12px;
  border: 1px solid var(--accent-color);
}

.customer-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.customer-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--accent-color);
  display: flex;
  align-items: center;
  justify-content: center;
}

.customer-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  font-weight: bold;
  color: white;
}

.avatar-placeholder.small {
  width: 32px;
  height: 32px;
  font-size: 0.8rem;
}

.customer-details {
  flex: 1;
}

.customer-name {
  font-weight: 600;
  color: var(--text-primary);
}

.customer-email {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.customer-type {
  font-size: 0.8rem;
  padding: 2px 6px;
  background: var(--bg-page);
  border-radius: 12px;
  display: inline-block;
  margin-top: 4px;
}

.remove-customer, .remove-participant {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: var(--danger-color);
  padding: 4px 8px;
  border-radius: 50%;
}

.remove-customer:hover, .remove-participant:hover {
  background: var(--danger-bg);
}

/* Participants */
.participants-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.participant-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px;
  background: var(--bg-page);
  border-radius: 8px;
  gap: 12px;
  flex-wrap: wrap;
}

.participant-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.participant-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--accent-color);
  display: flex;
  align-items: center;
  justify-content: center;
}

.participant-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.participant-details {
  display: flex;
  flex-direction: column;
}

.participant-name {
  font-weight: 500;
  color: var(--text-primary);
}

.participant-email {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.participant-role-selector select {
  width: 140px;
  padding: 6px 8px;
}

.add-participant-section {
  margin-top: 8px;
}

.add-participant-input {
  display: flex;
  gap: 8px;
}

.add-participant-input input {
  flex: 1;
}

.toggle-search-btn {
  padding: 8px 16px;
  background: var(--accent-color);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.add-btn {
  background: var(--accent-color);
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 1.2rem;
}

.no-participants {
  text-align: center;
  color: var(--text-secondary);
  font-style: italic;
  padding: 20px;
}

/* Required roles table */
.required-roles-table {
  width: 100%;
}

.role-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
  padding: 10px 8px;
  border-bottom: 1px solid var(--border-color);
  align-items: center;
}

.header-row {
  font-weight: 600;
  background: var(--bg-page);
  border-radius: 8px;
}

.target-input {
  width: 100px;
  padding: 6px 8px;
}

/* Tasks */
.tasks-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.add-task-button {
  background: var(--accent-color);
  color: white;
  border: none;
  border-radius: 20px;
  padding: 8px 16px;
  cursor: pointer;
}

.no-tasks {
  text-align: center;
  color: var(--text-secondary);
  padding: 20px;
  background: var(--bg-page);
  border-radius: 12px;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-item {
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background: var(--bg-card);
}

.task-compact {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
}

.task-title {
  font-weight: 500;
}

.delete-task-button {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: var(--danger-color);
}

.task-form {
  padding: 16px;
  border-top: 1px solid var(--border-color);
}

.task-form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.close-task-form {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
}

.task-form-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.save-task-button, .cancel-task-button {
  flex: 1;
  padding: 8px;
  border-radius: 20px;
  cursor: pointer;
}

.save-task-button {
  background: var(--accent-color);
  color: white;
  border: none;
}

.cancel-task-button {
  background: var(--bg-page);
  border: 1px solid var(--border-color);
}

/* Form actions */
.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 32px;
}

.save-button, .cancel-button {
  flex: 1;
  padding: 12px;
  border-radius: 30px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.save-button {
  background: var(--accent-color);
  color: white;
  border: none;
}

.save-button:hover:not(:disabled) {
  background: var(--accent-hover);
}

.save-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.cancel-button {
  background: var(--bg-page);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
}

.error-message {
  color: var(--danger-color);
  font-size: 0.85rem;
  margin-top: 8px;
}

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
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
  
  .admin-project-creator {
    margin-top: 0;
  }
  
  .participant-item {
    flex-direction: column;
    align-items: stretch;
  }
  
  .participant-role-selector select {
    width: 100%;
  }
}
</style>
