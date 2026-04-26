<template>
  <Teleport to="body">
    <div v-if="show" class="file-preview-overlay" @click.self="close">
      <div class="file-preview-modal" :class="{ 'wide-modal': isPdf || isVideo }">
        <div class="modal-header">
          <h3>{{ file?.original_filename || $t('filePreview.title') }}</h3>
          <button class="close-btn" @click="close">✕</button>
        </div>
        <div class="modal-body">
          <div v-if="loadingPreview" class="preview-loading">
            {{ $t('common.loading') }}
          </div>
          <!-- Изображения (включая .ico) -->
          <div v-else-if="isImage" class="image-container">
            <img :src="imageBlobUrl" :alt="file?.original_filename" />
          </div>
          <!-- Текстовые файлы -->
          <div v-else-if="isText" class="text-container">
            <pre>{{ textContent }}</pre>
          </div>
          <!-- PDF через iframe -->
          <div v-else-if="isPdf" class="pdf-container">
            <iframe
              v-if="pdfBlobUrl"
              :src="pdfBlobUrl"
              frameborder="0"
              class="pdf-viewer"
              @error="handlePdfError"
            ></iframe>
            <div v-else class="fallback-message">
              <p>{{ $t('filePreview.previewNotAvailable') }}</p>
              <button class="download-link" @click="downloadFile">{{ $t('filePreview.downloadFile') }}</button>
            </div>
          </div>
          <!-- Аудио (mp3) - прямая ссылка с токеном -->
          <div v-else-if="isAudio" class="audio-container">
            <audio v-if="audioStreamUrl" :src="audioStreamUrl" controls class="audio-player">
              {{ $t('filePreview.audioNotSupported') }}
            </audio>
            <div v-else class="fallback-message">
              <p>{{ $t('filePreview.previewNotAvailable') }}</p>
              <button class="download-link" @click="downloadFile">{{ $t('filePreview.downloadFile') }}</button>
            </div>
          </div>
          <!-- Видео (mp4) - прямая ссылка с токеном, стриминг -->
          <div v-else-if="isVideo" class="video-container">
            <video v-if="videoStreamUrl" :src="videoStreamUrl" controls class="video-player">
              {{ $t('filePreview.videoNotSupported') }}
            </video>
            <div v-else class="fallback-message">
              <p>{{ $t('filePreview.previewNotAvailable') }}</p>
              <button class="download-link" @click="downloadFile">{{ $t('filePreview.downloadFile') }}</button>
            </div>
          </div>
          <!-- Офисные документы (только Word, без презентаций) через Google Docs Viewer -->
          <div v-else-if="isOfficeDocument && isPublicUrl" class="office-container">
            <iframe :src="googleDocsUrl" frameborder="0" class="office-viewer"></iframe>
          </div>
          <!-- Все остальные файлы (включая презентации, неизвестные типы) -->
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
const imageBlobUrl = ref<string>();
const textContent = ref('');
const pdfBlobUrl = ref<string>();

// Базовый URL для файла
const fileBaseUrl = computed(() => `${props.baseUrl}/files/${props.file?.id}`);

// Добавляем токен в query-параметр для мультимедиа
const streamToken = computed(() => {
  const token = localStorage.getItem('access_token');
  return token ? `?token=${encodeURIComponent(token)}` : '';
});

const audioStreamUrl = computed(() => isAudio.value ? `${fileBaseUrl.value}${streamToken.value}` : '');
const videoStreamUrl = computed(() => isVideo.value ? `${fileBaseUrl.value}${streamToken.value}` : '');

const fileUrl = computed(() => fileBaseUrl.value); // для скачивания и Google Docs

const isImage = computed(() => props.file?.mime_type?.startsWith('image/'));
const isText = computed(() => props.file?.mime_type === 'text/plain');
const isPdf = computed(() => props.file?.mime_type === 'application/pdf');
const isAudio = computed(() => props.file?.mime_type === 'audio/mpeg');
const isVideo = computed(() => props.file?.mime_type === 'video/mp4');
const isOfficeDocument = computed(() => {
  const type = props.file?.mime_type;
  return (
    type === 'application/msword' ||
    type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  );
});

const isPublicUrl = computed(() => {
  const host = window.location.hostname;
  return !(host === 'localhost' || host === '127.0.0.1');
});

const googleDocsUrl = computed(() => {
  return `https://docs.google.com/viewer?url=${encodeURIComponent(fileUrl.value)}&embedded=true`;
});

// Загрузка изображения через blob (остаётся как раньше)
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

// Текстовый файл (blob)
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

// PDF через blob
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

const handlePdfError = () => {
  console.warn('PDF preview failed, falling back to download');
  pdfBlobUrl.value = undefined;
  alert(t('filePreview.previewNotAvailable') || 'Невозможно отобразить PDF. Попробуйте скачать файл.');
};

// Скачивание файла (полная загрузка)
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

// Загружаем контент при открытии, очищаем при закрытии
watch(
  () => props.show,
  (newVal) => {
    if (newVal) {
      if (isImage.value) loadImage();
      else if (isText.value) loadText();
      else if (isPdf.value) loadPdf();
      // Аудио и видео не требуют предзагрузки – просто прямая ссылка
    } else {
      // Очистка blob-ов
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
/* Общие стили */
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

.file-preview-modal.wide-modal {
  width: 90vw;
  max-width: none;
  height: 90vh;
  max-height: none;
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

/* Для широких контейнеров убираем отступы */
.modal-body:has(.pdf-container),
.modal-body:has(.office-container),
.modal-body:has(.video-container) {
  padding: 0;
}

.preview-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 300px;
  color: var(--text-secondary);
}

/* Изображения */
.image-container img {
  max-width: 100%;
  max-height: 70vh;
  object-fit: contain;
  border-radius: 8px;
}

/* Текстовые файлы */
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

/* PDF */
.pdf-container {
  width: 100%;
  height: 100%;
  min-height: 70vh;
}
.pdf-viewer {
  width: 100%;
  height: 100%;
  border: none;
  border-radius: 8px;
}

/* Аудио */
.audio-container {
  width: 100%;
  max-width: 500px;
  margin: 0 auto;
  padding: 20px;
}
.audio-player {
  width: 100%;
  outline: none;
}

/* Видео */
.video-container {
  width: 100%;
  height: 100%;
  min-height: 70vh;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.video-player {
  width: 100%;
  height: 100%;
  border: none;
  border-radius: 8px;
}

/* Офисные документы (Word) */
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

/* Запасной блок */
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