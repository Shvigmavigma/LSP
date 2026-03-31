<template>
  <div class="admin-emails-page">
    <header class="page-header">
      <h1>{{ $t('adminEmails.title') }}</h1>
      <div class="header-actions">
        <ThemeToggle />
        <LanguageSwitcher />
        <button class="home-button" @click="goHome" :title="$t('common.home')">🏠</button>
        <button class="back-button" @click="goBack" :title="$t('common.back')">◀</button>
      </div>
    </header>

    <div class="email-tabs">
      <button
        class="tab-button"
        :class="{ active: activeTab === 'teachers' }"
        @click="activeTab = 'teachers'"
      >
        👨‍🏫 {{ $t('adminEmails.tabs.teachers') }}
      </button>
      <button
        class="tab-button"
        :class="{ active: activeTab === 'students' }"
        @click="activeTab = 'students'"
      >
        👨‍🎓 {{ $t('adminEmails.tabs.students') }}
      </button>
    </div>

    <div v-if="loading" class="loading">{{ $t('common.loading') }}</div>
    <div v-else class="edit-card">
      <!-- Информационная подсказка -->
      <div class="info-hint" :class="activeTab === 'students' ? 'students-hint' : 'teachers-hint'">
        <span class="hint-icon">ℹ️</span>
        <span class="hint-text">
          <template v-if="activeTab === 'students'">
            {{ $t('adminEmails.hint.students.part1') }}
            <strong>lit1533.ru</strong>.
            {{ $t('adminEmails.hint.students.part2') }}
          </template>
          <template v-else>
            {{ $t('adminEmails.hint.teachers') }}
          </template>
        </span>
      </div>

      <!-- Раздел email -->
      <div class="form-section">
        <div class="section-header">
          <h3>{{ $t('adminEmails.allowedEmails') }}</h3>
          <button class="add-button" @click="openAddEmailModal">
            + {{ $t('adminEmails.addEmail') }}
          </button>
        </div>

        <div v-if="emailsList.length === 0" class="empty-list">
          {{ $t('adminEmails.noEmails') }}
        </div>
        <div v-else class="items-list">
          <div v-for="email in emailsList" :key="email" class="list-item">
            <span class="item-text">{{ email }}</span>
            <button class="remove-item" @click="removeEmail(email)" :title="$t('common.delete')">✕</button>
          </div>
        </div>
        <div class="hint">{{ $t('adminEmails.emailHint') }}</div>
      </div>

      <!-- Раздел доменов (только для учеников) -->
      <div v-if="activeTab === 'students'" class="form-section">
        <div class="section-header">
          <h3>🌐 {{ $t('adminEmails.allowedDomains') }}</h3>
          <button class="add-button" @click="openAddDomainModal">
            + {{ $t('adminEmails.addDomain') }}
          </button>
        </div>

        <div class="domain-note">
          <span class="domain-icon">🏫</span>
          <span>
            {{ $t('adminEmails.defaultDomainNote') }}
            <strong>lit1533.ru</strong>
          </span>
        </div>

        <div v-if="domainsList.length === 0" class="empty-list">
          {{ $t('adminEmails.noDomains') }}
        </div>
        <div v-else class="items-list">
          <div v-for="domain in domainsList" :key="domain" class="list-item">
            <span class="item-text">{{ domain }}</span>
            <button class="remove-item" @click="removeDomain(domain)" :title="$t('common.delete')">✕</button>
          </div>
        </div>
        <div class="hint">{{ $t('adminEmails.domainHint') }}</div>
      </div>

      <!-- Кнопки сохранения -->
      <div class="form-actions">
        <button class="save-button" @click="saveData" :disabled="saving">
          {{ saving ? $t('common.saving') : $t('adminEmails.saveChanges') }}
        </button>
        <button class="cancel-button" @click="loadData">
          ↺ {{ $t('common.cancelChanges') }}
        </button>
      </div>

      <div v-if="saveMessage" class="save-message" :class="{ success: saveSuccess, error: !saveSuccess }">
        {{ saveMessage }}
      </div>
    </div>

    <!-- Модальное окно добавления email -->
    <Teleport to="body">
      <div v-if="showAddEmailModal" class="modal-overlay" @click.self="closeAddEmailModal">
        <div class="modal-content">
          <h3>{{ $t('adminEmails.addEmailModalTitle') }}</h3>
          <input
            v-model="newEmail"
            type="email"
            :placeholder="$t('adminEmails.emailPlaceholder')"
            class="modal-input"
            @keyup.enter="addEmail"
          />
          <div class="modal-actions">
            <button class="modal-confirm" @click="addEmail" :disabled="!newEmail.trim()">
              {{ $t('common.add') }}
            </button>
            <button class="modal-cancel" @click="closeAddEmailModal">
              {{ $t('common.cancel') }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Модальное окно добавления домена (только для учеников) -->
    <Teleport to="body">
      <div v-if="showAddDomainModal" class="modal-overlay" @click.self="closeAddDomainModal">
        <div class="modal-content">
          <h3>{{ $t('adminEmails.addDomainModalTitle') }}</h3>
          <input
            v-model="newDomain"
            type="text"
            :placeholder="$t('adminEmails.domainPlaceholder')"
            class="modal-input"
            @keyup.enter="addDomain"
          />
          <div class="modal-actions">
            <button class="modal-confirm" @click="addDomain" :disabled="!newDomain.trim()">
              {{ $t('common.add') }}
            </button>
            <button class="modal-cancel" @click="closeAddDomainModal">
              {{ $t('common.cancel') }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import ThemeToggle from '@/components/ThemeToggle.vue';
import axios from 'axios';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';
const { t } = useI18n();
const router = useRouter();

const activeTab = ref<'teachers' | 'students'>('teachers');
const loading = ref(true);
const saving = ref(false);
const saveMessage = ref('');
const saveSuccess = ref(false);

// Данные
const emailsList = ref<string[]>([]);
const domainsList = ref<string[]>([]);

// Модальные окна
const showAddEmailModal = ref(false);
const showAddDomainModal = ref(false);
const newEmail = ref('');
const newDomain = ref('');

const loadData = async () => {
  loading.value = true;
  try {
    const endpoint = activeTab.value === 'teachers'
      ? '/admin/accepted-emails/teachers'
      : '/admin/accepted-emails/students';
    const response = await axios.get(endpoint);
    const data = response.data;
    emailsList.value = data.accepted_emails || [];
    domainsList.value = data.domains || [];
    saveMessage.value = '';
  } catch (error) {
    console.error('Failed to load data', error);
    saveMessage.value = t('adminEmails.loadError');
    saveSuccess.value = false;
  } finally {
    loading.value = false;
  }
};

const saveData = async () => {
  saving.value = true;
  saveMessage.value = '';

  const payload = {
    accepted_emails: emailsList.value,
    domains: domainsList.value
  };

  try {
    const endpoint = activeTab.value === 'teachers'
      ? '/admin/accepted-emails/teachers'
      : '/admin/accepted-emails/students';
    await axios.put(endpoint, payload);
    saveMessage.value = t('adminEmails.saveSuccess');
    saveSuccess.value = true;
    setTimeout(() => {
      saveMessage.value = '';
    }, 3000);
  } catch (error) {
    console.error('Failed to save data', error);
    saveMessage.value = t('adminEmails.saveError');
    saveSuccess.value = false;
  } finally {
    saving.value = false;
  }
};

// Управление email
const openAddEmailModal = () => {
  newEmail.value = '';
  showAddEmailModal.value = true;
};

const closeAddEmailModal = () => {
  showAddEmailModal.value = false;
  newEmail.value = '';
};

const addEmail = () => {
  if (!newEmail.value.trim()) return;
  const email = newEmail.value.trim().toLowerCase();
  if (!emailsList.value.includes(email)) {
    emailsList.value.push(email);
  }
  closeAddEmailModal();
};

const removeEmail = (email: string) => {
  emailsList.value = emailsList.value.filter(e => e !== email);
};

// Управление доменами (только для учеников)
const openAddDomainModal = () => {
  newDomain.value = '';
  showAddDomainModal.value = true;
};

const closeAddDomainModal = () => {
  showAddDomainModal.value = false;
  newDomain.value = '';
};

const addDomain = () => {
  if (!newDomain.value.trim()) return;
  const domain = newDomain.value.trim().toLowerCase();
  if (!domainsList.value.includes(domain)) {
    domainsList.value.push(domain);
  }
  closeAddDomainModal();
};

const removeDomain = (domain: string) => {
  domainsList.value = domainsList.value.filter(d => d !== domain);
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
.home-button:hover, .back-button:hover {
  background: rgba(255, 255, 255, 0.1);
}
.email-tabs {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-bottom: 30px;
}
.tab-button {
  padding: 12px 32px;
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
.edit-card {
  max-width: 800px;
  margin: 0 auto;
  background: var(--bg-card);
  border-radius: 24px;
  padding: 30px;
  box-shadow: var(--shadow-strong);
}
.info-hint {
  margin-bottom: 30px;
  padding: 16px 20px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(33, 150, 243, 0.1);
  border-left: 4px solid #2196f3;
}
.students-hint {
  background: rgba(76, 175, 80, 0.1);
  border-left-color: #4caf50;
}
.teachers-hint {
  background: rgba(255, 152, 0, 0.1);
  border-left-color: #ff9800;
}
.hint-icon {
  font-size: 1.5rem;
}
.hint-text {
  flex: 1;
  color: var(--text-primary);
  line-height: 1.5;
}
.hint-text strong {
  color: var(--accent-color);
}
.form-section {
  margin-bottom: 30px;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}
.section-header h3 {
  color: var(--heading-color);
  margin: 0;
  font-weight: 500;
  font-size: 1.2rem;
}
.add-button {
  background: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 30px;
  padding: 6px 16px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.add-button:hover {
  background: var(--accent-hover);
}
.empty-list {
  text-align: center;
  padding: 20px;
  background: var(--bg-page);
  border-radius: 12px;
  color: var(--text-secondary);
  font-style: italic;
  border: 1px dashed var(--border-color);
}
.items-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 10px;
}
.list-item {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--bg-page);
  padding: 8px 12px;
  border-radius: 30px;
  border: 1px solid var(--border-color);
}
.item-text {
  color: var(--text-primary);
  font-family: monospace;
  font-size: 0.9rem;
}
.remove-item {
  background: none;
  border: none;
  color: var(--danger-color);
  cursor: pointer;
  font-size: 1.1rem;
  padding: 0 4px;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}
.remove-item:hover {
  background: rgba(244, 67, 54, 0.1);
}
.domain-note {
  background: rgba(66, 185, 131, 0.1);
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-primary);
  font-size: 0.9rem;
}
.domain-icon {
  font-size: 1.2rem;
}
.hint {
  margin-top: 8px;
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
  box-shadow: var(--shadow-strong);
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
/* Модальные окна */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(5px);
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
.modal-content h3 {
  color: var(--heading-color);
  margin-bottom: 20px;
  font-weight: 500;
  text-align: center;
}
.modal-input {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-primary);
  font-size: 1rem;
  margin-bottom: 20px;
  outline: none;
}
.modal-input:focus {
  border-color: var(--accent-color);
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.2);
}
.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}
.modal-confirm, .modal-cancel {
  padding: 10px 24px;
  border: none;
  border-radius: 30px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.modal-confirm {
  background: var(--accent-color);
  color: var(--button-text);
}
.modal-confirm:hover:not(:disabled) {
  background: var(--accent-hover);
}
.modal-confirm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.modal-cancel {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}
.modal-cancel:hover {
  background: var(--bg-page);
}
</style>