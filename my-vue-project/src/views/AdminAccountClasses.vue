<template>
  <div class="page">
    <header>
      <h1>{{ $t('accountClasses.title') }}</h1>
      <div class="header-actions">
        <ThemeToggle />
        <LanguageSwitcher />
        <HomeButton />
      </div>
    </header>

    <main v-if="settings">
      <!-- Раздел 1: Разрешенные классы -->
      <section class="section-allowed">
        <div class="section-header">
          <h2>{{ $t('accountClasses.allowedClasses') }}</h2>
          <div class="header-controls">
            <div class="counters">
              <span class="counter selected">{{ selectedCount }}</span>
              <span class="counter-separator">/</span>
              <span class="counter total">{{ classOptions.length }}</span>
            </div>
            <button class="btn-save-classes" @click="saveSettings" :disabled="saving">
              {{ $t('common.save') }}
            </button>
          </div>
        </div>
        <div class="classes-grid">
          <label v-for="value in classOptions" :key="value" class="class-item">
            <input v-model="settings.allowed_classes" type="checkbox" :value="value" />
            <span>{{ value.toFixed(1) }}</span>
          </label>
        </div>
      </section>

      <!-- Раздел 2: Ролловер -->
      <section class="section-rollover">
        <div class="section-header">
          <h2>{{ $t('accountClasses.rollover') }}</h2>
        </div>
        
        <div class="rollover-block">
          <label class="toggle-switch">
            <input v-model="settings.annual_rollover_enabled" type="checkbox" />
            <span>{{ $t('accountClasses.rolloverEnabled') }}</span>
          </label>
          
          <div class="date-fields">
            <div class="field">
              <label>{{ $t('accountClasses.month') }}</label>
              <input v-model.number="settings.rollover_month" type="number" min="1" max="12" />
            </div>
            <div class="field">
              <label>{{ $t('accountClasses.day') }}</label>
              <input v-model.number="settings.rollover_day" type="number" min="1" max="31" />
            </div>
          </div>
          
          <div class="last-run">
            <span class="label">{{ $t('accountClasses.lastRun') }}:</span>
            <span class="value">{{ settings.last_rollover_year || $t('common.notSpecified') }}</span>
          </div>
          
          <div class="button-group">
            <button class="btn-save" @click="saveSettings" :disabled="saving">{{ $t('common.save') }}</button>
            <button class="btn-run" @click="runRollover">{{ $t('accountClasses.runNow') }}</button>
          </div>
        </div>
      </section>

      <!-- Раздел 3: Заявки -->
      <section class="section-requests">
        <div class="section-header">
          <h2>{{ $t('accountClasses.requests') }}</h2>
          <span v-if="pendingRequests.length" class="count-badge pending">{{ pendingRequests.length }}</span>
        </div>
        
        <div v-if="pendingRequests.length === 0" class="empty-requests">
          {{ $t('accountClasses.noRequests') }}
        </div>
        
        <div v-else class="requests-list">
          <div v-for="request in pendingRequests" :key="request.id" class="request-item">
            <div class="request-user">
              <strong>{{ request.user_name }}</strong>
              <small>{{ formatDate(request.created_at) }}</small>
            </div>
            <div class="request-controls">
              <select v-model.number="request.selectedClass" class="class-select">
                <option :value="null" disabled>{{ $t('accountClasses.selectClass') }}</option>
                <option v-for="value in settings.allowed_classes" :key="value" :value="value">
                  {{ Number(value).toFixed(1) }}
                </option>
              </select>
              <button class="btn-approve" @click="decide(request, 'approved')">
                {{ $t('accountClasses.approve') }}
              </button>
              <button class="btn-reject" @click="decide(request, 'rejected')">
                {{ $t('accountClasses.reject') }}
              </button>
            </div>
          </div>
        </div>
      </section>
    </main>
    
    <div v-else class="loading">
      {{ $t('common.loading') }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import api from '@/utils/api';
import ThemeToggle from '@/components/ThemeToggle.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';
import HomeButton from '@/components/HomeButton.vue';

const { t } = useI18n();
const settings = ref<any>(null);
const saving = ref(false);
const classOptions = Array.from({ length: 54 }, (_, index) => Number((3.1 + Math.floor(index / 6) + (index % 6) / 10).toFixed(1)));

// Каунтер выбранных классов
const selectedCount = computed(() => settings.value?.allowed_classes?.length || 0);

const pendingRequests = computed(() =>
  (settings.value?.restoration_requests || [])
    .filter((request: any) => request.status === 'pending')
    .map((request: any) => ({ ...request, selectedClass: request.selectedClass ?? null }))
);

const load = async () => {
  settings.value = (await api.get('/admin/account-class-settings')).data;
};

const saveSettings = async () => {
  saving.value = true;
  try {
    await api.put('/admin/account-class-settings', settings.value);
    alert(t('accountClasses.saved'));
    await load();
  } finally {
    saving.value = false;
  }
};

const runRollover = async () => {
  const result = (await api.post('/admin/account-class-settings/run-rollover')).data;
  alert(t('accountClasses.runResult', result));
  await load();
};

const decide = async (request: any, decision: string) => {
  await api.put(`/admin/account-restoration-requests/${request.id}`, {
    decision,
    class_value: decision === 'approved' ? request.selectedClass : null,
  });
  await load();
};

const formatDate = (value: string) => new Date(value).toLocaleString();
onMounted(load);
</script>

<style scoped>
* {
  box-sizing: border-box;
}

.page {
  min-height: 100vh;
  padding: 24px 20px;
  background: var(--bg-page);
  color: var(--text-primary);
}

header {
  max-width: 1200px;
  margin: 0 auto 32px auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

header h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

main {
  max-width: 1200px;
  margin: 0 auto;
}

/* СЕКЦИИ — КАЖДАЯ ОТДЕЛЬНО, НЕ СЛИВАЮТСЯ */
section {
  background: var(--bg-card);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 32px;
  border: 1px solid var(--border-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

section:last-child {
  margin-bottom: 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid var(--border-color);
}

.section-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* Стили для каунтеров */
.counters {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 15px;
  font-weight: 600;
  background: var(--bg-page);
  padding: 4px 12px;
  border-radius: 20px;
  border: 1px solid var(--border-color);
}

.counter {
  font-size: 15px;
  font-weight: 600;
}

.counter.selected {
  color: var(--accent-color);
}

.counter.total {
  color: var(--text-secondary);
}

.counter-separator {
  color: var(--text-secondary);
  font-weight: 500;
}

.count-badge {
  background: var(--accent-color);
  color: white;
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
}

.count-badge.pending {
  background: #ef4444;
}

/* Кнопка сохранения в секции классов */
.btn-save-classes {
  padding: 6px 16px;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
  background: var(--accent-color);
  color: var(--button-text);
}

.btn-save-classes:hover:not(:disabled) {
  filter: brightness(1.05);
  transform: translateY(-1px);
}

.btn-save-classes:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Сетка классов — с прокруткой, не вылезает */
.classes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(85px, 1fr));
  gap: 10px;
  max-height: 260px;
  overflow-y: auto;
  padding: 4px 2px;
}

.class-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-page);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.class-item:hover {
  background: var(--accent-color);
  border-color: var(--accent-color);
}

.class-item input {
  margin: 0;
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.class-item span {
  font-size: 14px;
  font-weight: 500;
}

/* Блок ролловера */
.rollover-block {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.toggle-switch {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 8px 0;
}

.toggle-switch input {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.date-fields {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.field input {
  padding: 10px 12px;
  background: var(--input-bg);
  color: var(--text-primary);
  border: 1px solid var(--input-border);
  border-radius: 10px;
  width: 100px;
  font-size: 14px;
}

.last-run {
  display: flex;
  gap: 12px;
  padding: 10px 0;
  font-size: 14px;
  border-top: 1px dashed var(--border-color);
  border-bottom: 1px dashed var(--border-color);
}

.last-run .label {
  font-weight: 600;
  color: var(--text-secondary);
}

.last-run .value {
  color: var(--text-primary);
}

.button-group {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.btn-save, .btn-run, .btn-approve, .btn-reject {
  padding: 10px 20px;
  border: none;
  border-radius: 10px;
  font-weight: 500;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-save {
  background: var(--accent-color);
  color: var(--button-text);
}

.btn-save:hover:not(:disabled) {
  filter: brightness(1.05);
  transform: translateY(-1px);
}

.btn-save:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-run {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.btn-run:hover {
  background: var(--bg-page);
  transform: translateY(-1px);
}

.btn-approve {
  background: #10b981;
  color: white;
}

.btn-approve:hover:not(:disabled) {
  background: #059669;
}

.btn-approve:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-reject {
  background: #ef4444;
  color: white;
}

.btn-reject:hover {
  background: #dc2626;
}

/* Заявки — отдельные карточки */
.requests-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.request-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  padding: 16px;
  background: var(--bg-page);
  border-radius: 14px;
  border: 1px solid var(--border-color);
  transition: all 0.2s;
}

.request-item:hover {
  border-color: var(--accent-color);
}

.request-user {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 160px;
}

.request-user strong {
  font-size: 15px;
}

.request-user small {
  font-size: 12px;
  color: var(--text-secondary);
}

.request-controls {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}

.class-select {
  padding: 8px 12px;
  background: var(--input-bg);
  color: var(--text-primary);
  border: 1px solid var(--input-border);
  border-radius: 10px;
  cursor: pointer;
  min-width: 140px;
  font-size: 14px;
}

.empty-requests {
  text-align: center;
  padding: 48px 20px;
  color: var(--text-secondary);
  font-size: 15px;
  background: var(--bg-page);
  border-radius: 14px;
}

.loading {
  text-align: center;
  padding: 60px 20px;
  font-size: 16px;
  color: var(--text-secondary);
}

/* Скролл для сетки классов */
.classes-grid::-webkit-scrollbar {
  width: 6px;
}

.classes-grid::-webkit-scrollbar-track {
  background: var(--bg-page);
  border-radius: 3px;
}

.classes-grid::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

/* Адаптив */
@media (max-width: 700px) {
  .page {
    padding: 16px;
  }
  
  section {
    padding: 18px;
    margin-bottom: 24px;
  }
  
  .request-item {
    flex-direction: column;
    align-items: stretch;
  }
  
  .request-controls {
    justify-content: stretch;
  }
  
  .request-controls select,
  .request-controls button {
    flex: 1;
  }
  
  .classes-grid {
    grid-template-columns: repeat(auto-fill, minmax(75px, 1fr));
  }
  
  .date-fields {
    flex-direction: column;
    gap: 12px;
  }
  
  .field input {
    width: 100%;
  }
  
  .header-controls {
    gap: 12px;
  }
  
  .btn-save-classes {
    padding: 4px 12px;
    font-size: 12px;
  }
  
  .counters {
    font-size: 13px;
    padding: 3px 10px;
  }
  
  .counter {
    font-size: 13px;
  }
}

@media (max-width: 480px) {
  header {
    flex-direction: column;
    text-align: center;
  }
  
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .header-controls {
    width: 100%;
    justify-content: space-between;
  }
}
</style>