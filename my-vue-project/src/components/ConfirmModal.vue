<template>
  <Teleport to="body">
    <div v-if="show" class="confirm-modal-overlay" @click.self="close">
      <div class="confirm-modal">
        <div class="modal-header">
          <div class="icon" v-if="icon">{{ icon }}</div>
          <h3>{{ title }}</h3>
        </div>
        <div class="modal-body">
          <p>{{ message }}</p>
        </div>
        <div class="modal-footer">
          <button class="confirm-btn" @click="confirm">{{ confirmText }}</button>
          <button class="cancel-btn" @click="close">{{ cancelText }}</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
defineProps<{
  show: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  icon?: string;
}>();

const emit = defineEmits<{
  (e: 'confirm'): void;
  (e: 'close'): void;
}>();

const confirm = () => {
  emit('confirm');
};

const close = () => {
  emit('close');
};
</script>

<style scoped>
.confirm-modal-overlay {
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
  z-index: 3000;
  animation: fadeIn 0.2s ease;
}

.confirm-modal {
  background: var(--modal-bg);
  border-radius: 24px;
  padding: 24px;
  max-width: 400px;
  width: 90%;
  box-shadow: var(--shadow-strong);
  animation: scaleIn 0.2s ease;
}

.modal-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.modal-header .icon {
  font-size: 2rem;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 600;
  color: var(--heading-color);
}

.modal-body {
  margin-bottom: 24px;
  color: var(--text-primary);
  line-height: 1.5;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.confirm-btn, .cancel-btn {
  padding: 8px 20px;
  border: none;
  border-radius: 30px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.confirm-btn {
  background: var(--danger-color);
  color: white;
}

.confirm-btn:hover {
  background: var(--danger-hover);
  transform: translateY(-1px);
}

.cancel-btn {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.cancel-btn:hover {
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