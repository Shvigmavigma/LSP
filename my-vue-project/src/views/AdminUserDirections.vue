<template>
  <div class="page">
    <header>
      <h1>{{ $t('adminDirections.title') }}</h1>
      <div class="actions"><LanguageSwitcher /><ThemeToggle /><HomeButton /></div>
    </header>

    <form class="add-row" @submit.prevent="addDirection">
      <input v-model.trim="label" :placeholder="$t('adminDirections.namePlaceholder')" required />
      <input v-model.trim="key" :placeholder="$t('adminDirections.keyPlaceholder')" />
      <button type="submit" :disabled="saving">{{ $t('common.add') }}</button>
    </form>

    <p v-if="error" class="error">{{ error }}</p>
    <div class="list">
      <div v-for="direction in directions" :key="direction.key" class="item">
        <div><strong>{{ direction.label }}</strong><small>{{ direction.key }}</small></div>
        <button v-if="direction.key !== 'no_direction'" class="delete" @click="removeDirection(direction.key)" :title="$t('common.delete')">×</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import api from '@/utils/api';
import HomeButton from '@/components/HomeButton.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';
import ThemeToggle from '@/components/ThemeToggle.vue';

interface Direction { key: string; label: string }
const directions = ref<Direction[]>([]);
const label = ref('');
const key = ref('');
const saving = ref(false);
const error = ref('');

async function load() {
  const response = await api.get('/user-directions');
  directions.value = response.data.directions || [];
}
async function addDirection() {
  saving.value = true; error.value = '';
  try {
    await api.post('/admin/user-directions', { label: label.value, key: key.value || undefined });
    label.value = ''; key.value = ''; await load();
  } catch (e: any) { error.value = e.response?.data?.detail || String(e); }
  finally { saving.value = false; }
}
async function removeDirection(directionKey: string) {
  error.value = '';
  try { await api.delete(`/admin/user-directions/${directionKey}`); await load(); }
  catch (e: any) { error.value = e.response?.data?.detail || String(e); }
}
onMounted(load);
</script>

<style scoped>
.page { min-height: 100vh; padding: 20px; background: var(--bg-page); color: var(--text-primary); }
header, .add-row, .list { max-width: 900px; margin: 0 auto 20px; }
header, .actions, .add-row, .item { display: flex; align-items: center; gap: 10px; }
header, .item { justify-content: space-between; }
.add-row { flex-wrap: wrap; }
input { flex: 1; min-width: 220px; padding: 10px; border: 1px solid var(--input-border); border-radius: 8px; background: var(--input-bg); color: var(--text-primary); }
button { padding: 10px 16px; border: 0; border-radius: 8px; background: var(--accent-color); color: var(--button-text); cursor: pointer; }
.item { padding: 14px; border-bottom: 1px solid var(--border-color); background: var(--bg-card); }
.item small { display: block; color: var(--text-secondary); margin-top: 4px; }
.delete { background: var(--danger-color); font-size: 20px; }
.error { max-width: 900px; margin: 0 auto 15px; color: var(--danger-color); }
</style>
