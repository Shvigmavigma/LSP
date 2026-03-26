<template>
  <div class="language-switcher-container" ref="containerRef">
    <button
      class="language-switcher-button"
      @click.stop="toggleDropdown"
      :aria-label="$t('language.select')"
    >
      <span class="current-flag">{{ currentFlag }}</span>
    </button>

    <Transition name="dropdown">
      <div v-if="isOpen" class="language-dropdown" @click.stop>
        <div
          v-for="lang in languages"
          :key="lang.code"
          class="language-option"
          :class="{ active: lang.code === currentLocale }"
          @click="selectLanguage(lang.code)"
        >
          <span class="lang-flag">{{ lang.flag }}</span>
          <span class="lang-name">{{ lang.name }}</span>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useLanguageStore } from '@/stores/language'
import { useI18n } from 'vue-i18n'
import i18n from '@/i18n'  // импортируем сам экземпляр i18n

const { t } = useI18n()
const languageStore = useLanguageStore()
const currentLocale = computed(() => languageStore.currentLocale)

const isOpen = ref(false)
const containerRef = ref<HTMLElement | null>(null)

type Locale = 'ru' | 'en' | 'zh'

const languages: { code: Locale; flag: string; name: string }[] = [
  { code: 'ru', flag: '🇷🇺', name: 'Русский' },
  { code: 'en', flag: 'en', name: 'English' },
  { code: 'zh', flag: '🇨🇳', name: '中文' }
]

const currentFlag = computed(() => {
  const lang = languages.find(l => l.code === currentLocale.value)
  return lang?.flag || '🌐'
})

const toggleDropdown = () => {
  isOpen.value = !isOpen.value
}

const selectLanguage = (code: Locale) => {
  // 1. Напрямую обновляем i18n
  i18n.global.locale.value = code
  // 2. Сохраняем в localStorage
  localStorage.setItem('locale', code)
  // 3. Обновляем стор (чтобы currentLocale тоже изменился)
  //    Используем as any для обхода типов, если стор пока не знает 'zh'
  languageStore.setLocale(code as any)
  // 4. Закрываем дропдаун
  isOpen.value = false
}

const handleClickOutside = (event: MouseEvent) => {
  if (containerRef.value && !containerRef.value.contains(event.target as Node)) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
/* все стили остаются прежними */
.language-switcher-container {
  position: relative;
  display: inline-block;
}

.language-switcher-button {
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

.language-switcher-button:hover {
  transform: scale(1.1);
  box-shadow: var(--shadow-strong);
}

.language-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  box-shadow: var(--shadow-strong);
  min-width: 140px;
  overflow: hidden;
  z-index: 1000;
}

.language-option {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  cursor: pointer;
  transition: background 0.2s;
  color: var(--text-primary);
}

.language-option:hover {
  background: var(--bg-page);
}

.language-option.active {
  background: rgba(66, 185, 131, 0.1);
  color: var(--accent-color);
}

.lang-flag {
  font-size: 1.3rem;
}

.lang-name {
  font-size: 0.95rem;
  font-weight: 500;
}

.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>