<template>
  <form @submit.prevent="onSubmit">
    <label>Название</label>
    <input v-model="localForm.title" required />

    <label>Описание (body)</label>
    <textarea v-model="localForm.body" required></textarea>

    <label>Дополнительно (underbody)</label>
    <textarea v-model="localForm.underbody"></textarea>

    <label>Задачи (JSON)</label>
    <textarea v-model="tasksText" placeholder='[{"title": "...", "status": "...", "body": "...", "timeline": "..."}]'></textarea>

    <button type="submit">{{ isEdit ? 'Сохранить' : 'Создать' }}</button>
  </form>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import type { Project, Task } from '@/types';

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
  tasks: [], // теперь тип tasks — Task[], а не never[]
});

// При редактировании заполняем форму данными проекта
watch(() => props.initialData, (val) => {
  if (val) {
    localForm.value = {
      title: val.title,
      body: val.body,
      underbody: val.underbody,
      tasks: val.tasks, // val.tasks имеет тип Task[]
    };
    tasksText.value = JSON.stringify(val.tasks || [], null, 2);
  }
}, { immediate: true });

const tasksText = ref('[]');

const onSubmit = () => {
  try {
    const tasks = JSON.parse(tasksText.value) as Task[]; // Приводим к Task[]
    const submitData = {
      ...localForm.value,
      tasks,
    };
    emit('submit', submitData);
  } catch (e) {
    alert('Ошибка в JSON задач. Проверьте формат.');
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