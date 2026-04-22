<template>
  <div class="old-projects-page">
    <header class="page-header">
      <h1>{{ $t('navigation.old_projects') }}</h1>
      <div class="header-buttons">
        <ThemeToggle />
        <LanguageSwitcher />
        <HomeButton/>
      </div>
    </header>

    <div v-if="loading" class="loading">{{ $t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="projects-grid">
      <div
        v-for="project in projects"
        :key="project.id"
        class="project-card"
        @click="goToProject(project.id)"
      >
        <h3>{{ project.title }}</h3>
        <p class="project-body">{{ project.body?.slice(0, 150) }}...</p>
        <div class="project-meta">
          <span class="participants-count">{{ project.participants?.length || 0 }} {{ $t('projectDetails.participants') }}</span>
          <span class="old-badge" v-if="project.is_old">{{ $t('projectDetails.oldProject') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import axios from 'axios';
import ThemeToggle from '@/components/ThemeToggle.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';
import type { Project } from '@/types';
import HomeButton from '@/components/HomeButton.vue';

const { t } = useI18n();
const router = useRouter();
const projects = ref<Project[]>([]);
const loading = ref(true);
const error = ref('');

const fetchOldProjects = async () => {
  try {
    const token = localStorage.getItem('access_token');
    const response = await axios.get('/projects/old', {
      headers: { Authorization: `Bearer ${token}` }
    });
    projects.value = response.data;
  } catch (err: any) {
    console.error(err);
    error.value = err.response?.data?.detail || t('common.error');
  } finally {
    loading.value = false;
  }
};

const goToProject = (id: number) => {
  router.push(`/project/${id}`);
};

const goHome = () => {
  router.push('/main');
};

onMounted(fetchOldProjects);
</script>

<style scoped>
.old-projects-page {
  min-height: 100vh;
  background: var(--bg-page);
  padding: 2rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.header-buttons {
  display: flex;
  gap: 10px;
  align-items: center;
}


.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.5rem;
}

.project-card {
  background: var(--bg-card);
  border-radius: 24px;
  padding: 1.5rem;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow);
}

.project-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-strong);
}

.project-card h3 {
  color: var(--heading-color);
  margin-bottom: 0.5rem;
}

.project-body {
  color: var(--text-primary);
  font-size: 0.9rem;
  margin-bottom: 1rem;
  line-height: 1.4;
}

.project-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.old-badge {
  background: #ff9800;
  color: white;
  padding: 2px 8px;
  border-radius: 20px;
}

.loading, .error {
  text-align: center;
  padding: 2rem;
  font-size: 1.2rem;
}
</style>