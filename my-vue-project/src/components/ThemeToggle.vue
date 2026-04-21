<template>
  <div class="theme-switch-wrapper">
    <input
      type="checkbox"
      :id="switchId"
      :checked="isDark"
      @change="toggleTheme"
    />
    <label :for="switchId">
      <div id="star">
        <div class="star" id="star-1"></div>
      </div>
      <div id="moon"></div>
    </label>
  </div>
</template>

<script setup lang="ts">
import { useThemeStore } from '@/stores/theme';
import { computed } from 'vue';

const themeStore = useThemeStore();

const isDark = computed(() => themeStore.isDark);
const switchId = computed(() => `toggle_checkbox_${Math.random()}`);

const toggleTheme = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.checked !== isDark.value) {
    themeStore.toggleTheme();
  }
};
</script>

<style scoped>
* {
  user-select: none;
}

.theme-switch-wrapper {
  display: inline-block;
  position: relative;
  width: 100px;
  height: 45px;
}

#toggle_checkbox {
  display: none;
}

.theme-switch-wrapper label {
  display: block;
  position: relative;
  width: 100px;
  height: 45px;
  background-color: var(--bg-card);
  border-radius: 25px;
  cursor: pointer;
  transition: 0.3s ease background-color;
  overflow: hidden;
}

.theme-switch-wrapper #star {
  position: absolute;
  top: 7.5px;
  left: 7.5px;
  width: 30px;
  height: 30px;
  background-color: #fdc10f;
  transform: scale(1);
  border-radius: 50%;
  transition: 0.3s ease top, 0.3s ease left, 0.3s ease transform, 0.3s ease background-color;
  z-index: 1;
}

.theme-switch-wrapper #star-1 {
  position: relative;
}

.theme-switch-wrapper #star-2 {
  position: absolute;
  transform: rotateZ(36deg);
}

.theme-switch-wrapper .star {
  top: 0px;
  left: 10px;
  font-size: 54px;
  line-height: 28px;
  color: #fdc10f;
  transition: 0.3s ease color;
}

.theme-switch-wrapper #moon {
  position: absolute;
  bottom: -52px;
  right: 7.5px;
  width: 30px;
  height: 30px;
  background-color: #fff;
  border-radius: 50%;
  transition: 0.3s ease bottom;
}

.theme-switch-wrapper #moon:before {
  content: "";
  position: absolute;
  top: -6px;
  left: -8px;
  width: 30px;
  height: 30px;
  background-color: var(--bg-card);
  border-radius: 50%;
  transition: 0.3s ease background-color;
}

/* Тёмная тема (когда чекбокс отмечен) */
.theme-switch-wrapper input:checked + label {
  background-color: var(--bg-card);
}

.theme-switch-wrapper input:checked + label #star {
  top: 2.5px;
  left: 56px;
  transform: scale(0.3);
  background-color: #fdc10f;
}

.theme-switch-wrapper input:checked + label .star {
  color: #fdc10f;
}

.theme-switch-wrapper input:checked + label #moon {
  bottom: 7.5px;
}

.theme-switch-wrapper input:checked + label #moon:before {
  background-color: var(--bg-card);
}

/* Скрываем стандартный чекбокс */
.theme-switch-wrapper input {
  display: none;
}

/* Адаптация для маленьких экранов */
@media (max-width: 768px) {
  .theme-switch-wrapper {
    transform: scale(0.8);
  }
}

@media (max-width: 480px) {
  .theme-switch-wrapper {
    transform: scale(0.7);
  }
}
</style>