<template>
  <form @submit.prevent="onSubmit">
    <label>{{ $t('projectForm.titleLabel') }}</label>
    <input v-model="localForm.title" required />

    <label>{{ $t('projectForm.bodyLabel') }}</label>
    <textarea v-model="localForm.body" required></textarea>

    <label>{{ $t('projectForm.underbodyLabel') }}</label>
    <textarea v-model="localForm.underbody"></textarea>

    <label>{{ $t('projectForm.tasksLabel') }}</label>
    <textarea
      v-model="tasksText"
      :placeholder="$t('projectForm.tasksPlaceholder')"
    ></textarea>

    <button type="submit">
      {{ isEdit ? $t('common.save') : $t('common.create') }}
    </button>
  </form>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import type { Project, Task } from '@/types';

const { t } = useI18n();

const props = defineProps<{
  initialData?: Project | null;
  isEdit: boolean;
}>();

const emit = defineEmits<{
  (e: 'submit', data: any): void;
}>();

const localForm = ref<{
  title: string;
  body: string;
  underbody: string;
  tasks: Task[];
}>({
  title: '',
  body: '',
  underbody: '',
  tasks: [],
});

watch(() => props.initialData, (val) => {
  if (val) {
    localForm.value = {
      title: val.title,
      body: val.body,
      underbody: val.underbody,
      tasks: val.tasks,
    };
    tasksText.value = JSON.stringify(val.tasks || [], null, 2);
  }
}, { immediate: true });

const tasksText = ref('[]');

const onSubmit = () => {
  try {
    const tasks = JSON.parse(tasksText.value) as Task[];
    const submitData = {
      ...localForm.value,
      tasks,
    };
    emit('submit', submitData);
  } catch (e) {
    alert(t('projectForm.jsonError'));
  }
};
</script>

<style scoped>
form { display: flex; flex-direction: column; max-width: 600px; margin: 0 auto; }
label { margin-top: 1rem; }
input, textarea { padding: 0.5rem; }
textarea { min-height: 100px; }
button { margin-top: 1rem; padding: 0.5rem; background: #42b983; color: white; border: none; cursor: pointer; }
</style>