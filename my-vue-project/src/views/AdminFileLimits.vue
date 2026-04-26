<template>
  <div class="file-limits-page">
    <header class="page-header">
      <h1>{{ $t('adminPanel.fileLimits.title') }}</h1>
      <div class="header-actions">
        <ThemeToggle />
        <LanguageSwitcher />
        <HomeButton />
      </div>
    </header>

    <div class="limits-container">
      <p class="hint">{{ $t('adminPanel.fileLimits.hint') }}</p>
      <div v-for="(info, mime) in limits" :key="mime" class="limit-row">
        <label :for="'limit-' + mime" class="limit-label">
          {{ getTypeName(mime) }} ({{ mime }})
        </label>
        <div class="input-wrapper">
          <input
            :id="'limit-' + mime"
            v-model.number="limits[mime]"
            type="number"
            min="0.1"
            step="0.1"
            class="size-input"
          />
          <span class="unit">МБ</span>
        </div>
      </div>
      <div class="actions">
        <button class="save-btn" @click="saveLimits" :disabled="saving">
          {{ saving ? $t('common.saving') : $t('common.save') }}
        </button>
        <span v-if="message" class="message" :class="{ error: isError }">{{ message }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { useI18n } from 'vue-i18n';
import ThemeToggle from '@/components/ThemeToggle.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';
import HomeButton from '@/components/HomeButton.vue';

const { t } = useI18n();

// Человеческие названия типов
const typeNames: Record<string, string> = {
  'text/plain': 'Текстовый файл (.txt)',
  'application/pdf': 'PDF (.pdf)',
  'application/msword': 'Документ Word (.doc)',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'Документ Word (.docx)',
  'application/vnd.ms-powerpoint': 'Презентация PowerPoint (.ppt)',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'Презентация PowerPoint (.pptx)',
  'image/png': 'Изображение PNG',
  'image/jpeg': 'Изображение JPEG',
  'image/x-icon': 'Иконка (.ico)',
  'image/vnd.microsoft.icon': 'Иконка (.ico) alt',
  'audio/mpeg': 'Аудио MP3',
  'video/mp4': 'Видео MP4',
};

const limits = ref<Record<string, number>>({});
const saving = ref(false);
const message = ref('');
const isError = ref(false);

function getTypeName(mime: string): string {
  return typeNames[mime] || mime;
}

async function fetchLimits() {
  try {
    const { data } = await axios.get('/admin/file-size-limits');
    // Преобразуем байты в мегабайты для отображения
    const mbValues: Record<string, number> = {};
    for (const [mime, bytes] of Object.entries(data)) {
      mbValues[mime] = Math.round((bytes as number) / (1024 * 1024) * 10) / 10; // 1 десятичный знак
    }
    limits.value = mbValues;
  } catch (e) {
    console.error(e);
    showMessage(t('adminPanel.fileLimits.loadError'), true);
  }
}

async function saveLimits() {
  saving.value = true;
  message.value = '';
  isError.value = false;
  try {
    // Конвертируем МБ обратно в байты
    const bytesPayload: Record<string, number> = {};
    for (const [mime, mb] of Object.entries(limits.value)) {
      bytesPayload[mime] = Math.round(mb * 1024 * 1024);
    }
    await axios.put('/admin/file-size-limits', bytesPayload);
    showMessage(t('adminPanel.fileLimits.saveSuccess'), false);
  } catch (e) {
    console.error(e);
    showMessage(t('adminPanel.fileLimits.saveError'), true);
  } finally {
    saving.value = false;
  }
}

function showMessage(msg: string, error: boolean) {
  message.value = msg;
  isError.value = error;
  setTimeout(() => { message.value = ''; }, 3000);
}

onMounted(fetchLimits);
</script>

<style scoped>
.file-limits-page {
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
.limits-container {
  max-width: 600px;
  margin: 0 auto;
  background: var(--bg-card);
  padding: 24px;
  border-radius: 16px;
  box-shadow: var(--shadow);
}
.hint {
  color: var(--text-secondary);
  margin-bottom: 20px;
}
.limit-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-color);
}
.limit-label {
  flex: 1;
  font-weight: 500;
  color: var(--text-primary);
}
.input-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}
.size-input {
  width: 80px;
  padding: 6px 10px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-primary);
  text-align: right;
}
.unit {
  color: var(--text-secondary);
  font-size: 0.9rem;
}
.actions {
  margin-top: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}
.save-btn {
  background: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 24px;
  padding: 10px 24px;
  font-size: 1rem;
  cursor: pointer;
}
.save-btn:hover:not(:disabled) {
  background: var(--accent-hover);
}
.message {
  font-size: 0.95rem;
}
.message.error {
  color: var(--danger-color);
}
.message:not(.error) {
  color: var(--accent-color);
}
</style>