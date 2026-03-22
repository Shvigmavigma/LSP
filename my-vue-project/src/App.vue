<template>
  <router-view />
</template>

<script setup lang="ts">
import { useThemeStore } from './stores/theme';
import { onMounted } from 'vue';
import { useAuthStore } from './stores/auth';

useThemeStore();
const authStore = useAuthStore();

onMounted(async () => {
  await authStore.checkAuth();
});

</script>

<style>
/* Светлая тема (по умолчанию) */
:root, .light-theme {
  --bg-page: linear-gradient(135deg, #f0f9f0 0%, #d4eed7 100%);
  --bg-card: #ffffff;
  --bg-column: rgba(255, 255, 255, 0.6);
  --text-primary: #1a3a1a;
  --text-secondary: #3b5e3b;
  --heading-color: #1f4f22;
  --accent-color: #42b983;
  --accent-hover: #3aa876;
  --link-color: #42b983;
  --link-hover: #2c5e2e;
  --border-color: #e0f0e0;
  --shadow: 0 8px 20px rgba(0, 0, 0, 0.05);
  --shadow-strong: 0 10px 30px rgba(0, 40, 0, 0.1);
  --input-bg: #ffffff;
  --input-border: #020d18;
  --button-text: #ffffff;
  --danger-color: #c44;
  --danger-bg: #fee;
  --danger-hover: #fdd;
  --overlay-bg: rgba(0, 0, 0, 0.5);
  --modal-bg: #ffffff;
  --modal-text: #1a3a1a;
  --overdue-bg: #ffebee;
  --urgent-bg: #fff3e0;
  --invalid-bg: #f5f5f5;
  --not-started-bg: #eeeeee;
  --completed-bg: #f0f9f0;
}

/* Тёмная тема */
.dark-theme {
  --bg-page: #1b212c;
  --bg-card: #2d3748;
  --bg-column: rgba(45, 55, 72, 0.8);
  --text-primary: #ffffff;
  --text-secondary: #a0aec0;
  --heading-color: #5ec089;
  --accent-color: #2c7ef9;
  --accent-hover: #08387c;
  --link-color: #90cdf4;
  --link-hover: #5ec089;
  --border-color: #3a3f4b;
  --shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
  --shadow-strong: 0 10px 30px rgba(0, 0, 0, 0.3);
  --input-bg: #2d3748;
  --input-border: #3a3f4b;
  --button-text: #ffffff;
  --danger-color: #fc8181;
  --danger-bg: #742a2a;
  --danger-hover: #9b2c2c;
  --overlay-bg: rgba(0, 0, 0, 0.7);
  --modal-bg: #2d3748;
  --modal-text: #ffffff;
  --overdue-bg: rgba(244, 67, 54, 0.2);
  --urgent-bg: rgba(255, 152, 0, 0.2);
  --invalid-bg: rgba(158, 158, 158, 0.2);
  --not-started-bg: rgba(189, 189, 189, 0.2);
  --completed-bg: rgba(66, 185, 131, 0.1);
}

body {
  font-family: Arial, sans-serif;
  margin: 0;
  padding: 20px;
  background: var(--bg-page);
  color: var(--text-primary);
  transition: background 0.3s, color 0.3s;
}

* {
  box-sizing: border-box;
}
/* В App.vue или в отдельном CSS файле */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  width: 100%;
  max-width: 100%;
  overflow-x: hidden;
  margin: 0;
  padding: 0;
}

#app {
  width: 100%;
  max-width: 100%;
  overflow-x: hidden;
  min-height: 100vh;
}

/* Центрирование контента */
.container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}
</style>