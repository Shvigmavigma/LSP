import { createI18n } from 'vue-i18n'
import ru from './locales/ru.json'
import en from './locales/en.json'
import zh from './locales/zh.json'   // добавьте импорт

const messages = {
  ru,
  en,
  zh     // добавьте в объект
}

const savedLocale = localStorage.getItem('locale') || 'ru'

const i18n = createI18n({
  legacy: false,
  locale: savedLocale,
  fallbackLocale: 'ru',
  messages
})

export default i18n