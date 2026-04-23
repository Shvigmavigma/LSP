import { defineStore } from 'pinia';
import { ref, watch } from 'vue';

export const useThemeStore = defineStore('theme', () => {
  const savedTheme = localStorage.getItem('theme');
  const isDark = ref(savedTheme === 'dark');

  function toggleTheme() {
    isDark.value = !isDark.value;
  }

  function setTheme(dark: boolean) {
    isDark.value = dark;
  }

  function applyTheme(dark: boolean) {
    if (dark) {
      document.documentElement.classList.add('dark-theme');
      document.documentElement.classList.remove('light-theme');
    } else {
      document.documentElement.classList.add('light-theme');
      document.documentElement.classList.remove('dark-theme');
    }
  }

  watch(isDark, (val) => {
    localStorage.setItem('theme', val ? 'dark' : 'light');
    applyTheme(val);
  }, { immediate: true });

  return { isDark, toggleTheme, setTheme };
});