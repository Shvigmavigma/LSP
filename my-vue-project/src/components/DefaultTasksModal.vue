<template>
  <Teleport to="body">
    <div v-if="show" class="modal-overlay" @click.self="close">
      <div class="modal-content">
        <h3>{{ $t('defaultTasksModal.title') }}</h3>
        
        <div class="form-group readonly-field">
          <label>{{ $t('defaultTasksModal.autoClass') }}</label>
          <div class="readonly-value">{{ currentClassLabel }}</div>
        </div>

        <div class="form-group readonly-field">
          <label>{{ $t('defaultTasksModal.autoStage') }}</label>
          <div class="readonly-value">{{ stageLabel }}</div>
        </div>

        <div class="form-group" v-if="hasDirections">
          <label>{{ $t('defaultTasksModal.selectDirection') }}</label>
          <select v-model="selectedDirection">
            <option v-for="(dir, key) in currentDirections" :key="key" :value="key">
              {{ dir.label }}
            </option>
          </select>
        </div>

        <div class="preview-tasks">
          <h4>{{ $t('defaultTasksModal.preview') }}</h4>
          <div v-if="loading" class="loading">{{ $t('common.loading') }}</div>
          <div v-else-if="previewTasks.length === 0" class="no-tasks">
            {{ emptyMessage }}
          </div>
          <div v-else class="tasks-preview-list">
            <div v-for="(task, idx) in previewTasks" :key="idx" class="preview-task-item">
              <strong>{{ task.title }}</strong>
              <p>{{ task.body }}</p>
              <div v-if="task.required_files?.length" class="preview-files">
                <small>{{ $t('defaultTasksModal.requiredFiles') }}:</small>
                <span v-for="rf in task.required_files" :key="rf.name">{{ rf.name }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-actions">
          <button class="add-btn" @click="addTasks" :disabled="previewTasks.length === 0">
            {{ $t('defaultTasksModal.add') }}
          </button>
          <button class="cancel-btn" @click="close">{{ $t('common.cancel') }}</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';

import { v4 as uuidv4 } from 'uuid';
import api from '@/utils/api';

const { t } = useI18n();

const props = defineProps<{
  show: boolean;
  classKey?: string | null;
  directionKey?: string | null;
  stageId?: string | null;
  stageTitle?: string | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'add', tasks: any[]): void;
}>();

const templates = ref<any>({});
const loading = ref(false);
const selectedDirection = ref<string>('');

const selectedClass = computed(() => props.classKey || '');
const stageId = computed(() => props.stageId || '');
const stageLabel = computed(() => props.stageTitle || stageId.value || t('common.notSelected'));

const hasDirections = computed(() => {
  const cls = templates.value[selectedClass.value];
  return cls && cls.directions && Object.keys(cls.directions).length > 0;
});

const currentClassLabel = computed(() => {
  const cls = templates.value[selectedClass.value];
  if (!selectedClass.value) return t('common.notSelected');
  return cls?.label || selectedClass.value;
});

const currentDirections = computed(() => {
  const cls = templates.value[selectedClass.value];
  return cls?.directions || {};
});

const previewTasks = computed(() => {
  const cls = templates.value[selectedClass.value];
  if (!cls) return [];
  if (!stageId.value) return [];
  if (hasDirections.value && selectedDirection.value) {
    const dir = cls.directions?.[selectedDirection.value];
    return dir?.stage_tasks?.[stageId.value] || [];
  } else if (cls.stage_tasks) {
    return cls.stage_tasks?.[stageId.value] || [];
  }
  return [];
});

const emptyMessage = computed(() => {
  if (!selectedClass.value) return t('defaultTasksModal.noClass');
  if (!stageId.value) return t('defaultTasksModal.noStage');
  if (!templates.value[selectedClass.value]) return t('defaultTasksModal.noClassTemplates');
  if (hasDirections.value && !selectedDirection.value) return t('defaultTasksModal.noDirection');
  return t('defaultTasksModal.noStageTasks');
});

const loadTemplates = async () => {
  loading.value = true;
  try {
    const response = await api.get('/default-tasks');
    templates.value = response.data;
    syncDirection();
  } catch (error) {
    console.error('Failed to load default tasks templates', error);
  } finally {
    loading.value = false;
  }
};

watch(() => props.show, (val) => {
  if (val) {
    loadTemplates();
  }
});

watch(() => props.classKey, () => {
  syncDirection();
});

watch(() => props.directionKey, () => {
  syncDirection();
});

function syncDirection() {
  if (hasDirections.value) {
    const dirKeys = Object.keys(currentDirections.value);
    const preferredDirection = props.directionKey || selectedDirection.value;
    if (preferredDirection && dirKeys.includes(preferredDirection)) {
      selectedDirection.value = preferredDirection;
    } else if (!dirKeys.includes(selectedDirection.value)) {
      selectedDirection.value = dirKeys[0] || '';
    }
  } else {
    selectedDirection.value = '';
  }
}

function addTasks() {
  if (previewTasks.value.length === 0) return;
  const tasksToAdd = previewTasks.value.map((task: any) => ({
    ...task,
    id: undefined,
    expanded: false,
    required_files: (task.required_files || []).map((rf: any) => ({
      id: uuidv4(),
      name: rf.name,
      description: rf.description || ''
    }))
  }));
  emit('add', tasksToAdd);
  close();
}

function close() {
  emit('close');
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.7);
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
  max-width: 550px;
  width: 90%;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: var(--shadow-strong);
}
.modal-content h3 {
  color: var(--heading-color);
  margin-bottom: 20px;
}
.form-group {
  margin-bottom: 15px;
}
.form-group label {
  display: block;
  margin-bottom: 6px;
  color: var(--text-secondary);
}
.readonly-value {
  width: 100%;
  box-sizing: border-box;
  padding: 10px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-card);
  color: var(--text-primary);
  font-weight: 600;
}
select {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-primary);
}
.preview-tasks {
  margin: 20px 0;
  max-height: 350px;
  overflow-y: auto;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 10px;
}
.preview-tasks h4 {
  margin-top: 0;
  margin-bottom: 10px;
  color: var(--heading-color);
}
.tasks-preview-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.preview-task-item {
  padding: 10px;
  background: var(--bg-page);
  border-radius: 8px;
  border-left: 3px solid var(--accent-color);
}
.preview-task-item strong {
  color: var(--heading-color);
}
.preview-task-item p {
  margin: 5px 0 0;
  font-size: 0.85rem;
  color: var(--text-secondary);
}
.preview-files {
  margin-top: 6px;
  font-size: 0.75rem;
  color: var(--text-secondary);
}
.preview-files small {
  font-weight: 500;
  margin-right: 6px;
}
.preview-files span {
  display: inline-block;
  background: var(--bg-card);
  padding: 2px 8px;
  border-radius: 12px;
  margin-right: 6px;
  margin-top: 4px;
}
.no-tasks {
  text-align: center;
  color: var(--text-secondary);
  padding: 20px;
  font-style: italic;
}
.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 20px;
}
.add-btn, .cancel-btn {
  padding: 10px 24px;
  border: none;
  border-radius: 30px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
}
.add-btn {
  background: var(--accent-color);
  color: var(--button-text);
}
.add-btn:hover:not(:disabled) {
  background: var(--accent-hover);
}
.add-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.cancel-btn {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}
.cancel-btn:hover {
  background: var(--bg-page);
}
.loading {
  text-align: center;
  padding: 20px;
  color: var(--text-secondary);
}
</style>
