import { createI18n } from 'vue-i18n'
import ru from './locales/ru.json'
import en from './locales/en.json'
import zh from './locales/zh.json'
import ua from './locales/ua.json'
import ar from './locales/ar.json'   // новый импорт

const messages = {
  ru,
  en,
  zh,
  ua,
  ar
}

export type Locale = keyof typeof messages  // 'ru' | 'en' | 'zh' | 'ua' | 'ar'

const savedLocale = (localStorage.getItem('locale') as Locale) || 'ru'

const i18n = createI18n({
  legacy: false,
  locale: savedLocale,
  fallbackLocale: 'ru',
  messages
})

export default i18n