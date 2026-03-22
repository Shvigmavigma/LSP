<template>
  <div class="class-input-wrapper">
    <div class="input-container">
      <input
        type="text"
        :value="inputValue"
        @input="handleInput"
        @keydown.up="handleArrowUp"
        @keydown.down="handleArrowDown"
        @blur="handleBlur"
        :placeholder="placeholder"
        :required="required"
        class="class-input"
        :class="{ 'error': showError }"
      />
      <div class="class-input-spinners">
        <button
          type="button"
          class="spinner-button up"
          @click="handleArrowUp"
          :disabled="!canGoUp"
          title="Увеличить"
        >
          ▲
        </button>
        <button
          type="button"
          class="spinner-button down"
          @click="handleArrowDown"
          :disabled="!canGoDown"
          title="Уменьшить"
        >
          ▼
        </button>
      </div>
    </div>
    <div v-if="showError" class="error-message">
      {{ errorMessage }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';

const props = defineProps<{
  modelValue: number | null;
  placeholder?: string;
  required?: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: number | null): void;
}>();

// Локальное состояние для отображения ввода
const inputValue = ref(props.modelValue?.toFixed(1) || '');
const showError = ref(false);
const errorMessage = ref('');

// Следим за изменением modelValue извне (например, сброс)
watch(() => props.modelValue, (newVal) => {
  inputValue.value = newVal?.toFixed(1) || '';
  showError.value = false;
});

// Все допустимые значения
const validValues = new Set<number>();
for (let whole = 3; whole <= 11; whole++) {
  let maxFrac = 2;
  if (whole === 5) maxFrac = 4;
  else if (whole >= 6) maxFrac = 6;
  for (let frac = 1; frac <= maxFrac; frac++) {
    validValues.add(whole + frac / 10);
  }
}
const sortedValidValues = Array.from(validValues).sort((a, b) => a - b);

// Проверка, является ли строка допустимым значением класса
const isValidClassString = (str: string): boolean => {
  if (str === '') return true;
  if (!/^\d+\.\d$/.test(str)) return false;
  const [wholeStr, fracStr] = str.split('.');
  const whole = parseInt(wholeStr, 10);
  const frac = parseInt(fracStr, 10);
  if (whole < 3 || whole > 11) return false;
  let maxFrac = 2;
  if (whole === 5) maxFrac = 4;
  else if (whole >= 6) maxFrac = 6;
  return frac >= 1 && frac <= maxFrac;
};

// Маска: последняя цифра становится дробной частью
const applyMask = (raw: string): string => {
  const digits = raw.replace(/\D/g, '');
  if (digits.length === 0) return '';
  if (digits.length === 1) return digits;
  const wholePart = digits.slice(0, -1);
  const fracPart = digits.slice(-1);
  return `${wholePart}.${fracPart}`;
};

// Индекс текущего значения в списке
const currentIndex = computed(() => {
  if (props.modelValue === null) return -1;
  return sortedValidValues.indexOf(props.modelValue);
});

const canGoUp = computed(() => {
  if (props.modelValue === null) return true;
  return currentIndex.value < sortedValidValues.length - 1;
});

const canGoDown = computed(() => {
  if (props.modelValue === null) return true;
  return currentIndex.value > 0;
});

// Обработка ввода
const handleInput = (e: Event) => {
  const input = e.target as HTMLInputElement;
  const raw = input.value;
  const masked = applyMask(raw);
  inputValue.value = masked;

  if (masked === '') {
    if (!props.required) {
      emit('update:modelValue', null);
      showError.value = false;
    } else {
      showError.value = true;
      errorMessage.value = 'Поле обязательно';
    }
  } else if (isValidClassString(masked)) {
    const num = parseFloat(masked);
    emit('update:modelValue', num);
    showError.value = false;
  } else {
    showError.value = true;
    errorMessage.value = 'Недопустимое значение класса';
  }
};

// Получить следующее допустимое значение
const getNextValid = (direction: 'up' | 'down'): number | null => {
  if (props.modelValue === null) {
    return direction === 'up' ? 3.1 : 11.6;
  }
  const index = currentIndex.value;
  if (index === -1) return props.modelValue;
  let newIndex = direction === 'up' ? index + 1 : index - 1;
  if (newIndex < 0) newIndex = sortedValidValues.length - 1;
  if (newIndex >= sortedValidValues.length) newIndex = 0;
  return sortedValidValues[newIndex];
};

const handleArrowUp = (e?: KeyboardEvent | MouseEvent) => {
  e?.preventDefault();
  const next = getNextValid('up');
  emit('update:modelValue', next);
  showError.value = false;
  inputValue.value = next?.toFixed(1) || '';
};

const handleArrowDown = (e?: KeyboardEvent | MouseEvent) => {
  e?.preventDefault();
  const next = getNextValid('down');
  emit('update:modelValue', next);
  showError.value = false;
  inputValue.value = next?.toFixed(1) || '';
};

// При потере фокуса
const handleBlur = () => {
  if (inputValue.value === '') {
    if (props.required) {
      showError.value = true;
      errorMessage.value = 'Поле обязательно';
    } else {
      emit('update:modelValue', null);
      showError.value = false;
    }
    return;
  }
  if (!isValidClassString(inputValue.value)) {
    inputValue.value = props.modelValue?.toFixed(1) || '';
    showError.value = false;
  }
};
</script>

<style scoped>
.class-input-wrapper {
  width: 100%;
}

.input-container {
  display: flex;
  align-items: stretch;
  width: 100%;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  overflow: hidden;
  background: var(--input-bg);
}

.class-input {
  flex: 1;
  padding: 12px 16px;
  border: none;
  font-size: 1rem;
  outline: none;
  background: var(--input-bg);
  color: var(--text-primary);
}

.class-input:focus {
  box-shadow: inset 0 0 0 2px var(--accent-color);
}

.class-input.error {
  box-shadow: inset 0 0 0 2px var(--danger-color);
}

.class-input-spinners {
  display: flex;
  flex-direction: column;
  border-left: 1px solid var(--input-border);
  background: var(--input-bg);
  width: 30px;
}

.spinner-button {
  background: var(--input-bg);
  border: none;
  font-size: 12px;
  padding: 0;
  cursor: pointer;
  color: var(--text-secondary);
  transition: background 0.2s;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  min-height: 24px;
}

.spinner-button:hover:not(:disabled) {
  background: var(--bg-card);
  color: var(--accent-color);
}

.spinner-button:active:not(:disabled) {
  background: var(--accent-color);
  color: white;
}

.spinner-button:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.spinner-button.up {
  border-bottom: 1px solid var(--input-border);
}

.error-message {
  margin-top: 4px;
  font-size: 0.85rem;
  color: var(--danger-color);
  padding-left: 4px;
}
</style>