import { defineStore } from 'pinia'
import { ref } from 'vue'
import i18n from '@/i18n'

type Locale = 'ru' | 'en' | 'zh' | 'ua' | 'ar'

export const useLanguageStore = defineStore('language', () => {
  const currentLocale = ref<Locale>(localStorage.getItem('locale') as Locale || 'ru')

  function setLocale(locale: Locale) {
    currentLocale.value = locale
    i18n.global.locale.value = locale
    localStorage.setItem('locale', locale)
  }

  setLocale(currentLocale.value)

  return { currentLocale, setLocale }
})