<template>
  <button
    class="theme-toggle-switch"
    @click="toggleTheme"
    :title="titleText"
    :aria-label="titleText"
    role="switch"
    :aria-checked="isDark"
  >
    <span v-if="!isDark" class="theme-icon sun">☀️</span>
    <span v-else class="theme-icon moon">🌙</span>
    <span class="toggle-slider" :class="{ dark: isDark }"></span>
  </button>
</template>

<script setup lang="ts">
import { useThemeStore } from '@/stores/theme';
import { useI18n } from 'vue-i18n';
import { computed } from 'vue';

const themeStore = useThemeStore();
const { t } = useI18n();

const isDark = computed(() => themeStore.isDark);

const titleText = computed(() =>
  isDark.value ? t('theme.light') : t('theme.dark')
);

const toggleTheme = () => {
  themeStore.toggleTheme();
};
</script>

<style scoped>
.theme-toggle-switch {
  position: relative;
  width: 72px;
  height: 34px;
  border-radius: 34px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: background 0.2s;
  box-shadow: var(--shadow);
}

.theme-icon {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  font-size: 1.2rem;
  line-height: 1;
  z-index: 2;
  transition: opacity 0.2s;
}

.sun {
  left: 5px;
  top: calc(50% + 0px);
}

.moon {
  right: 2px;
}

.theme-toggle-switch .toggle-slider {
  position: absolute;
  top: 2px;
  left: 5px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--accent-color);
  transition: transform 0.25s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  z-index: 1;
}

/* Уменьшенный диапазон перемещения: 28px вместо 37 */
.theme-toggle-switch .toggle-slider.dark {
  transform: translateX(35px);
}

.theme-toggle-switch:hover {
  box-shadow: var(--shadow-strong);
}
</style>