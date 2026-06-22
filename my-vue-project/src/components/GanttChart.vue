<template>
  <div class="gantt-wrapper">
    <div class="gantt-header">
      <h3>{{ title }}</h3>
      <div class="controls">
        <button class="zoom-btn" @click="zoomOut" :title="t('projectDetails.gantt.zoomOut')" :aria-label="t('projectDetails.gantt.zoomOut')" :disabled="dayWidth <= 20">−</button>
        <span class="zoom-level">{{ Math.round(dayWidth / 40 * 100) }}%</span>
        <button class="zoom-btn" @click="zoomIn" :title="t('projectDetails.gantt.zoomIn')" :aria-label="t('projectDetails.gantt.zoomIn')" :disabled="dayWidth >= 120">+</button>
        <button class="expand-btn" @click="expanded = !expanded" :aria-expanded="expanded">
          {{ expanded ? t('projectDetails.gantt.collapse') : t('projectDetails.gantt.expand') }}
        </button>
      </div>
    </div>
    <div v-if="expanded" class="gantt-container" ref="ganttContainer" @wheel.prevent="handleWheel">
      <div class="gantt-chart" :style="{ minWidth: timelineWidth + 'px' }">
        <!-- Заголовки дат -->
        <div class="gantt-header-row">
          <div class="gantt-label">{{ t('projectDetails.gantt.task') }}</div>
          <div class="gantt-timeline" :style="{ width: timelineWidth + 'px' }">
            <div
              v-for="(date, idx) in dateHeaders"
              :key="date.iso"
              class="date-header"
              :class="{ weekend: date.isWeekend, today: date.isToday }"
              :style="{ left: idx * dayWidth + 'px', width: dayWidth + 'px' }"
            >
              {{ date.label }}
            </div>
          </div>
        </div>
        <div v-if="displayTasks.length === 0" class="gantt-empty">
          {{ t('projectDetails.gantt.noTasks') }}
        </div>
        <!-- Строки задач -->
        <div
          v-for="task in displayTasks"
          :key="task.key"
          class="gantt-row"
          :class="{ 'task-disabled': !task.editable || readonly }"
        >
          <div class="gantt-label" :title="task.title">
            {{ task.title }}
          </div>
          <div class="gantt-timeline" :style="{ width: timelineWidth + 'px' }">
            <div
              class="gantt-bar"
              :style="{
                left: startOffset(task.start) + 'px',
                width: barWidth(task.start, task.end) + 'px',
                backgroundColor: task.barColor
              }"
              :class="{ dragging: draggingTaskId === task.id }"
              @mousedown="!readonly && startDrag(task, $event)"
              @touchstart="!readonly && startDrag(task, $event)"
            >
              <!-- Ресайз справа (только если не readonly) -->
              <div
                v-if="!readonly"
                class="resize-handle right"
                @mousedown.stop="startResize(task, 'right', $event)"
                @touchstart.stop="startResize(task, 'right', $event)"
              ></div>
              <!-- Ресайз слева (только если не readonly) -->
              <div
                v-if="!readonly"
                class="resize-handle left"
                @mousedown.stop="startResize(task, 'left', $event)"
                @touchstart.stop="startResize(task, 'left', $event)"
              ></div>
              <span class="bar-text">{{ task.barText }}</span>
            </div>
          </div>
        </div>
        <!-- Вертикальная линия сегодняшнего дня -->
        <div
          v-if="todayOffset !== null"
          class="today-line"
          :style="{ left: (200 + todayOffset) + 'px' }"
        ></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue';
import { useEventListener } from '@vueuse/core';
import { useI18n } from 'vue-i18n';
import type { Task } from '@/types';
import { parseDate, formatDate } from '@/utils/dateUtils';

const props = defineProps<{
  tasks: Task[];
  title: string;
  readonly?: boolean; // новый проп – отключает редактирование
}>();

const { t } = useI18n();

const emit = defineEmits<{
  (e: 'update-tasks', payload: { task: Task; index: number }): void;
}>();

const expanded = ref(true);
const dayWidth = ref(40);
const ganttContainer = ref<HTMLElement | null>(null);

// Состояния drag & drop
const draggingTaskId = ref<string | null>(null);
const dragStartX = ref(0);
const originalStart = ref<Date | null>(null);
const originalEnd = ref<Date | null>(null);
const resizeDirection = ref<'left' | 'right' | null>(null);
const draggingTaskTemp = ref<{ start: Date; end: Date } | null>(null);

// Вспомогательная функция для получения цвета и текста статуса
function getTaskVisuals(status: string, start: Date, end: Date, title: string) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const now = today.getTime();
  const startTime = start.getTime();
  const endTime = end.getTime();

  if (status === 'выполнена') {
    return {
      barColor: '#4caf50',
      barText: `${title} (выполнена)`
    };
  }

  if (now > endTime) {
    return {
      barColor: '#9e9e9e',
      barText: `${title} (просрочена)`
    };
  }

  if (now < startTime) {
    return {
      barColor: '#4caf50',
      barText: `${title} (не начата)`
    };
  }

  const totalDuration = endTime - startTime;
  const elapsed = now - startTime;
  const progress = elapsed / totalDuration;

  let barColor = '#4caf50';
  if (progress > 0.8) barColor = '#f44336';
  else if (progress > 0.5) barColor = '#ff9800';

  let statusText = '';
  if (status && status !== '') statusText = ` (${status})`;
  else statusText = ' (в процессе)';

  return {
    barColor,
    barText: `${title}${statusText}`
  };
}

const tasksWithDates = computed(() => {
  return props.tasks
    .map((task, idx) => {
      let start = null, end = null;
      if (task.timeline && task.timelinend) {
        start = parseDate(task.timeline);
        end = parseDate(task.timelinend);
      } else if (task.timeline && task.timeline.includes('-')) {
        const parts = task.timeline.split('-');
        start = parseDate(parts[0]);
        end = parseDate(parts[1]);
      } else if (task.timeline) {
        start = parseDate(task.timeline);
        end = start;
      }
      if (!start || !end) return null;

      const visual = getTaskVisuals(task.status, start, end, task.title);
      const uniqueId = task.id || task.title;
      const isCompleted = task.status === 'выполнена';
      const editable = true; // в режиме readonly будет заблокировано через проп

      return {
        id: uniqueId,
        title: task.title,
        start,
        end,
        editable,
        barColor: visual.barColor,
        barText: visual.barText,
        originalIndex: idx,
        key: `${uniqueId}-${start.getTime()}-${end.getTime()}`,
      };
    })
    .filter(t => t !== null);
});

const displayTasks = computed(() => {
  if (!draggingTaskId.value || !draggingTaskTemp.value) {
    return tasksWithDates.value;
  }
  return tasksWithDates.value.map(task => {
    if (task.id === draggingTaskId.value) {
      const newStart = draggingTaskTemp.value!.start;
      const newEnd = draggingTaskTemp.value!.end;
      const originalTask = props.tasks.find(t => (t.id || t.title) === task.id);
      if (originalTask) {
        const visual = getTaskVisuals(originalTask.status, newStart, newEnd, originalTask.title);
        return {
          ...task,
          start: newStart,
          end: newEnd,
          barColor: visual.barColor,
          barText: visual.barText,
        };
      }
      return {
        ...task,
        start: newStart,
        end: newEnd,
      };
    }
    return task;
  });
});

const allTasksForRange = computed(() => {
  const base = tasksWithDates.value;
  if (!draggingTaskId.value || !draggingTaskTemp.value) return base;
  return base.map(task => {
    if (task.id === draggingTaskId.value) {
      return { ...task, start: draggingTaskTemp.value!.start, end: draggingTaskTemp.value!.end };
    }
    return task;
  });
});

const dateRange = computed(() => {
  const dates = allTasksForRange.value.flatMap(t => [t.start, t.end]).filter(d => d);
  if (dates.length === 0) return { start: new Date(), end: new Date() };
  let min = new Date(Math.min(...dates.map(d => d.getTime())));
  let max = new Date(Math.max(...dates.map(d => d.getTime())));
  min.setDate(min.getDate() - 2);
  max.setDate(max.getDate() + 2);
  return { start: min, end: max };
});

const dateHeaders = computed(() => {
  const start = dateRange.value.start;
  const end = dateRange.value.end;
  const headers: Array<{ label: string; iso: string; isWeekend: boolean; isToday: boolean }> = [];
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const current = new Date(start);
  while (current <= end) {
    headers.push({
      label: `${current.getDate()}.${current.getMonth() + 1}`,
      iso: current.toISOString(),
      isWeekend: current.getDay() === 0 || current.getDay() === 6,
      isToday: current.getTime() === today.getTime(),
    });
    current.setDate(current.getDate() + 1);
  }
  return headers;
});

const timelineWidth = computed(() => dateHeaders.value.length * dayWidth.value);

const todayOffset = computed(() => {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const startDate = dateRange.value.start;
  if (today < startDate || today > dateRange.value.end) return null;
  const diffDays = Math.floor((today.getTime() - startDate.getTime()) / (1000 * 3600 * 24));
  return diffDays * dayWidth.value;
});

function startOffset(start: Date): number {
  const startDate = dateRange.value.start;
  const diffDays = Math.floor((start.getTime() - startDate.getTime()) / (1000 * 3600 * 24));
  return Math.max(0, diffDays * dayWidth.value);
}

function barWidth(start: Date, end: Date): number {
  const diffDays = Math.floor((end.getTime() - start.getTime()) / (1000 * 3600 * 24));
  return Math.max(dayWidth.value, diffDays * dayWidth.value);
}

function zoomIn() {
  dayWidth.value = Math.min(120, dayWidth.value + 5);
}
function zoomOut() {
  dayWidth.value = Math.max(20, dayWidth.value - 5);
}
function handleWheel(e: WheelEvent) {
  if (e.ctrlKey) {
    if (e.deltaY < 0) zoomIn();
    else zoomOut();
    e.preventDefault();
  }
}

function startDrag(task: any, event: MouseEvent | TouchEvent) {
  if (!task.editable || props.readonly) return;
  event.preventDefault();
  draggingTaskId.value = task.id;
  const clientX = 'touches' in event ? event.touches[0].clientX : event.clientX;
  dragStartX.value = clientX;
  originalStart.value = new Date(task.start);
  originalEnd.value = new Date(task.end);
  draggingTaskTemp.value = { start: new Date(task.start), end: new Date(task.end) };
}

function startResize(task: any, direction: 'left' | 'right', event: MouseEvent | TouchEvent) {
  if (!task.editable || props.readonly) return;
  event.stopPropagation();
  event.preventDefault();
  draggingTaskId.value = task.id;
  resizeDirection.value = direction;
  const clientX = 'touches' in event ? event.touches[0].clientX : event.clientX;
  dragStartX.value = clientX;
  originalStart.value = new Date(task.start);
  originalEnd.value = new Date(task.end);
  draggingTaskTemp.value = { start: new Date(task.start), end: new Date(task.end) };
}

function onMouseMove(event: MouseEvent | TouchEvent) {
  if (!draggingTaskId.value || !draggingTaskTemp.value) return;
  const task = tasksWithDates.value.find(t => t.id === draggingTaskId.value);
  if (!task) return;
  const clientX = 'touches' in event ? event.touches[0].clientX : event.clientX;
  const deltaX = clientX - dragStartX.value;
  const deltaDays = Math.round(deltaX / dayWidth.value);
  if (deltaDays === 0) return;

  let newStart = new Date(originalStart.value!);
  let newEnd = new Date(originalEnd.value!);
  if (resizeDirection.value === 'right') {
    newEnd.setDate(newEnd.getDate() + deltaDays);
    if (newEnd <= newStart) return;
  } else if (resizeDirection.value === 'left') {
    newStart.setDate(newStart.getDate() + deltaDays);
    if (newStart >= newEnd) return;
  } else {
    newStart.setDate(newStart.getDate() + deltaDays);
    newEnd.setDate(newEnd.getDate() + deltaDays);
  }
  draggingTaskTemp.value = { start: newStart, end: newEnd };
}

function onMouseUp() {
  if (draggingTaskId.value && draggingTaskTemp.value) {
    const taskWithId = tasksWithDates.value.find(t => t.id === draggingTaskId.value);
    if (taskWithId) {
      const originalTask = props.tasks.find(t => (t.id || t.title) === draggingTaskId.value);
      if (originalTask) {
        const updatedTask: Task = {
          ...originalTask,
          timeline: formatDate(draggingTaskTemp.value.start),
          timelinend: formatDate(draggingTaskTemp.value.end),
        };
        emit('update-tasks', { task: updatedTask, index: taskWithId.originalIndex });
      } else {
        console.warn('[Gantt] Original task not found by id:', draggingTaskId.value);
      }
    } else {
      console.warn('[Gantt] Task with id not found in tasksWithDates:', draggingTaskId.value);
    }
  }
  draggingTaskId.value = null;
  resizeDirection.value = null;
  originalStart.value = null;
  originalEnd.value = null;
  draggingTaskTemp.value = null;
}

const stopMouseMove = useEventListener('mousemove', onMouseMove);
const stopMouseUp = useEventListener('mouseup', onMouseUp);
const stopTouchMove = useEventListener('touchmove', onMouseMove);
const stopTouchEnd = useEventListener('touchend', onMouseUp);

onUnmounted(() => {
  stopMouseMove();
  stopMouseUp();
  stopTouchMove();
  stopTouchEnd();
});
</script>

<style scoped>
.gantt-wrapper {
  margin-top: 20px;
  border: 1px solid var(--border-color);
  background: var(--bg-card);
  border-radius: 12px;
  padding: 0;
  overflow: hidden;
  box-shadow: var(--shadow);
}
.gantt-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 0;
  padding: 16px 18px;
  border-bottom: 1px solid var(--border-color);
  flex-wrap: wrap;
  gap: 10px;
}
.gantt-header h3 {
  margin: 0;
  color: var(--heading-color);
  font-size: 1rem;
}
.controls {
  display: flex;
  gap: 6px;
  align-items: center;
  padding: 4px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--completed-bg);
}
.zoom-btn,
.expand-btn {
  min-height: 32px;
  border: 1px solid transparent;
  border-radius: 6px;
  background: transparent;
  color: var(--text-primary);
  cursor: pointer;
  font-weight: 700;
  transition: background-color 0.18s ease, color 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
}
.zoom-btn {
  width: 34px;
  padding: 0;
  font-size: 1.1rem;
}
.expand-btn {
  padding: 5px 12px;
}
.zoom-btn:hover:not(:disabled),
.expand-btn:hover {
  border-color: var(--accent-color);
  background: var(--accent-color);
  color: var(--button-text);
  box-shadow: var(--shadow);
}
.zoom-btn:active:not(:disabled),
.expand-btn:active {
  transform: translateY(0);
  box-shadow: none;
}
.zoom-btn:focus-visible,
.expand-btn:focus-visible {
  outline: 2px solid var(--accent-color);
  outline-offset: 2px;
}
.zoom-btn:disabled {
  opacity: 0.38;
  cursor: not-allowed;
}
.zoom-level {
  font-size: 0.85rem;
  color: var(--text-secondary);
  min-width: 48px;
  text-align: center;
}
.gantt-container {
  max-height: 520px;
  overflow: auto;
  position: relative;
  scrollbar-color: var(--accent-color) var(--completed-bg);
  scrollbar-width: thin;
}
.gantt-chart {
  display: table;
  width: 100%;
  position: relative;
}
.gantt-header-row,
.gantt-row {
  display: flex;
  border-bottom: 1px solid var(--border-color);
}
.gantt-header-row {
  min-height: 42px;
  background: var(--completed-bg);
  position: sticky;
  top: 0;
  z-index: 10;
}
.gantt-row {
  min-height: 46px;
  background: var(--bg-card);
  transition: background-color 0.18s ease;
}
.gantt-row:nth-child(odd) {
  background: var(--completed-bg);
}
.gantt-row:hover {
  background: var(--bg-page);
}
.gantt-label {
  width: 200px;
  flex: 0 0 200px;
  padding: 12px;
  font-weight: 500;
  color: var(--heading-color);
  border-right: 1px solid var(--border-color);
  background: inherit;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  position: sticky;
  left: 0;
  z-index: 6;
}
.gantt-header-row .gantt-label {
  z-index: 12;
  background: var(--completed-bg);
  font-weight: 700;
}
.gantt-timeline {
  position: relative;
  min-height: 46px;
  background: var(--bg-page);
  height: 100%;
}
.gantt-header-row .gantt-timeline {
  min-height: 42px;
}
.date-header {
  position: absolute;
  top: 0;
  text-align: center;
  font-size: 0.7rem;
  color: var(--text-secondary);
  height: 100%;
  padding: 12px 0;
  white-space: nowrap;
  border-left: 1px solid var(--border-color);
  box-sizing: border-box;
}
.date-header.weekend {
  background: color-mix(in srgb, var(--accent-color) 7%, transparent);
}
.date-header.today {
  color: var(--danger-color);
  font-weight: 800;
}
.gantt-bar {
  position: absolute;
  top: 4px;
  height: 32px;
  border-radius: 6px;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.32);
  transition: box-shadow 0.2s, transform 0.2s, filter 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 0.7rem;
  font-weight: 500;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  padding: 0 4px;
  z-index: 2;
}
.gantt-bar:hover {
  z-index: 4;
  filter: brightness(1.08);
  box-shadow: 0 5px 12px rgba(0,0,0,0.24);
}
.gantt-bar.dragging {
  opacity: 0.8;
  cursor: grabbing;
}
.resize-handle {
  position: absolute;
  top: 0;
  width: 10px;
  height: 100%;
  cursor: ew-resize;
  background: rgba(255,255,255,0.5);
}
.resize-handle.right {
  right: 0;
  border-radius: 0 6px 6px 0;
}
.resize-handle.left {
  left: 0;
  border-radius: 6px 0 0 6px;
}
.resize-handle:hover {
  background: rgba(255,255,255,0.8);
}
.task-disabled .gantt-bar {
  opacity: 0.72;
  cursor: default;
}
.task-disabled .gantt-bar:hover {
  transform: none;
}
.bar-text {
  font-size: 0.7rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
  padding: 0 4px;
}
.today-line {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background-color: #ff4444;
  z-index: 5;
  pointer-events: none;
  box-shadow: 0 0 4px rgba(255,68,68,0.5);
}
.gantt-empty {
  position: sticky;
  left: 0;
  width: 100%;
  padding: 30px 18px;
  color: var(--text-secondary);
  text-align: center;
  background: var(--bg-card);
}
</style>
