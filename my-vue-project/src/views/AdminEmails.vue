<template>
  <div class="admin-emails-page">
    <header class="page-header">
      <h1>Управление разрешёнными email</h1>
      <div class="header-actions">
        <ThemeToggle />
        <button class="home-button" @click="goHome" title="На главную">🏠</button>
        <button class="back-button" @click="goBack" title="Назад">◀</button>
      </div>
    </header>

    <div class="email-tabs">
      <button class="tab-button" :class="{ active: activeTab === 'teachers' }" @click="activeTab = 'teachers'">
        Учителя
      </button>
      <button class="tab-button" :class="{ active: activeTab === 'students' }" @click="activeTab = 'students'">
        Ученики
      </button>
    </div>

    <div v-if="loading" class="loading">Загрузка...</div>
    <div v-else class="edit-card">
      <div class="form-section">
        <h3>Разрешённые email (по одному на строку)</h3>
        <textarea
          v-model="emailsText"
          rows="6"
          placeholder="user@example.com&#10;another@domain.com"
          class="emails-textarea"
        ></textarea>
        <div class="hint">Email в этом списке разрешены для регистрации.</div>
      </div>

      <div class="form-section">
        <h3>Разрешённые домены (по одному на строку)</h3>
        <textarea
          v-model="domainsText"
          rows="3"
          placeholder="example.com&#10;school.ru"
          class="emails-textarea"
        ></textarea>
        <div class="hint">Любой email с этими доменами разрешён.</div>
      </div>

      <div class="form-actions">
        <button class="save-button" @click="saveData" :disabled="saving">
          {{ saving ? 'Сохранение...' : 'Сохранить изменения' }}
        </button>
        <button class="cancel-button" @click="loadData">Отменить изменения</button>
      </div>

      <div v-if="saveMessage" class="save-message" :class="{ success: saveSuccess, error: !saveSuccess }">
        {{ saveMessage }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import ThemeToggle from '@/components/ThemeToggle.vue';
import axios from 'axios';

const router = useRouter();
const activeTab = ref<'teachers' | 'students'>('teachers');
const loading = ref(true);
const saving = ref(false);
const saveMessage = ref('');
const saveSuccess = ref(false);

const emailsText = ref('');
const domainsText = ref('');

const loadData = async () => {
  loading.value = true;
  try {
    const endpoint = activeTab.value === 'teachers'
      ? '/admin/accepted-emails/teachers'
      : '/admin/accepted-emails/students';
    const response = await axios.get(endpoint);
    const data = response.data;
    emailsText.value = (data.accepted_emails || []).join('\n');
    domainsText.value = (data.domains || []).join('\n');
    saveMessage.value = '';
  } catch (error) {
    console.error('Failed to load data', error);
    saveMessage.value = 'Ошибка загрузки данных';
    saveSuccess.value = false;
  } finally {
    loading.value = false;
  }
};

const saveData = async () => {
  saving.value = true;
  saveMessage.value = '';
  const accepted_emails = emailsText.value.split('\n')
    .map(email => email.trim())
    .filter(email => email !== '');
  const domains = domainsText.value.split('\n')
    .map(domain => domain.trim())
    .filter(domain => domain !== '');
  const payload = { accepted_emails, domains };

  try {
    const endpoint = activeTab.value === 'teachers'
      ? '/admin/accepted-emails/teachers'
      : '/admin/accepted-emails/students';
    await axios.put(endpoint, payload);
    saveMessage.value = 'Изменения сохранены';
    saveSuccess.value = true;
    setTimeout(() => {
      saveMessage.value = '';
    }, 3000);
  } catch (error) {
    console.error('Failed to save data', error);
    saveMessage.value = 'Ошибка сохранения';
    saveSuccess.value = false;
  } finally {
    saving.value = false;
  }
};

watch(activeTab, () => {
  loadData();
});

onMounted(() => {
  loadData();
});

function goHome() {
  router.push('/main');
}
function goBack() {
  router.push('/admin');
}
</script>

<style scoped>
.admin-emails-page {
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
.page-header h1 {
  color: var(--heading-color);
  font-size: 2rem;
  margin: 0;
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
.email-tabs {
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
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(66, 185, 131, 0.2);
}
.edit-card {
  max-width: 800px;
  margin: 0 auto;
  background: var(--bg-card);
  border-radius: 24px;
  padding: 30px;
  box-shadow: var(--shadow-strong);
}
.form-section {
  margin-bottom: 30px;
}
.form-section h3 {
  color: var(--heading-color);
  margin-bottom: 10px;
  font-weight: 500;
}
.emails-textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-primary);
  font-family: monospace;
  font-size: 0.9rem;
  resize: vertical;
}
.hint {
  margin-top: 6px;
  font-size: 0.85rem;
  color: var(--text-secondary);
}
.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 30px;
}
.save-button, .cancel-button {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 30px;
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
.save-message {
  margin-top: 15px;
  padding: 10px;
  border-radius: 8px;
  text-align: center;
}
.save-message.success {
  background: rgba(76, 175, 80, 0.1);
  color: #4caf50;
  border: 1px solid #4caf50;
}
.save-message.error {
  background: rgba(244, 67, 54, 0.1);
  color: #f44336;
  border: 1px solid #f44336;
}
.loading {
  text-align: center;
  color: var(--text-primary);
  padding: 40px;
}
</style>