<template>
  <button class="theme-toggle" @click="toggleTheme" :title="isDark ? 'Светлая тема' : 'Темная тема'">
    {{ isDark ? '☀️' : '🌙' }}
  </button>
</template>

<script setup lang="ts">
import { useThemeStore } from '@/stores/theme';

const themeStore = useThemeStore();
const isDark = themeStore.isDark;

const toggleTheme = () => {
  themeStore.toggleTheme();
};
</script>

<style scoped>
.theme-toggle {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 50%;
  width: 44px;
  height: 44px;
  font-size: 1.5rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  color: var(--text-primary);
  padding: 0;
  margin: 0;
}

.theme-toggle:hover {
  transform: scale(1.1);
  box-shadow: var(--shadow-strong);
}
</style>