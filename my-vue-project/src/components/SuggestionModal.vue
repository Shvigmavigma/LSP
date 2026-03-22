<!-- src/components/SuggestionModal.vue (если требуется доработка для корректной отправки) -->
<template>
  <Teleport to="body">
    <div v-if="show" class="modal-overlay" @click.self="close">
      <div class="modal-content">
        <h3>Создать предложение</h3>
        <form @submit.prevent="submit">
          <div class="form-group">
            <label>Что хотите изменить?</label>
            <select v-model="targetType">
              <option value="project">Проект (название, описание, доп. информация)</option>
              <option value="task">Задачу</option>
              <option value="link">Ссылку</option>
            </select>
          </div>

          <div v-if="targetType === 'task'" class="form-group">
            <label>Выберите задачу</label>
            <select v-model="targetId">
              <option v-for="(task, idx) in tasks" :key="idx" :value="String(idx)">
                {{ task.title }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>Предлагаемые изменения (JSON)</label>
            <textarea
              v-model="changes"
              rows="6"
              placeholder='{"title": "Новое название", "body": "Новое описание"}'
            ></textarea>
            <div v-if="jsonError" class="error-message">{{ jsonError }}</div>
          </div>

          <div class="modal-actions">
            <button type="submit" class="submit-btn">Отправить</button>
            <button type="button" class="cancel-btn" @click="close">Отмена</button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import type { Task } from '@/types';

const props = defineProps<{
  show: boolean;
  tasks: Task[];
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'submit', data: { target_type: string; target_id?: string; changes: Record<string, any> }): void;
}>();

const targetType = ref('project');
const targetId = ref<string | undefined>();
const changes = ref('');
const jsonError = ref('');

watch(() => props.show, (val) => {
  if (val) {
    targetType.value = 'project';
    targetId.value = undefined;
    changes.value = '';
    jsonError.value = '';
  }
});

function submit() {
  try {
    const parsed = JSON.parse(changes.value);
    emit('submit', {
      target_type: targetType.value,
      target_id: targetId.value,
      changes: parsed,
    });
    close();
  } catch (e) {
    jsonError.value = 'Неверный формат JSON';
  }
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
  border-radius: 32px;
  padding: 30px;
  max-width: 500px;
  width: 90%;
  box-shadow: var(--shadow-strong);
  color: var(--modal-text);
}
.modal-content h3 {
  color: var(--heading-color);
  margin-bottom: 20px;
  font-weight: 500;
}
.form-group {
  margin-bottom: 20px;
}
.form-group label {
  display: block;
  margin-bottom: 6px;
  color: var(--text-secondary);
  font-weight: 500;
}
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-primary);
  font-size: 1rem;
  outline: none;
}
.form-group select:focus,
.form-group textarea:focus {
  border-color: var(--accent-color);
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.2);
}
.error-message {
  color: var(--danger-color);
  font-size: 0.85rem;
  margin-top: 4px;
}
.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 30px;
}
.submit-btn, .cancel-btn {
  padding: 10px 25px;
  border: none;
  border-radius: 30px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.submit-btn {
  background: var(--accent-color);
  color: var(--button-text);
}
.submit-btn:hover {
  background: var(--accent-hover);
  transform: scale(1.02);
}
.cancel-btn {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}
.cancel-btn:hover {
  background: var(--bg-page);
}
</style>