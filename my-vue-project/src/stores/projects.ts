// src/stores/projects.ts (дополненный методами для предложений)
import { defineStore } from 'pinia';
import axios from 'axios';
import { useAuthStore } from './auth';
import type { Project, ProjectCreate, ProjectUpdate, Suggestion } from '@/types';

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
    async fetchProjectById(id: number): Promise<Project> {
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
      return response.data;
    },
    async deleteProject(id: number): Promise<void> {
      await axios.delete(`/projects/${id}`);
    },
    // Методы для предложений (опционально, можно вызывать напрямую axios)
    async acceptSuggestion(projectId: number, suggestionId: string): Promise<Project> {
      const response = await axios.put<Project>(`/projects/${projectId}/suggestions/${suggestionId}/accept`);
      return response.data;
    },
    async rejectSuggestion(projectId: number, suggestionId: string): Promise<Project> {
      const response = await axios.put<Project>(`/projects/${projectId}/suggestions/${suggestionId}/reject`);
      return response.data;
    }
  },
});