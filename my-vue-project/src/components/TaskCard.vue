<template>
  <div class="task-node" :class="[taskStatusClass(task), { readonly: isReadonly }]" @click="!isReadonly && $emit('click')">
    <span class="task-icon">📄</span>
    <div class="task-content">
      <strong>{{ task.title }}</strong>
      <span class="task-status">{{ getTaskStatusText(task.status) }}</span>
      <p>{{ task.body }}</p>
      
      <!-- Требуемые файлы -->
      <div v-if="task.required_files && task.required_files.length" class="task-required-files">
        <div class="required-files-label">{{ $t('taskDetails.requiredFilesLabel') }}:</div>
        <div class="required-files-list">
          <div 
            v-for="req in task.required_files" 
            :key="req.id" 
            class="required-file-item" 
            :class="{ satisfied: isTaskRequiredFileAttached(task, req.id) }"
          >
            {{ req.name }}
          </div>
        </div>
      </div>
      
      <!-- Прогресс -->
      <span v-if="task.status === 'в работе'" class="task-progress">
        {{ $t('projectDetails.progress') }}: {{ task.progress ?? 0 }}%
      </span>
      
      <!-- Дедлайн -->
      <small>{{ $t('projectDetails.deadline') }}: {{ formatTaskDates(task) }}</small>
      
      <!-- Бейджи статуса -->
      <span v-if="isTaskOverdue(task)" class="overdue-badge">{{ $t('projectDetails.overdue') }}</span>
      <span v-if="isTaskInvalid(task)" class="invalid-badge">{{ $t('projectDetails.invalidDates') }}</span>
      <span v-if="isTaskNotStarted(task)" class="not-started-badge">{{ $t('projectDetails.notStarted') }}</span>
      
      <!-- Назначенный исполнитель -->
      <span v-if="task.assigned_to" class="assigned-info">
        {{ $t('projectDetails.assignee') }}: {{ getUserDisplayNameById(task.assigned_to) }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Task } from '@/types';
import { useI18n } from 'vue-i18n';
import { parseDate } from '@/utils/dateUtils';

const { t } = useI18n();

const props = defineProps<{
  task: Task;
  isReadonly?: boolean;
  getUserDisplayNameById: (id: number) => string;
}>();

defineEmits<{
  (e: 'click'): void;
}>();

function formatTaskDates(task: Task): string {
  if (task.timelinend) return `${task.timeline || '?'} – ${task.timelinend}`;
  if (task.timeline?.includes('-')) {
    const parts = task.timeline.split('-');
    return `${parts[0]} – ${parts[1]}`;
  }
  return task.timeline || '?';
}

function isTaskOverdue(task: Task): boolean {
  const today = new Date(); 
  today.setHours(0, 0, 0, 0);
  
  let endStr = task.timelinend;
  if (!endStr && task.timeline?.includes('-')) {
    const parts = task.timeline.split('-');
    endStr = parts[1];
  }
  
  const endDate = parseDate(endStr || '');
  if (!endDate) return false;
  
  return today > endDate && task.status !== 'выполнена';
}

function isTaskInvalid(task: Task): boolean {
  let startStr = task.timeline, endStr = task.timelinend;
  if (!endStr && startStr?.includes('-')) {
    const parts = startStr.split('-');
    startStr = parts[0];
    endStr = parts[1];
  }
  
  const start = parseDate(startStr || '');
  const end = parseDate(endStr || '');
  
  if (!start || !end) return true;
  return start > end;
}

function isTaskNotStarted(task: Task): boolean {
  if (isTaskInvalid(task) || isTaskOverdue(task)) return false;
  
  let startStr = task.timeline;
  if (!task.timelinend && startStr?.includes('-')) {
    startStr = startStr.split('-')[0];
  }
  
  const start = parseDate(startStr || '');
  if (!start) return false;
  
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  return today < start;
}

function taskStatusClass(task: Task): string {
  if (isTaskInvalid(task)) return 'task-invalid';
  if (isTaskOverdue(task)) return 'task-overdue';
  if (isTaskNotStarted(task)) return 'task-not-started';
  return '';
}

function getTaskStatusText(status: string): string {
  switch (status) {
    case 'в работе': return t('projectDetails.status.inProgress');
    case 'ожидает': return t('projectDetails.status.waiting');
    case 'выполнена': return t('projectDetails.status.completed');
    default: return status;
  }
}

function isTaskRequiredFileAttached(task: Task, requiredFileId: string): boolean {
  return task.attachments?.some(att => att.required_file_id === requiredFileId) ?? false;
}
</script>

<style scoped>
.task-node {
  display: flex;
  align-items: flex-start;
  gap: 15px;
  padding: 15px;
  background: var(--bg-card);
  border-radius: 12px;
  box-shadow: var(--shadow);
  cursor: pointer;
  transition: all 0.2s;
  border-left: 4px solid var(--accent-color);
}

.task-node:hover {
  transform: translateX(5px);
  box-shadow: var(--shadow-strong);
}

.task-node.readonly {
  cursor: default;
  opacity: 0.8;
}

.task-node.readonly:hover {
  transform: none;
  box-shadow: var(--shadow);
}

.task-node.task-overdue {
  background-color: var(--overdue-bg);
  border-left-color: #f44336;
}

.task-node.task-invalid {
  background-color: var(--invalid-bg);
  border-left-color: #9e9e9e;
  opacity: 0.7;
}

.task-node.task-not-started {
  background-color: var(--not-started-bg);
  border-left-color: #bdbdbd;
  opacity: 0.8;
}

.task-icon {
  font-size: 1.5rem;
  color: var(--accent-color);
}

.task-content {
  flex: 1;
}

.task-content strong {
  color: var(--heading-color);
  display: block;
  margin-bottom: 4px;
}

.task-status {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-left: 8px;
}

.task-content p {
  color: var(--text-primary);
  margin: 8px 0 4px;
}

.task-required-files {
  margin-top: 8px;
  font-size: 0.8rem;
}

.required-files-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.required-files-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.required-file-item {
  font-size: 0.75rem;
  color: #888;
  background: var(--bg-page);
  padding: 2px 8px;
  border-radius: 12px;
  display: inline-block;
}

.required-file-item.satisfied {
  color: #4caf50;
  background: rgba(76, 175, 80, 0.1);
  font-weight: 500;
}

.task-progress {
  display: inline-block;
  margin-top: 4px;
  margin-right: 8px;
  font-size: 0.9rem;
  color: var(--heading-color);
  background: var(--completed-bg);
  padding: 2px 8px;
  border-radius: 12px;
}

.task-content small {
  color: var(--text-secondary);
  display: inline-block;
  margin-right: 8px;
}

.overdue-badge,
.invalid-badge,
.not-started-badge {
  display: inline-block;
  margin-left: 8px;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: bold;
  color: white;
}

.overdue-badge {
  background-color: #f44336;
}

.invalid-badge {
  background-color: #9e9e9e;
}

.not-started-badge {
  background-color: #757575;
}

.assigned-info {
  display: inline-block;
  margin-left: 8px;
  font-size: 0.8rem;
  color: var(--text-secondary);
  background: var(--bg-card);
  padding: 2px 8px;
  border-radius: 12px;
}
</style>