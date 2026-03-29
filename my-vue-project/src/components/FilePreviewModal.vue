<template>
  <Teleport to="body">
    <div v-if="show" class="file-preview-overlay" @click.self="close">
      <div class="file-preview-modal">
        <div class="modal-header">
          <h3>{{ file?.original_filename || $t('filePreview.title') }}</h3>
          <button class="close-btn" @click="close">✕</button>
        </div>
        <div class="modal-body">
          <div v-if="loadingPreview" class="preview-loading">
            {{ $t('common.loading') }}
          </div>
          <!-- Изображения -->
          <div v-else-if="isImage" class="image-container">
            <img :src="imageBlobUrl" :alt="file?.original_filename" />
          </div>
          <!-- Текстовые файлы -->
          <div v-else-if="isText" class="text-container">
            <pre>{{ textContent }}</pre>
          </div>
          <!-- PDF через встроенный просмотрщик браузера -->
          <div v-else-if="isPdf" class="pdf-container">
            <embed v-if="pdfBlobUrl" :src="pdfBlobUrl" type="application/pdf" width="100%" height="100%" />
          </div>
          <!-- Офисные документы через Google Docs Viewer (только для публичных URL) -->
          <div v-else-if="isOfficeDocument && isPublicUrl" class="office-container">
            <iframe :src="googleDocsUrl" frameborder="0" class="office-viewer"></iframe>
          </div>
          <!-- Остальные файлы -->
          <div v-else class="fallback-message">
            <p>{{ $t('filePreview.previewNotAvailable') }}</p>
            <button class="download-link" @click="downloadFile" :disabled="downloading">
              {{ $t('filePreview.downloadFile') }}
            </button>
          </div>
        </div>
        <div class="modal-footer">
          <button class="download-button" @click="downloadFile" :disabled="downloading">
            {{ downloading ? $t('common.sending') : $t('common.download') }}
          </button>
          <button class="close-button" @click="close">{{ $t('common.close') }}</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue';
import { useI18n } from 'vue-i18n';
import axios from 'axios';

const { t } = useI18n();

const props = defineProps<{
  show: boolean;
  file: any;
  baseUrl: string;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const downloading = ref(false);
const loadingPreview = ref(false);
const imageBlobUrl = ref<string>(); // string | undefined
const textContent = ref('');
const pdfBlobUrl = ref<string>(); // Blob URL для PDF

const fileUrl = computed(() => `${props.baseUrl}/files/${props.file.id}`);

const isImage = computed(() => props.file?.mime_type?.startsWith('image/'));
const isText = computed(() => props.file?.mime_type === 'text/plain');
const isPdf = computed(() => props.file?.mime_type === 'application/pdf');
const isOfficeDocument = computed(() => {
  const type = props.file?.mime_type;
  return (
    type === 'application/msword' ||
    type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
    type === 'application/vnd.ms-powerpoint' ||
    type === 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
  );
});

const isPublicUrl = computed(() => {
  const host = window.location.hostname;
  return !(host === 'localhost' || host === '127.0.0.1');
});

const googleDocsUrl = computed(() => {
  return `https://docs.google.com/viewer?url=${encodeURIComponent(fileUrl.value)}&embedded=true`;
});

const loadImage = async () => {
  if (!props.file || !isImage.value) return;
  loadingPreview.value = true;
  try {
    const token = localStorage.getItem('access_token');
    const response = await axios.get(fileUrl.value, {
      responseType: 'blob',
      headers: { Authorization: `Bearer ${token}` }
    });
    const url = URL.createObjectURL(response.data);
    imageBlobUrl.value = url;
  } catch (error) {
    console.error('Failed to load image:', error);
    alert(t('fileUploader.previewError') || 'Ошибка загрузки изображения');
  } finally {
    loadingPreview.value = false;
  }
};

const loadText = async () => {
  if (!props.file || !isText.value) return;
  loadingPreview.value = true;
  try {
    const token = localStorage.getItem('access_token');
    const response = await axios.get(fileUrl.value, {
      responseType: 'text',
      headers: { Authorization: `Bearer ${token}` }
    });
    textContent.value = response.data;
  } catch (error) {
    console.error('Failed to load text file:', error);
    alert(t('fileUploader.previewError') || 'Ошибка загрузки текстового файла');
  } finally {
    loadingPreview.value = false;
  }
};

const loadPdf = async () => {
  if (!props.file || !isPdf.value) return;
  loadingPreview.value = true;
  try {
    const token = localStorage.getItem('access_token');
    const response = await axios.get(fileUrl.value, {
      responseType: 'blob',
      headers: { Authorization: `Bearer ${token}` }
    });
    const blob = new Blob([response.data], { type: 'application/pdf' });
    const url = URL.createObjectURL(blob);
    pdfBlobUrl.value = url;
  } catch (error) {
    console.error('Failed to load PDF:', error);
    alert(t('fileUploader.previewError') || 'Ошибка загрузки PDF');
  } finally {
    loadingPreview.value = false;
  }
};

const downloadFile = async () => {
  downloading.value = true;
  try {
    const token = localStorage.getItem('access_token');
    const response = await axios.get(fileUrl.value, {
      responseType: 'blob',
      headers: { Authorization: `Bearer ${token}` }
    });
    const blob = new Blob([response.data]);
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = props.file.original_filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
  } catch (error) {
    console.error('Download error:', error);
    alert(t('fileUploader.downloadError') || 'Ошибка скачивания');
  } finally {
    downloading.value = false;
  }
};

const close = () => {
  if (imageBlobUrl.value) {
    URL.revokeObjectURL(imageBlobUrl.value);
    imageBlobUrl.value = undefined;
  }
  if (pdfBlobUrl.value) {
    URL.revokeObjectURL(pdfBlobUrl.value);
    pdfBlobUrl.value = undefined;
  }
  emit('close');
};

watch(
  () => props.show,
  (newVal) => {
    if (newVal) {
      if (isImage.value) loadImage();
      else if (isText.value) loadText();
      else if (isPdf.value) loadPdf();
    } else {
      if (imageBlobUrl.value) {
        URL.revokeObjectURL(imageBlobUrl.value);
        imageBlobUrl.value = undefined;
      }
      if (pdfBlobUrl.value) {
        URL.revokeObjectURL(pdfBlobUrl.value);
        pdfBlobUrl.value = undefined;
      }
    }
  }
);

onUnmounted(() => {
  if (imageBlobUrl.value) URL.revokeObjectURL(imageBlobUrl.value);
  if (pdfBlobUrl.value) URL.revokeObjectURL(pdfBlobUrl.value);
});
</script>

<style scoped>
/* ... существующие стили ... */

/* Расширяем модальное окно для PDF */
.file-preview-modal:has(.pdf-container) {
  width: 90vw;
  max-width: none;
  height: 90vh;
  max-height: none;
}

/* Контейнер PDF занимает всё доступное пространство */
.pdf-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  width: 100%;
  height: 100%;
  min-height: 70vh;
}

/* Если нужен встроенный просмотрщик через embed, то увеличиваем его размеры */
.pdf-container embed {
  width: 100%;
  height: 100%;
  min-height: 70vh;
  border: none;
  border-radius: 8px;
}

/* Также увеличиваем контейнер для офисных документов, если нужно */
.office-container {
  width: 100%;
  height: 100%;
  min-height: 70vh;
}
.office-viewer {
  width: 100%;
  height: 100%;
  border: none;
  border-radius: 8px;
}

/* Убираем лишние отступы в теле модального окна для PDF/Office */
.modal-body:has(.pdf-container),
.modal-body:has(.office-container) {
  padding: 0;
}

/* Остальные стили без изменений */
</style>


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

.preview-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 300px;
  color: var(--text-secondary);
}

.image-container img {
  max-width: 100%;
  max-height: 70vh;
  object-fit: contain;
  border-radius: 8px;
}

.text-container {
  width: 100%;
  max-height: 70vh;
  overflow: auto;
  background: var(--bg-page);
  padding: 16px;
  border-radius: 8px;
}
.text-container pre {
  margin: 0;
  white-space: pre-wrap;
  font-family: monospace;
  font-size: 0.9rem;
  color: var(--text-primary);
}

.pdf-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  width: 100%;
  height: 70vh;
}
.pdf-canvas {
  max-width: 100%;
  height: auto;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: var(--shadow);
}
.pdf-controls {
  display: flex;
  gap: 12px;
  align-items: center;
}
.pdf-controls button {
  background: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 30px;
  padding: 6px 12px;
  cursor: pointer;
  transition: background 0.2s;
}
.pdf-controls button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.pdf-controls button:hover:not(:disabled) {
  background: var(--accent-hover);
}

.office-container {
  width: 100%;
  height: 70vh;
}
.office-viewer {
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
  cursor: pointer;
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
  cursor: pointer;
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