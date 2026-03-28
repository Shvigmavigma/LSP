<template>
  <Teleport to="body">
    <div v-if="show" class="file-preview-overlay" @click.self="close">
      <div class="file-preview-modal">
        <div class="modal-header">
          <h3>{{ file?.original_filename || $t('filePreview.title') }}</h3>
          <button class="close-btn" @click="close">✕</button>
        </div>
        <div class="modal-body">
          <!-- Изображения -->
          <div v-if="isImage" class="image-container">
            <img :src="fileUrl" :alt="file?.original_filename" />
          </div>
          <!-- PDF -->
          <div v-else-if="isPdf" class="pdf-container">
            <iframe :src="fileUrl" frameborder="0" class="pdf-viewer"></iframe>
          </div>
          <!-- Остальные файлы -->
          <div v-else class="fallback-message">
            <p>{{ $t('filePreview.previewNotAvailable') }}</p>
            <a :href="fileUrl" download class="download-link">
              {{ $t('filePreview.downloadFile') }}
            </a>
          </div>
        </div>
        <div class="modal-footer">
          <a :href="fileUrl" download class="download-button">
            {{ $t('common.download') }}
          </a>
          <button class="close-button" @click="close">{{ $t('common.close') }}</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const props = defineProps<{
  show: boolean;
  file: any; // объект файла (с полями id, original_filename, mime_type)
  baseUrl: string;
}>();

const emit = defineEmits(['close']);

const fileUrl = computed(() => `${props.baseUrl}/files/${props.file.id}`);

const isImage = computed(() => props.file?.mime_type?.startsWith('image/'));
const isPdf = computed(() => props.file?.mime_type === 'application/pdf');

const close = () => {
  emit('close');
};
</script>

<style scoped>
.file-preview-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(5px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 3000;
  animation: fadeIn 0.2s ease;
}

.file-preview-modal {
  background: var(--bg-card);
  border-radius: 16px;
  max-width: 90vw;
  max-height: 90vh;
  width: auto;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-strong);
  animation: scaleIn 0.2s ease;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 500;
  color: var(--heading-color);
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--text-secondary);
  padding: 4px;
  line-height: 1;
}
.close-btn:hover {
  color: var(--danger-color);
}

.modal-body {
  flex: 1;
  overflow: auto;
  padding: 20px;
  text-align: center;
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-container img {
  max-width: 100%;
  max-height: 70vh;
  object-fit: contain;
  border-radius: 8px;
}

.pdf-container {
  width: 100%;
  height: 70vh;
}

.pdf-viewer {
  width: 100%;
  height: 100%;
  border: none;
  border-radius: 8px;
}

.fallback-message {
  text-align: center;
  color: var(--text-secondary);
}
.fallback-message p {
  margin-bottom: 16px;
}
.download-link {
  color: var(--accent-color);
  text-decoration: underline;
  cursor: pointer;
}
.download-link:hover {
  color: var(--accent-hover);
}

.modal-footer {
  padding: 12px 20px;
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
.download-button {
  background: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 30px;
  padding: 8px 20px;
  font-size: 0.9rem;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: background 0.2s;
}
.download-button:hover {
  background: var(--accent-hover);
}
.close-button {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  border-radius: 30px;
  padding: 8px 20px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}
.close-button:hover {
  background: var(--bg-page);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes scaleIn {
  from { transform: scale(0.95); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
</style>