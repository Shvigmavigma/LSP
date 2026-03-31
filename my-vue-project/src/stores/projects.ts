// src/stores/projects.ts
import { defineStore } from 'pinia';
import axios from 'axios';
import { useAuthStore } from './auth';
import type { Project, ProjectCreate, ProjectUpdate } from '@/types';

interface ProjectsState {
  projects: Project[];
  currentProject: Project | null;
}

export const useProjectsStore = defineStore('projects', {
  state: (): ProjectsState => ({
    projects: [],
    currentProject: null,
  }),
  actions: {
    async fetchAllProjects(): Promise<void> {
      const response = await axios.get<Project[]>('/projects/');
      this.projects = response.data;
    },

    async fetchUserProjects(): Promise<Project[]> {
      const authStore = useAuthStore();
      if (!authStore.userId) return [];
      const response = await axios.get<Project[]>('/projects/', {
        params: { participant_id: authStore.userId },
      });
      this.projects = response.data;
      return response.data;
    },

    /**
     * Загружает проект по ID. Если параметр `force` равен true,
     * принудительно делает запрос к серверу, игнорируя текущее состояние.
     */
    async fetchProjectById(id: number, force: boolean = false): Promise<Project> {
      // Если уже есть загруженный проект и force=false, возвращаем его
      if (!force && this.currentProject?.id === id) {
        return this.currentProject;
      }
      const response = await axios.get<Project>(`/projects/${id}`);
      this.currentProject = response.data;
      return response.data;
    },

    async createProject(projectData: ProjectCreate): Promise<Project> {
      const response = await axios.post<Project>('/projects/', projectData);
      return response.data;
    },

    async updateProject(id: number, updateData: ProjectUpdate): Promise<Project> {
      const response = await axios.put<Project>(`/projects/${id}`, updateData);
      // После обновления обновляем currentProject, если он совпадает
      if (this.currentProject?.id === id) {
        this.currentProject = response.data;
      }
      return response.data;
    },

    async deleteProject(id: number): Promise<void> {
      await axios.delete(`/projects/${id}`);
      if (this.currentProject?.id === id) {
        this.currentProject = null;
      }
      this.projects = this.projects.filter(p => p.id !== id);
    },

    // Методы для предложений (опционально)
    async acceptSuggestion(projectId: number, suggestionId: string): Promise<Project> {
      const response = await axios.put<Project>(`/projects/${projectId}/suggestions/${suggestionId}/accept`);
      if (this.currentProject?.id === projectId) {
        this.currentProject = response.data;
      }
      return response.data;
    },

    async rejectSuggestion(projectId: number, suggestionId: string): Promise<Project> {
      const response = await axios.put<Project>(`/projects/${projectId}/suggestions/${suggestionId}/reject`);
      if (this.currentProject?.id === projectId) {
        this.currentProject = response.data;
      }
      return response.data;
    },
  },
});