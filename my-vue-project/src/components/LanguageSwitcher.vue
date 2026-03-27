<template>
  <div class="language-switcher-container" ref="containerRef">
    <button
      class="language-switcher-button"
      @click.stop="toggleDropdown"
      :aria-label="$t('language.select')"
    >
      <div class="current-flag-wrapper">
        <span :class="`fi fi-${flagCode[currentLocale]}`" class="current-flag"></span>
      </div>
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
          <div class="lang-flag-wrapper">
            <span :class="`fi fi-${flagCode[lang.code]}`" class="lang-flag"></span>
          </div>
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

const { t } = useI18n()
const languageStore = useLanguageStore()
const currentLocale = computed(() => languageStore.currentLocale)

const isOpen = ref(false)
const containerRef = ref<HTMLElement | null>(null)

type Locale = 'ru' | 'en' | 'zh' | 'ua' | 'ar'

const flagCode: Record<Locale, string> = {
  ru: 'ru',
  en: 'gb',
  zh: 'cn',
  ua: 'ua',
  ar: 'sa'
}

const languages: { code: Locale; name: string }[] = [
  { code: 'ru', name: 'Русский' },
  { code: 'en', name: 'English' },
  { code: 'zh', name: '中文' },
  { code: 'ua', name: 'Українська' },
  { code: 'ar', name: 'العربية' }
]

const toggleDropdown = () => {
  isOpen.value = !isOpen.value
}

const selectLanguage = (code: Locale) => {
  languageStore.setLocale(code)
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

.current-flag-wrapper {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-card);
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.05); /* тонкая рамка для чёткости */
}

.current-flag {
  font-size: 1.5rem;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scale(1.05); /* небольшое увеличение, чтобы заполнить круг */
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

.lang-flag-wrapper {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-card);
  flex-shrink: 0;
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.05);
}

.lang-flag {
  font-size: 1.1rem;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scale(1.05);
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