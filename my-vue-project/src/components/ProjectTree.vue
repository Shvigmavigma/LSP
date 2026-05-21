<template>
  <div class="project-tree-wrapper">
    <div class="project-tree" :class="{ collapsed: isCollapsed }">
      <div class="tree-header">
        <button 
          v-if="isCollapsed" 
          class="expand-sidebar-btn" 
          @click="toggleCollapse" 
          :title="$t('projectTree.expandSidebar')"
        >
          ▶
        </button>
        <template v-else>
          <button class="collapse-btn" @click="toggleCollapse" :title="$t('projectTree.toggleSidebar')">
            ◀
          </button>
          <div class="tree-controls">
            <button class="expand-all-btn" @click="expandAll" :title="$t('projectTree.expandAll')">▼</button>
            <button class="collapse-all-btn" @click="collapseAll" :title="$t('projectTree.collapseAll')">▲</button>
          </div>
        </template>
      </div>

      <div v-if="!isCollapsed" class="tree-content">
        <div class="tree-node project-node">
          <div class="node-content" @click="goToProject">
            <span class="expand-icon" @click.stop="toggleProjectExpanded">
              {{ projectExpanded ? '▼' : '▶' }}
            </span>
            <span class="node-title">{{ project.title }}</span>
          </div>

          <div v-show="projectExpanded" class="children-container">
            <div
              v-for="(task, taskIndex) in tasks"
              :key="task.id || taskIndex"
              class="tree-node task-node"
              :class="{ 
                'drag-over': dragOverTaskIndex === taskIndex,
                'status-in-progress': task.status === 'в работе',
                'status-waiting': task.status === 'ожидает',
                'status-completed': task.status === 'выполнена'
              }"
              draggable="true"
              @dragstart="handleTaskDragStart($event, task, taskIndex)"
              @dragend="handleDragEnd"
              @dragover.prevent="handleDragOver($event, taskIndex)"
              @dragleave="handleDragLeave"
              @drop="handleTaskDrop($event, taskIndex)"
            >
              <div class="node-content" @click="goToTask(taskIndex)">
                <span class="expand-icon" @click.stop="toggleTaskExpanded(taskIndex)">
                  {{ isTaskExpanded(taskIndex) ? '▼' : '▶' }}
                </span>
                <span class="node-title">{{ task.title }}</span>
                <span class="task-status-badge" :class="task.status">
                  {{ getTaskStatusText(task.status) }}
                </span>
              </div>

              <div v-show="isTaskExpanded(taskIndex)" class="children-container subtasks-container">
                <div
                  v-for="(subtask, subtaskIndex) in task.subtasks"
                  :key="subtask.id"
                  class="tree-node subtask-node static"
                >
                  <div class="node-content">
                    <span class="subtask-indicator" :class="{ completed: subtask.completed }"></span>
                    <span class="node-title" :class="{ completed: subtask.completed }">
                      {{ subtask.title }}
                    </span>
                    <span v-if="subtask.progressPercent" class="subtask-percent">
                      {{ subtask.progressPercent }}%
                    </span>
                  </div>
                </div>
                <div v-if="!task.subtasks?.length" class="empty-subtasks">
                  {{ $t('projectTree.noSubtasks') }}
                </div>
              </div>
            </div>
            <div v-if="tasks.length === 0" class="empty-tasks">
              {{ $t('projectTree.noTasks') }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import type { Task } from '@/types';

const { t } = useI18n();
const router = useRouter();
const route = useRoute();

const props = defineProps<{
  project: {
    id: number;
    title: string;
    tasks: Task[];
  };
  projectId?: number;
}>();

const emit = defineEmits<{
  (e: 'task-moved', fromIndex: number, toIndex: number): void;
  (e: 'update-tasks', tasks: Task[]): void;
}>();

const isCollapsed = ref(false);
const projectExpanded = ref(true);
const expandedTasks = ref<Set<number>>(new Set());

const dragStartTaskIndex = ref<number | null>(null);
const dragOverTaskIndex = ref<number | null>(null);
const isMoving = ref(false);

// Initialize all tasks as expanded
props.project.tasks.forEach((_, index) => {
  expandedTasks.value.add(index);
});

const isTaskExpanded = (taskIndex: number): boolean => {
  return expandedTasks.value.has(taskIndex);
};

const toggleTaskExpanded = (taskIndex: number) => {
  if (expandedTasks.value.has(taskIndex)) {
    expandedTasks.value.delete(taskIndex);
  } else {
    expandedTasks.value.add(taskIndex);
  }
};

const expandAll = () => {
  projectExpanded.value = true;
  props.project.tasks.forEach((_, index) => {
    expandedTasks.value.add(index);
  });
};

const collapseAll = () => {
  expandedTasks.value.clear();
};

const toggleProjectExpanded = () => {
  projectExpanded.value = !projectExpanded.value;
};

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value;
};

const goToProject = () => {
  router.push(`/project/${props.project.id}`);
};

const goToTask = (taskIndex: number) => {
  const task = props.project.tasks[taskIndex];
  if (!task) return;
  
  // Используем task.id если доступен, иначе taskIndex
  const taskIdentifier = task.id || taskIndex;
  
  // Формируем целевой путь
  const targetPath = `/project/${props.project.id}/task/${taskIdentifier}`;
  
  // Проверяем, совпадает ли текущий путь с целевым
  if (route.path === targetPath) {
    // Если путь тот же самый, используем query параметр для принудительного обновления
    router.push({
      path: targetPath,
      query: { ...route.query, _t: Date.now().toString() }
    });
  } else {
    // Если путь отличается, просто переходим
    router.push(targetPath);
  }
};

const handleTaskDragStart = (event: DragEvent, task: Task, taskIndex: number) => {
  if (isMoving.value) {
    event.preventDefault();
    return false;
  }
  dragStartTaskIndex.value = taskIndex;
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/plain', JSON.stringify({
      type: 'task',
      taskIndex,
      taskTitle: task.title
    }));
  }
};

const handleDragEnd = () => {
  setTimeout(() => {
    dragStartTaskIndex.value = null;
    dragOverTaskIndex.value = null;
    isMoving.value = false;
  }, 100);
};

const handleDragOver = (event: DragEvent, taskIndex: number) => {
  event.preventDefault();
  if (dragOverTaskIndex.value !== taskIndex) {
    dragOverTaskIndex.value = taskIndex;
  }
};

const handleDragLeave = () => {
  dragOverTaskIndex.value = null;
};

const handleTaskDrop = async (event: DragEvent, targetTaskIndex: number) => {
  event.preventDefault();
  
  const data = JSON.parse(event.dataTransfer?.getData('text/plain') || '{}');
  
  if (data.type === 'task' && dragStartTaskIndex.value !== null && dragStartTaskIndex.value !== targetTaskIndex) {
    isMoving.value = true;
    emit('task-moved', dragStartTaskIndex.value, targetTaskIndex);
    
    const tasksCopy = [...props.project.tasks];
    const [movedTask] = tasksCopy.splice(dragStartTaskIndex.value, 1);
    tasksCopy.splice(targetTaskIndex, 0, movedTask);
    emit('update-tasks', tasksCopy);
  }
  
  setTimeout(() => {
    dragStartTaskIndex.value = null;
    dragOverTaskIndex.value = null;
    isMoving.value = false;
  }, 100);
};

const getTaskStatusText = (status: string): string => {
  switch (status) {
    case 'в работе': return t('projectTree.inProgress');
    case 'ожидает': return t('projectTree.waiting');
    case 'выполнена': return t('projectTree.completed');
    default: return status;
  }
};

const tasks = computed(() => props.project.tasks || []);
</script>

<style scoped>
.project-tree-wrapper {
  position: fixed;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  z-index: 100;
}

.project-tree {
  background: transparent;
}

.tree-header {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 4px;
  background: transparent;
}

.expand-sidebar-btn {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  cursor: pointer;
  padding: 8px 10px;
  border-radius: 0 8px 8px 0;
  font-size: 12px;
  transition: all 0.2s;
}

.expand-sidebar-btn:hover {
  color: var(--accent-color);
  border-color: var(--accent-color);
  background: var(--bg-card);
}

.collapse-btn {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  cursor: pointer;
  padding: 6px 8px;
  border-radius: 0 6px 6px 0;
  font-size: 10px;
  transition: all 0.2s;
}

.collapse-btn:hover {
  color: var(--accent-color);
  border-color: var(--accent-color);
}

.tree-controls {
  display: flex;
  gap: 2px;
  padding: 4px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-card);
}

.expand-all-btn,
.collapse-all-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 4px;
  font-size: 9px;
  transition: all 0.2s;
}

.expand-all-btn:hover,
.collapse-all-btn:hover {
  color: var(--accent-color);
  background: rgba(66, 185, 131, 0.1);
}

.tree-content {
  background: var(--bg-card);
  border-radius: 0 12px 12px 0;
  border: 1px solid var(--border-color);
  border-left: none;
  padding: 12px;
  width: 280px;
  max-height: 70vh;
  overflow-y: auto;
  font-size: 12px;
  box-shadow: var(--shadow);
}

.tree-content::-webkit-scrollbar {
  width: 4px;
}

.tree-content::-webkit-scrollbar-track {
  background: var(--bg-page);
  border-radius: 2px;
}

.tree-content::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 2px;
}

.tree-content::-webkit-scrollbar-thumb:hover {
  background: var(--accent-color);
}

.tree-node {
  margin-left: 0;
  user-select: none;
}

.project-node > .node-content {
  padding: 8px 6px;
  cursor: pointer;
  font-weight: 600;
  color: var(--heading-color);
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 6px;
}

.node-content {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 6px;
  border-radius: 4px;
  cursor: pointer;
  color: var(--text-primary);
  transition: all 0.2s;
}

.node-content:hover {
  background: var(--bg-page);
}

/* Убираем pointer cursor для подзадач */
.subtask-node.static .node-content {
  cursor: default;
}

.subtask-node.static .node-content:hover {
  background: transparent;
}

.expand-icon {
  font-size: 7px;
  width: 10px;
  cursor: pointer;
  color: var(--text-secondary);
}

.expand-icon:hover {
  color: var(--accent-color);
}

.node-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  color: #1976D2; /* Синий цвет для светлой темы */
}

.node-title.completed {
  text-decoration: line-through;
  opacity: 0.5;
}

.task-status-badge {
  font-size: 9px;
  padding: 2px 6px;
  border-radius: 10px;
  font-weight: 500;
  white-space: nowrap;
}

/* Убираем фон у статусов задач */
.task-status-badge.в\ работы,
.task-status-badge.in-progress {
  color: #1976D2; /* Синий */
}

.task-status-badge.ожидает,
.task-status-badge.waiting {
  color: #1976D2; /* Синий */
}

.task-status-badge.выполнена,
.task-status-badge.completed {
  color: #1976D2; /* Синий */
}

.children-container {
  margin-left: 14px;
  padding-left: 8px;
  border-left: 1px solid var(--border-color);
}

.subtasks-container {
  margin-left: 14px;
}

.task-node {
  margin-bottom: 2px;
  cursor: grab;
}

.task-node.drag-over {
  background: rgba(66, 185, 131, 0.1);
  border-radius: 4px;
  border: 1px dashed var(--accent-color);
}

.task-node:active {
  cursor: grabbing;
}

.task-node.status-in-progress .node-title,
.task-node.status-waiting .node-title,
.task-node.status-completed .node-title {
  color: #1976D2; /* Синий для статусов задач в светлой теме */
}

.task-node.status-completed .node-title {
  text-decoration: line-through;
  opacity: 0.6;
}

.subtask-node {
  margin-bottom: 1px;
}

.subtask-node.static {
  cursor: default;
}

.subtask-node .node-content {
  padding: 3px 6px;
}

.subtask-indicator {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--text-secondary);
  display: inline-block;
}

.subtask-indicator.completed {
  background: #1976D2; /* Синий для выполненной подзадачи */
}

.subtask-percent {
  font-size: 9px;
  color: #1976D2; /* Синий для процентов */
  padding: 1px 4px;
  border-radius: 8px;
}

.empty-tasks,
.empty-subtasks {
  text-align: center;
  color: var(--text-secondary);
  font-style: italic;
  padding: 10px;
  font-size: 10px;
}

/* Темная тема */
.dark-theme .tree-content {
  background: rgba(45, 55, 72, 0.95);
  border-color: rgba(255, 255, 255, 0.1);
}

.dark-theme .expand-sidebar-btn,
.dark-theme .collapse-btn,
.dark-theme .tree-controls {
  background: rgba(45, 55, 72, 0.95);
  border-color: rgba(255, 255, 255, 0.1);
}

.dark-theme .node-content:hover {
  background: rgba(255, 255, 255, 0.05);
}

/* Отключаем hover для статичных подзадач в темной теме */
.dark-theme .subtask-node.static .node-content:hover {
  background: transparent;
}

/* Желтые цвета для темной темы */
.dark-theme .node-title {
  color: #FFD700; /* Золотой/желтый для названий задач и подзадач */
}

.dark-theme .task-node.status-in-progress .node-title,
.dark-theme .task-node.status-waiting .node-title,
.dark-theme .task-node.status-completed .node-title {
  color: #FFD700; /* Желтый для статусов задач */
}

.dark-theme .task-node.status-completed .node-title {
  text-decoration: line-through;
  opacity: 0.6;
}

/* Убираем фон у статусов в темной теме */
.dark-theme .task-status-badge.в\ работы,
.dark-theme .task-status-badge.in-progress,
.dark-theme .task-status-badge.ожидает,
.dark-theme .task-status-badge.waiting,
.dark-theme .task-status-badge.выполнена,
.dark-theme .task-status-badge.completed {
  color: #FFD700; /* Желтый */
}

.dark-theme .subtask-indicator.completed {
  background: #FFD700; /* Желтый */
}

.dark-theme .subtask-percent {
  color: #FFD700;
}
</style>