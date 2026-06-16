<template>
  <div class="lifecycle-dashboard">
    <header class="page-header">
      <h1>{{ $t('lifecycleDashboard.title') }}</h1>
      <div class="header-actions">
        <ThemeToggle />
        <LanguageSwitcher />
        <HomeButton />
      </div>
    </header>

    <div class="toolbar">
      <input v-model="search" :placeholder="$t('lifecycleDashboard.search')" @input="loadProjects" />
      <select v-model="classFilter" class="class-filter" @change="loadProjects">
        <option value="">{{ $t('lifecycleDashboard.allClasses') }}</option>
        <option value="8">8</option>
        <option value="9">9</option>
        <option value="10">10</option>
        <option value="11">11</option>
      </select>
    </div>

    <div v-if="loading" class="loading">{{ $t('common.loading') }}</div>
    <div v-else class="project-list">
      <article v-for="project in projects" :key="project.id" class="project-row" @click="router.push(`/project/${project.id}`)">
        <div class="project-main">
          <div class="project-title-line">
            <strong>{{ project.title }}</strong>
            <span v-if="project.is_old" class="old-project-badge">{{ $t('projectDetails.oldProject') }}</span>
          </div>
          <small v-if="project.class_key" class="class-badge">{{ $t('lifecycleDashboard.classLabel') }}: {{ project.class_key }}</small>
          <span>{{ project.body }}</span>
          <small>{{ $t('lifecycleDashboard.tasks', { count: project.tasks_count }) }}</small>
        </div>
        <div class="stage-strip">
          <span
            v-for="stage in schema.stages"
            :key="stage.id"
            class="stage-dot"
            :class="getStageStatus(project, stage.id)"
            :title="stage.title"
          >
            {{ stage.title }}
          </span>
        </div>
        <div v-if="project.pending_requests?.length" class="pending-requests">
          <strong>{{ $t('lifecycleDashboard.pendingRequests') }}</strong>
          <div v-for="request in project.pending_requests" :key="`${project.id}-${request.stage_id}`" class="pending-request">
            <span>{{ $t('lifecycleDashboard.requestedStage') }}: {{ request.stage_title }}</span>
            <span>{{ $t('lifecycleDashboard.requestedBy') }}: {{ request.requested_by_name || request.requested_by }}</span>
            <small v-if="request.comment">{{ request.comment }}</small>
          </div>
        </div>
      </article>
      <div v-if="projects.length === 0" class="empty">{{ $t('lifecycleDashboard.empty') }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import ThemeToggle from '@/components/ThemeToggle.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';
import HomeButton from '@/components/HomeButton.vue';
import api from '@/utils/api';

const router = useRouter();
const search = ref('');
const classFilter = ref('');
const loading = ref(false);
const schema = ref<{ stages: Array<{ id: string; title: string }> }>({ stages: [] });
const projects = ref<Array<any>>([]);
let searchTimer: number | null = null;

async function loadProjects() {
  if (searchTimer) window.clearTimeout(searchTimer);
  searchTimer = window.setTimeout(async () => {
    loading.value = true;
    try {
      const { data } = await api.get('/admin/lifecycle-projects', {
        params: {
          q: search.value || undefined,
          class_key: classFilter.value || undefined,
        },
      });
      schema.value = data.schema;
      projects.value = data.projects || [];
    } finally {
      loading.value = false;
    }
  }, 200);
}

function getStageStatus(project: any, stageId: string): string {
  return project.lifecycle_state?.stages?.find((stage: any) => stage.id === stageId)?.status || 'pending';
}

onMounted(loadProjects);
</script>

<style scoped>
.lifecycle-dashboard {
  min-height: 100vh;
  padding: 24px;
  background: var(--bg-page);
  color: var(--text-primary);
}
.page-header,
.header-actions,
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.toolbar {
  margin: 20px 0;
  justify-content: flex-start;
}
.toolbar input,
.toolbar select {
  width: min(620px, 100%);
  padding: 12px 14px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-primary);
}
.toolbar select {
  width: 180px;
}
.project-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.project-row {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) 2fr;
  gap: 18px;
  padding: 16px;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background: var(--bg-card);
  box-shadow: var(--shadow);
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.pending-requests {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  background: var(--bg-page);
}
.pending-requests > strong {
  color: var(--heading-color);
}
.pending-request {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  color: var(--text-secondary);
}
.pending-request small {
  flex-basis: 100%;
  color: var(--text-primary);
}
.project-row:hover {
  border-color: var(--accent-color);
  box-shadow: var(--shadow-strong);
}
.project-main {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.project-title-line {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.old-project-badge {
  padding: 4px 12px;
  border-radius: 20px;
  background: rgba(255, 152, 0, 0.14);
  color: #ff9800;
  border: 1px solid rgba(255, 152, 0, 0.35);
  font-size: 0.85rem;
  font-weight: 700;
}
.project-main span {
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.class-badge {
  width: fit-content;
  padding: 3px 8px;
  border-radius: 999px;
  background: var(--completed-bg);
  color: var(--heading-color);
  border: 1px solid var(--border-color);
}
.stage-strip {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow-x: auto;
}
.stage-dot {
  min-width: 110px;
  padding: 8px 10px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  text-align: center;
  font-size: 0.82rem;
  background: var(--bg-card);
  color: var(--text-primary);
}
.stage-dot.completed {
  background: var(--completed-bg);
  color: var(--text-primary);
  border-color: var(--accent-color);
}
.stage-dot.current,
.stage-dot.approval_pending {
  border-color: var(--accent-color);
  box-shadow: inset 0 0 0 1px var(--accent-color);
  font-weight: 700;
}
.stage-dot.rejected {
  background: var(--danger-bg);
  color: var(--danger-color);
  border-color: var(--danger-color);
}
.empty,
.loading {
  padding: 28px;
  text-align: center;
  opacity: 0.75;
}
@media (max-width: 760px) {
  .project-row {
    grid-template-columns: 1fr;
  }
}
</style>
