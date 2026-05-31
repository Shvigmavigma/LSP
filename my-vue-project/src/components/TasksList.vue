<template>
  <div class="tasks-list">
    <template v-if="hasActiveTasks">
      <div v-if="inProgressTasks.length > 0" class="task-group">
        <h4 class="task-group-title in-progress-title">{{ $t('projectDetails.inProgress') }}</h4>
        <div class="task-tree">
          <TaskCard
            v-for="task in inProgressTasks"
            :key="task.title || task.id"
            :task="task"
            :is-readonly="isReadonly"
            :get-user-nickname="getUserNickname"
            @click="$emit('goToTask', task)"
          />
        </div>
      </div>
      
      <div v-if="waitingTasks.length > 0" class="task-group">
        <h4 class="task-group-title waiting-title">{{ $t('projectDetails.waiting') }}</h4>
        <div class="task-tree">
          <TaskCard
            v-for="task in waitingTasks"
            :key="task.title || task.id"
            :task="task"
            :is-readonly="isReadonly"
            :get-user-nickname="getUserNickname"
            @click="$emit('goToTask', task)"
          />
        </div>
      </div>
    </template>
    <div v-else class="no-tasks">{{ $t('projectDetails.noActiveTasks') }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { Task } from '@/types';
import TaskCard from './TaskCard.vue';

const props = defineProps<{
  tasks: Task[];
  isReadonly?: boolean;
  getUserNickname: (id: number) => string;
}>();

const emit = defineEmits<{
  (e: 'goToTask', task: Task): void;
}>();

const inProgressTasks = computed(() => 
  props.tasks?.filter(t => t.status === 'в работе') || []
);

const waitingTasks = computed(() => 
  props.tasks?.filter(t => t.status === 'ожидает') || []
);

const hasActiveTasks = computed(() => 
  inProgressTasks.value.length > 0 || waitingTasks.value.length > 0
);
</script>

<style scoped>
.task-group { margin-bottom: 30px; }
.task-group-title { font-size: 1.2rem; font-weight: 600; margin-bottom: 15px; padding-bottom: 5px; border-bottom: 2px solid; }
.task-group-title.in-progress-title { color: var(--accent-color); border-bottom-color: var(--accent-color); }
.task-group-title.waiting-title { color: #ff9800; border-bottom-color: #ff9800; }
.task-tree { display: flex; flex-direction: column; gap: 15px; }
.no-tasks { text-align: center; color: var(--text-secondary); padding: 40px; }
</style>