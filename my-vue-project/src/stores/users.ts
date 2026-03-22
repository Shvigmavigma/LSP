// stores/users.ts
import { defineStore } from 'pinia'
import axios from 'axios'
import type { User } from '@/types'

interface UsersState {
  users: User[]
}

export const useUsersStore = defineStore('users', {
  state: (): UsersState => ({
    users: []
  }),
  actions: {
    /**
     * Загружает пользователей с возможностью фильтрации по типу и поиску.
     * @param userType - 'student', 'teacher' или undefined (все)
     * @param query - поисковый запрос
     */
    async fetchUsers(userType?: string, query?: string) {
      try {
        const params: any = {}
        if (userType) params.user_type = userType
        if (query) params.q = query

        const response = await axios.get('/users/', { params })
        this.users = response.data
        return this.users
      } catch (error) {
        console.error('Ошибка загрузки пользователей:', error)
        throw error
      }
    },

    // Для совместимости со старым кодом
    async fetchAllUsers() {
      return this.fetchUsers()
    },

    async searchUsers(query: string) {
      return this.fetchUsers(undefined, query)
    },

    async fetchStudents(query?: string) {
      return this.fetchUsers('student', query)
    },

    async fetchTeachers(query?: string) {
      return this.fetchUsers('teacher', query)
    },

    async getUserById(id: number): Promise<User | undefined> {
      try {
        const response = await axios.get(`/users/${id}`)
        return response.data
      } catch (error) {
        console.error(`Ошибка загрузки пользователя ${id}:`, error)
        return undefined
      }
    }
  }
})