<template>
  <div class="user-search-filters">
    <select v-model="local.role">
      <option value="">{{ $t('allUsers.filterAll') }}</option>
      <option value="student">{{ $t('register.student') }}</option>
      <option value="teacher">{{ $t('register.teacher') }}</option>
      <option value="admin">{{ $t('register.admin') }}</option>
      <option value="curator">{{ $t('roles.curator') }}</option>
      <option value="customer">{{ $t('roles.customer') }}</option>
      <option value="supervisor">{{ $t('roles.supervisor') }}</option>
      <option value="expert">{{ $t('roles.expert') }}</option>
      <option value="executor">{{ $t('roles.executor') }}</option>
    </select>
    <input v-model.number="local.parallel" type="number" min="1" max="11" :placeholder="$t('adminDirections.parallel')" />
    <input v-model.number="local.class_grade" type="number" min="0" max="9" :placeholder="$t('adminDirections.class')" />
    <select v-model="local.direction_key">
      <option value="">{{ $t('adminDirections.all') }}</option>
      <option v-for="direction in directions" :key="direction.key" :value="direction.key">
        {{ direction.label }}
      </option>
    </select>
    <select v-model="local.sort_by">
      <option value="fullname">{{ $t('adminDirections.sort') }}: {{ $t('adminUsers.table.fullname') }}</option>
      <option value="role">{{ $t('adminUsers.table.type') }}</option>
      <option value="parallel">{{ $t('adminDirections.parallel') }}</option>
      <option value="class">{{ $t('adminDirections.class') }}</option>
      <option value="direction">{{ $t('adminDirections.direction') }}</option>
    </select>
    <select v-model="local.sort_order">
      <option value="asc">A-Z</option>
      <option value="desc">Z-A</option>
    </select>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue';
import api from '@/utils/api';

export interface UserSearchFilterValue {
  role?: string;
  class_grade?: number | null;
  parallel?: number | null;
  direction_key?: string;
  sort_by?: string;
  sort_order?: string;
}

const props = withDefaults(defineProps<{ modelValue?: UserSearchFilterValue }>(), {
  modelValue: () => ({})
});
const emit = defineEmits<{
  (event: 'update:modelValue', value: UserSearchFilterValue): void;
  (event: 'change'): void;
}>();

const directions = ref<Array<{ key: string; label: string }>>([]);
const local = reactive<UserSearchFilterValue>({
  role: props.modelValue.role || '',
  class_grade: props.modelValue.class_grade ?? null,
  parallel: props.modelValue.parallel ?? null,
  direction_key: props.modelValue.direction_key || '',
  sort_by: props.modelValue.sort_by || 'fullname',
  sort_order: props.modelValue.sort_order || 'asc'
});

watch(local, () => {
  emit('update:modelValue', { ...local });
  emit('change');
});

onMounted(async () => {
  const response = await api.get('/user-directions');
  directions.value = response.data.directions || [];
});
</script>

<style scoped>
.user-search-filters {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin: 8px 0 12px;
}

select,
input {
  min-width: 0;
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-primary);
}

@media (max-width: 700px) {
  .user-search-filters {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
