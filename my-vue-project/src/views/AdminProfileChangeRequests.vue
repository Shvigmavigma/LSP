<template>
  <div class="requests-page">
    <header>
      <h1>{{ $t('profileRequests.title') }}</h1>
      <div class="header-actions"><ThemeToggle /><LanguageSwitcher /><HomeButton /></div>
    </header>

    <div class="filters">
      <button v-for="item in statuses" :key="item" :class="{ active: status === item }" @click="status = item; loadRequests()">
        {{ $t(`profileRequests.statuses.${item}`) }}
      </button>
    </div>

    <div v-if="loading" class="empty">{{ $t('common.loading') }}</div>
    <div v-else-if="!requests.length" class="empty">{{ $t('profileRequests.empty') }}</div>
    <article v-for="request in requests" :key="request.id" class="request-card">
      <div class="request-header">
        <div>
          <strong>{{ request.user_name }}</strong>
          <span>{{ request.user_email }}</span>
        </div>
        <span class="status">{{ $t(`profileRequests.statuses.${request.status}`) }}</span>
      </div>
      <div class="changes">
        <div v-for="field in changedFields(request)" :key="field" class="change-row">
          <strong>{{ fieldLabel(field) }}</strong>
          <span>{{ formatValue(request.old_data[field]) }}</span>
          <span>→</span>
          <span>{{ formatValue(request.new_data[field]) }}</span>
        </div>
      </div>
      <textarea v-if="request.status === 'pending'" v-model="comments[request.id]" :placeholder="$t('profileRequests.comment')" />
      <div v-if="request.status === 'pending'" class="actions">
        <button class="approve" @click="decide(request.id, 'approved')">{{ $t('profileRequests.approve') }}</button>
        <button class="reject" @click="decide(request.id, 'rejected')">{{ $t('profileRequests.reject') }}</button>
      </div>
    </article>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import api from '@/utils/api';
import ThemeToggle from '@/components/ThemeToggle.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';
import HomeButton from '@/components/HomeButton.vue';

const { t } = useI18n();
const statuses = ['pending', 'approved', 'rejected', 'withdrawn'];
const status = ref('pending');
const requests = ref<any[]>([]);
const comments = ref<Record<number, string>>({});
const loading = ref(true);

onMounted(loadRequests);

async function loadRequests() {
  loading.value = true;
  try {
    requests.value = (await api.get('/admin/profile-change-requests', { params: { status: status.value } })).data;
  } finally {
    loading.value = false;
  }
}
function changedFields(request: any) {
  return Object.keys(request.new_data || {}).filter(
    (field) => JSON.stringify(request.old_data?.[field]) !== JSON.stringify(request.new_data?.[field]),
  );
}
function fieldLabel(field: string) {
  return t(`profileRequests.fields.${field}`);
}
function formatValue(value: any) {
  if (value === null || value === undefined || value === '') return '—';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}
async function decide(id: number, decision: 'approved' | 'rejected') {
  await api.put(`/admin/profile-change-requests/${id}`, { decision, comment: comments.value[id] || '' });
  await loadRequests();
}
</script>

<style scoped>
.requests-page { min-height: 100vh; padding: 20px; background: var(--bg-page); color: var(--text-primary); }
header, .request-header, .actions, .filters { display: flex; justify-content: space-between; gap: 10px; align-items: center; }
header { max-width: 1100px; margin: 0 auto 20px; }
.header-actions, .filters { display: flex; flex-wrap: wrap; }
.filters { max-width: 1100px; margin: 0 auto 16px; justify-content: flex-start; }
button { padding: 8px 12px; border: 1px solid var(--border-color); background: var(--bg-card); color: var(--text-primary); cursor: pointer; border-radius: 6px; }
.filters button.active, .approve { background: var(--accent-color); color: var(--button-text); }
.reject { color: var(--danger-color); border-color: var(--danger-color); }
.request-card { max-width: 1100px; margin: 0 auto 14px; padding: 16px; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; }
.request-header div { display: flex; flex-direction: column; }
.request-header span, .empty { color: var(--text-secondary); }
.changes { margin: 14px 0; border-top: 1px solid var(--border-color); }
.change-row { display: grid; grid-template-columns: 180px 1fr 24px 1fr; gap: 10px; padding: 10px 0; border-bottom: 1px solid var(--border-color); overflow-wrap: anywhere; }
textarea { width: 100%; min-height: 70px; padding: 9px; background: var(--input-bg); color: var(--text-primary); border: 1px solid var(--input-border); }
.actions { justify-content: flex-end; margin-top: 10px; }
.empty { max-width: 1100px; margin: 30px auto; text-align: center; }
@media (max-width: 700px) { .change-row { grid-template-columns: 1fr; } header { align-items: flex-start; flex-direction: column; } }
</style>
