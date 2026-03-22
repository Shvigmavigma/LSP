<template>
  <Teleport to="body">
    <div v-if="show" class="modal-overlay" @click.self="close">
      <div class="modal-content">
        <h3>Пригласить участника</h3>
        <form @submit.prevent="submit">
          <div class="form-group">
            <label for="email">Email пользователя</label>
            <input
              id="email"
              v-model="email"
              type="email"
              placeholder="user@example.com"
              required
            />
          </div>

          <div class="form-group">
            <label for="role">Роль</label>
            <select id="role" v-model="role" required>
              <option value="executor">Исполнитель</option>
              <option value="customer">Заказчик</option>
              <option value="supervisor">Научный руководитель</option>
              <option value="expert">Эксперт</option>
              <option value="curator">Куратор</option>
            </select>
          </div>

          <div class="modal-actions">
            <button type="submit" class="invite-btn" :disabled="sending">
              {{ sending ? 'Отправка...' : 'Отправить приглашение' }}
            </button>
            <button type="button" class="cancel-btn" @click="close">Отмена</button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import type { ProjectRole } from '@/types';

const props = defineProps<{
  show: boolean;
  projectId?: number;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'invite', email: string, role: ProjectRole): void;
}>();

const email = ref('');
const role = ref<ProjectRole>('executor');
const sending = ref(false);

watch(() => props.show, (val) => {
  if (val) {
    email.value = '';
    role.value = 'executor';
    sending.value = false;
  }
});

async function submit() {
  if (!email.value || !role.value) return;
  sending.value = true;
  try {
    await emit('invite', email.value, role.value);
    close();
  } catch (error) {
    console.error('Invite error:', error);
  } finally {
    sending.value = false;
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
  max-width: 400px;
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
.form-group input,
.form-group select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-primary);
  font-size: 1rem;
  outline: none;
}
.form-group input:focus,
.form-group select:focus {
  border-color: var(--accent-color);
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.2);
}
.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 30px;
}
.invite-btn, .cancel-btn {
  padding: 10px 25px;
  border: none;
  border-radius: 30px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.invite-btn {
  background: var(--accent-color);
  color: var(--button-text);
}
.invite-btn:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: scale(1.02);
}
.invite-btn:disabled {
  opacity: 0.6;
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
</style>