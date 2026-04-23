<template>
  <div class="verify-page">
    <div class="theme-toggle-container">
      <ThemeToggle />
      <LanguageSwitcher />
    </div>
    <div class="verify-card">
      <h2>{{ $t('verifyEmail.title') }}</h2>
      
      <div v-if="verifying" class="loading">
        {{ $t('common.loading') }}
      </div>
      
      <div v-else-if="success" class="success">
        ✅ {{ $t('verifyEmail.successTitle') }}
        <p>{{ $t('verifyEmail.successMessage') }}</p>
      </div>
      
      <div v-else-if="error" class="error">
        ❌ {{ error }}
        <p v-if="errorDetails" class="error-details">{{ errorDetails }}</p>
        <button @click="goBack" class="back-button">{{ $t('verifyEmail.backToRegistration') }}</button>
      </div>
      
      <div v-else>
        <p>{{ $t('verifyEmail.enterCodeInstruction') }}</p>
        <p class="email-highlight">{{ email }}</p>
        
        <div class="form-group">
          <input
            v-model="code"
            type="text"
            :placeholder="$t('verifyEmail.codePlaceholder')"
            maxlength="6"
            @keyup.enter="verifyCode"
          />
        </div>
        
        <button @click="verifyCode" :disabled="verifying">
          {{ verifying ? $t('common.sending') : $t('verifyEmail.verifyButton') }}
        </button>
        
        <p class="resend">
          <a href="#" @click.prevent="resendCode">{{ $t('verifyEmail.resendCode') }}</a>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import ThemeToggle from '@/components/ThemeToggle.vue'
import LanguageSwitcher from '@/components/LanguageSwitcher.vue'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const email = ref(route.query.email || '')
const code = ref('')
const verifying = ref(false)
const success = ref(false)
const error = ref('')
const errorDetails = ref('')
const hasCheckedData = ref(false)

onMounted(() => {
  checkPendingData()
})

function checkPendingData() {
  const pendingData = sessionStorage.getItem('pending_registration')
  console.log('Проверка sessionStorage на VerifyEmail:', pendingData ? 'Данные найдены' : 'Данные не найдены')
  console.log('Email из URL:', email.value)
  
  if (!pendingData) {
    if (email.value) {
      error.value = t('verifyEmail.errors.noRegistrationData')
      errorDetails.value = t('verifyEmail.errors.sessionExpired')
    } else {
      error.value = t('verifyEmail.errors.missingEmail')
      errorDetails.value = t('verifyEmail.errors.startOver')
    }
  } else {
    try {
      const userData = JSON.parse(pendingData)
      if (userData.email !== email.value) {
        console.warn('Email в URL не совпадает с email в данных:', userData.email, email.value)
        error.value = t('verifyEmail.errors.emailMismatch')
        errorDetails.value = t('verifyEmail.errors.restart')
        sessionStorage.removeItem('pending_registration')
        sessionStorage.removeItem('pending_avatar')
      }
    } catch (e) {
      console.error('Ошибка парсинга данных:', e)
      sessionStorage.removeItem('pending_registration')
      sessionStorage.removeItem('pending_avatar')
      error.value = t('verifyEmail.errors.dataCorrupted')
      errorDetails.value = t('verifyEmail.errors.restart')
    }
  }
  
  hasCheckedData.value = true
}

async function verifyCode() {
  if (!code.value || code.value.length !== 6) {
    error.value = t('verifyEmail.errors.invalidCodeLength')
    return
  }
  
  const pendingData = sessionStorage.getItem('pending_registration')
  if (!pendingData) {
    error.value = t('verifyEmail.errors.noRegistrationData')
    errorDetails.value = t('verifyEmail.errors.goBack')
    return
  }
  
  verifying.value = true
  error.value = ''
  errorDetails.value = ''
  
  try {
    const userData = JSON.parse(pendingData)
    console.log('Данные пользователя из sessionStorage:', userData)
    
    const response = await axios.post(
      'http://localhost:8000/auth/register-with-verification',
      {
        email: email.value,
        code: code.value,
        user_data: userData,
        is_teacher: userData.is_teacher || false
      }
    )
    
    console.log('Пользователь успешно создан:', response.data)
    
    const pendingAvatar = sessionStorage.getItem('pending_avatar')
    if (pendingAvatar && response.data.id) {
      try {
        const base64Data = pendingAvatar.split(',')[1]
        const byteCharacters = atob(base64Data)
        const byteArrays = []
        
        for (let offset = 0; offset < byteCharacters.length; offset += 512) {
          const slice = byteCharacters.slice(offset, offset + 512)
          const byteNumbers = new Array(slice.length)
          for (let i = 0; i < slice.length; i++) {
            byteNumbers[i] = slice.charCodeAt(i)
          }
          const byteArray = new Uint8Array(byteNumbers)
          byteArrays.push(byteArray)
        }
        
        const blob = new Blob(byteArrays, { type: 'image/webp' })
        const file = new File([blob], 'avatar.webp', { type: 'image/webp' })
        
        const formData = new FormData()
        formData.append('file', file)
        
        await axios.post(
          `http://localhost:8000/users/${response.data.id}/avatar`,
          formData,
          { headers: { 'Content-Type': 'multipart/form-data' } }
        )
        console.log('Аватарка загружена')
      } catch (avatarError) {
        console.error('Ошибка загрузки аватарки:', avatarError)
      }
    }
    
    sessionStorage.removeItem('pending_registration')
    sessionStorage.removeItem('pending_avatar')
    
    success.value = true
    setTimeout(() => router.push('/login'), 3000)
    
  } catch (err: any) {
    console.error('Ошибка верификации:', err)
    
    if (err.code === 'ERR_NETWORK') {
      error.value = t('verifyEmail.errors.network')
    } else if (err.response) {
      if (err.response.status === 400) {
        if (err.response.data?.detail === 'Invalid or expired verification code') {
          error.value = t('verifyEmail.errors.invalidOrExpiredCode')
          errorDetails.value = t('verifyEmail.errors.resendHint')
        } else if (err.response.data?.detail === 'Nickname or email already registered') {
          error.value = t('verifyEmail.errors.alreadyRegistered')
          errorDetails.value = t('verifyEmail.errors.tryLogin')
        } else {
          error.value = err.response.data?.detail || t('verifyEmail.errors.registrationFailed')
        }
      } else if (err.response.status === 403) {
        error.value = t('verifyEmail.errors.emailNotAllowed')
        errorDetails.value = t('verifyEmail.errors.teacherEmailHint')
      } else {
        error.value = err.response.data?.detail || t('verifyEmail.errors.serverError')
      }
    } else {
      error.value = err.message || t('verifyEmail.errors.unknown')
    }
  } finally {
    verifying.value = false
  }
}

async function resendCode() {
  if (!email.value) {
    error.value = t('verifyEmail.errors.missingEmail')
    return
  }
  
  verifying.value = true
  error.value = ''
  
  try {
    const response = await axios.post('http://localhost:8000/auth/request-verification-code', {
      email: email.value
    })
    alert(t('verifyEmail.resendSuccess'))
  } catch (err: any) {
    console.error('Ошибка при повторной отправке:', err)
    
    if (err.response?.status === 400) {
      if (err.response.data?.detail === 'Email already registered') {
        error.value = t('verifyEmail.errors.alreadyRegistered')
        errorDetails.value = t('verifyEmail.errors.tryLogin')
      } else {
        error.value = err.response.data?.detail || t('verifyEmail.errors.resendFailed')
      }
    } else if (err.code === 'ERR_NETWORK') {
      error.value = t('verifyEmail.errors.network')
    } else {
      error.value = err.message || t('verifyEmail.errors.resendFailed')
    }
  } finally {
    verifying.value = false
  }
}

function goBack() {
  sessionStorage.removeItem('pending_registration')
  sessionStorage.removeItem('pending_avatar')
  router.push('/register')
}
</script>

<style scoped>
.verify-page {
  min-height: 100vh;
  background: var(--bg-page);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  position: relative;
}

.theme-toggle-container {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 10;
}

.verify-card {
  background: var(--bg-card);
  border-radius: 16px;
  padding: 40px;
  max-width: 400px;
  width: 90%;
  box-shadow: var(--shadow-strong);
}

h2 {
  color: var(--heading-color);
  margin-bottom: 20px;
  text-align: center;
}

.email-highlight {
  font-weight: bold;
  color: var(--accent-color);
  text-align: center;
  margin-bottom: 20px;
  word-break: break-all;
}

.form-group {
  margin-bottom: 20px;
}

input {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  font-size: 18px;
  text-align: center;
  background: var(--input-bg);
  color: var(--text-primary);
  outline: none;
}

input:focus {
  border-color: var(--accent-color);
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.2);
}

button {
  width: 100%;
  padding: 14px;
  background: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

button:hover:not(:disabled) {
  background: var(--accent-hover);
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.back-button {
  margin-top: 15px;
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.back-button:hover:not(:disabled) {
  background: var(--bg-page);
}

.success {
  color: #4caf50;
  text-align: center;
  padding: 20px;
}

.error {
  color: #f44336;
  text-align: center;
  padding: 20px;
}

.error-details {
  font-size: 0.85rem;
  background: rgba(244, 67, 54, 0.1);
  padding: 10px;
  border-radius: 8px;
  margin-top: 10px;
  word-break: break-word;
}

.resend {
  text-align: center;
  margin-top: 20px;
}

.resend a {
  color: var(--link-color);
  text-decoration: none;
  cursor: pointer;
}

.resend a:hover {
  text-decoration: underline;
}

.loading {
  text-align: center;
  color: var(--text-secondary);
  padding: 20px;
}
</style>