<template>
  <Teleport to="body">
    <div v-if="show" class="avatar-modal-overlay" @click.self="close">
      <div class="avatar-modal-content" @click.stop>
        <button class="close-button" @click="close">×</button>
        <img :src="src" :alt="alt" class="avatar-modal-image" />
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
defineProps<{
  show: boolean;
  src: string;
  alt?: string;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const close = () => {
  emit('close');
};
</script>

<style scoped>
.avatar-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(5px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  animation: fadeIn 0.2s ease;
}

.avatar-modal-content {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
  background: var(--bg-card);
  border-radius: 16px;
  padding: 16px;
  box-shadow: var(--shadow-strong);
  animation: zoomIn 0.3s ease;
}

.avatar-modal-image {
  display: block;
  max-width: 100%;
  max-height: calc(90vh - 32px);
  border-radius: 12px;
  object-fit: contain;
}

.close-button {
  position: absolute;
  top: -12px;
  right: -12px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--bg-card);
  border: 2px solid var(--border-color);
  color: var(--text-primary);
  font-size: 24px;
  font-weight: bold;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  z-index: 2001;
}

.close-button:hover {
  background: var(--accent-color);
  color: var(--button-text);
  transform: scale(1.1);
  border-color: var(--accent-color);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes zoomIn {
  from { transform: scale(0.9); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
</style>