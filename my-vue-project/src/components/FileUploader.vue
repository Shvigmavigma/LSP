<template>
  <div class="file-uploader">
    <div class="upload-area">
      <input
        type="file"
        ref="fileInput"
        @change="uploadFile"
        :accept="acceptedTypes"
        style="display: none"
      />
      <button class="upload-btn" @click="triggerFileInput" :disabled="uploading">
        {{ uploading ? $t('common.sending') : $t('fileUploader.selectFile') }}
      </button>
    </div>
    <div v-if="files.length" class="file-list">
      <div v-for="file in files" :key="file.id" class="file-item">
        <a
          href="#"
          class="file-link"
          @click.prevent="openPreview(file)"
        >
          {{ file.original_filename }}
        </a>
        <span class="file-size">{{ formatSize(file.file_size) }}</span>
        <button class="delete-file" @click="confirmDelete(file)" :title="$t('common.delete')">
          🗑
        </button>
      </div>
    </div>

    <FilePreviewModal
      :show="showPreview"
      :file="selectedFile"
      :base-url="baseUrl"
      @close="closePreview"
    />

    <ConfirmModal
      :show="showDeleteModal"
      :title="$t('fileUploader.deleteConfirmTitle')"
      :message="$t('fileUploader.deleteConfirmMessage')"
      :confirm-text="$t('common.delete')"
      :cancel-text="$t('common.cancel')"
      icon="🗑️"
      @confirm="deleteFileConfirmed"
      @close="closeDeleteModal"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { useI18n } from 'vue-i18n';
import FilePreviewModal from './FilePreviewModal.vue';
import ConfirmModal from './ConfirmModal.vue';

const { t } = useI18n();
const baseUrl = 'http://localhost:8000';

const props = defineProps<{
  projectId: number;
  taskIndex?: number;
}>();

const emit = defineEmits<{
  (e: 'upload'): void;
  (e: 'delete'): void;
}>();

const files = ref<any[]>([]);
const uploading = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);
const showPreview = ref(false);
const selectedFile = ref<any>(null);
const showDeleteModal = ref(false);
const fileToDelete = ref<any>(null);

// Расширенный список типов файлов
const acceptedTypes = [
  'text/plain',
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-powerpoint',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  'image/png',
  'image/jpeg',
  'image/x-icon',
  'image/vnd.microsoft.icon',
  'audio/mpeg',
  'video/mp4',
].join(',');

const fetchFiles = async () => {
  try {
    const url = props.taskIndex !== undefined
      ? `/projects/${props.projectId}/files?task_id=${props.taskIndex}`
      : `/projects/${props.projectId}/files`;
    const res = await axios.get(url);
    files.value = res.data;
  } catch (err) {
    console.error('Failed to fetch files', err);
  }
};

const triggerFileInput = () => {
  fileInput.value?.click();
};

// Сжатие изображений на клиенте (оставим для уменьшения трафика)
const compressImage = async (file: File): Promise<File> => {
  return new Promise((resolve, reject) => {
    if (!file.type.startsWith('image/')) {
      resolve(file);
      return;
    }

    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = (event) => {
      const result = event.target?.result;
      if (typeof result !== 'string') {
        reject(new Error('Failed to read image'));
        return;
      }
      const img = new Image();
      img.src = result;
      img.onload = () => {
        const canvas = document.createElement('canvas');
        let width = img.width;
        let height = img.height;
        const maxDimension = 1200;
        if (width > maxDimension || height > maxDimension) {
          if (width > height) {
            height = (height * maxDimension) / width;
            width = maxDimension;
          } else {
            width = (width * maxDimension) / height;
            height = maxDimension;
          }
        }
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        ctx?.drawImage(img, 0, 0, width, height);
        canvas.toBlob(
          (blob) => {
            if (!blob) {
              reject(new Error('Compression failed'));
              return;
            }
            const compressedFile = new File([blob], file.name, {
              type: 'image/jpeg',
              lastModified: Date.now(),
            });
            resolve(compressedFile);
          },
          'image/jpeg',
          0.8
        );
      };
      img.onerror = () => reject(new Error('Image loading failed'));
    };
    reader.onerror = () => reject(new Error('File reading failed'));
  });
};

const uploadFile = async (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (!input.files?.length) return;
  let file = input.files[0];

  if (file.type.startsWith('image/')) {
    try {
      file = await compressImage(file);
    } catch (err) {
      console.warn('Compression failed, uploading original:', err);
    }
  }

  const formData = new FormData();
  formData.append('file', file);
  if (props.taskIndex !== undefined) {
    formData.append('task_id', String(props.taskIndex));
  }
  uploading.value = true;
  try {
    // ❗️ УБРАН headers: { 'Content-Type': ... }
    await axios.post(`/projects/${props.projectId}/files`, formData);
    await fetchFiles();
    emit('upload');
  } catch (err: any) {
    console.error(err);
    alert(err.response?.data?.detail || t('fileUploader.uploadError'));
  } finally {
    uploading.value = false;
    input.value = '';
  }
};

const confirmDelete = (file: any) => {
  fileToDelete.value = file;
  showDeleteModal.value = true;
};

const closeDeleteModal = () => {
  showDeleteModal.value = false;
  fileToDelete.value = null;
};

const deleteFileConfirmed = async () => {
  if (!fileToDelete.value) return;
  try {
    await axios.delete(`/files/${fileToDelete.value.id}`);
    await fetchFiles();
    emit('delete');
  } catch (err: any) {
    console.error(err);
    alert(err.response?.data?.detail || t('fileUploader.deleteError'));
  } finally {
    closeDeleteModal();
  }
};

const openPreview = (file: any) => {
  selectedFile.value = file;
  showPreview.value = true;
};

const closePreview = () => {
  showPreview.value = false;
  selectedFile.value = null;
};

const formatSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
};

onMounted(fetchFiles);
</script>

<style scoped>
/* ... все стили без изменений ... */
.file-uploader {
  margin-top: 12px;
}
.upload-area {
  margin-bottom: 12px;
}
.upload-btn {
  background: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 30px;
  padding: 6px 16px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.2s;
}
.upload-btn:hover:not(:disabled) {
  background: var(--accent-hover);
}
.upload-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.file-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
}
.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg-page);
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  gap: 12px;
}
.file-link {
  color: var(--link-color);
  text-decoration: none;
  font-size: 0.9rem;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
}
.file-link:hover {
  text-decoration: underline;
}
.file-size {
  font-size: 0.8rem;
  color: var(--text-secondary);
  white-space: nowrap;
}
.delete-file {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  padding: 4px;
  border-radius: 4px;
  transition: background 0.2s;
  color: var(--danger-color);
}
.delete-file:hover {
  background: var(--danger-bg);
}
</style>