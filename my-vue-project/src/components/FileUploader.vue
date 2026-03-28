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
        <button class="delete-file" @click="deleteFile(file.id)" :title="$t('common.delete')">
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { useI18n } from 'vue-i18n';
import FilePreviewModal from './FilePreviewModal.vue';

const { t } = useI18n();
const baseUrl = 'http://localhost:8000';

const props = defineProps<{
  projectId: number;
  taskIndex?: number;
}>();

const emit = defineEmits(['upload', 'delete']);

const files = ref<any[]>([]);
const uploading = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);
const showPreview = ref(false);
const selectedFile = ref<any>(null);

const acceptedTypes = [
  'text/plain',
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-powerpoint',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
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

const uploadFile = async (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (!input.files?.length) return;
  const file = input.files[0];
  const formData = new FormData();
  formData.append('file', file);
  if (props.taskIndex !== undefined) {
    formData.append('task_id', String(props.taskIndex));
  }
  uploading.value = true;
  try {
    await axios.post(`/projects/${props.projectId}/files`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
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

const deleteFile = async (fileId: number) => {
  if (confirm(t('fileUploader.confirmDelete'))) {
    try {
      await axios.delete(`/files/${fileId}`);
      await fetchFiles();
      emit('delete');
    } catch (err: any) {
      console.error(err);
      alert(err.response?.data?.detail || t('fileUploader.deleteError'));
    }
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
}
.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  overflow: hidden;
}
.file-icon {
  font-size: 1.2rem;
  min-width: 24px;
}
.file-name {
  font-size: 0.9rem;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.file-size {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-left: auto;
  white-space: nowrap;
}
.file-actions {
  display: flex;
  gap: 8px;
}
.open-file, .delete-file {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  padding: 4px;
  border-radius: 4px;
  transition: background 0.2s;
}
.open-file {
  color: var(--accent-color);
}
.open-file:hover {
  background: rgba(66, 185, 131, 0.2);
}
.delete-file {
  color: var(--danger-color);
}
.delete-file:hover {
  background: var(--danger-bg);
}
</style>