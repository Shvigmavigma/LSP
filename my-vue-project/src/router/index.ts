import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import VerifyEmail from '../views/VerifyEmail.vue'
import MainMenu from '../views/MainMenu.vue'
import AllUsers from '../views/AllUsers.vue'
import UserDetails from '../views/UserDetails.vue'
import AllProjects from '../views/AllProjects.vue'
import MyProjects from '../views/MyProjects.vue'
import ProjectDetails from '../views/ProjectDetails.vue'
import ProjectEdit from '../views/ProjectEdit.vue'
import TaskDetails from '../views/TaskDetails.vue'
import TaskEdit from '../views/TaskEdit.vue'
import Profile from '../views/Profile.vue'
import ProfileEdit from '../views/ProfileEdit.vue'
import UserProjects from '../views/UserProjects.vue'
import InviteAccept from '@/views/InviteAccept.vue'

import AdminEmails from '../views/AdminEmails.vue'
import AdminPanel from '../views/AdminPanel.vue'
import AdminUsers from '../views/AdminUsers.vue'
import AdminUserEdit from '../views/AdminUserEdit.vue'
import AdminProjects from '../views/AdminProjects.vue'
import AdminProjectEdit from '../views/AdminProjectEdit.vue'

const routes: Array<RouteRecordRaw> = [
  { path: '/', redirect: '/login' },
  { path: '/login', name: 'Login', component: Login },
  { path: '/register', name: 'Register', component: Register },
  { path: '/verify-email', name: 'VerifyEmail', component: VerifyEmail },
  { path: '/main', name: 'MainMenu', component: MainMenu },
  { path: '/users', name: 'AllUsers', component: AllUsers },
  { path: '/user/:id', name: 'UserDetails', component: UserDetails },
  { path: '/projects', name: 'AllProjects', component: AllProjects },
  { path: '/my-projects', name: 'MyProjects', component: MyProjects },
  { path: '/project/:id', name: 'ProjectDetails', component: ProjectDetails },
  { path: '/project/edit/:id', name: 'ProjectEdit', component: ProjectEdit },
  { path: '/project/:projectId/task/:taskIndex', name: 'TaskDetails', component: TaskDetails },
  { path: '/project/:projectId/task/:taskIndex/edit', name: 'TaskEdit', component: TaskEdit },
  { path: '/profile', name: 'Profile', component: Profile },
  { path: '/profile/edit', name: 'ProfileEdit', component: ProfileEdit },
  { path: '/user/:id/projects', name: 'UserProjects', component: UserProjects },
  { path: '/invite/:token', name: 'InviteAccept', component: InviteAccept },
  
  // Админские маршруты
  {
    path: '/admin',
    name: 'AdminPanel',
    component: AdminPanel,
    meta: { requiresAdmin: true }
  },
  {
    path: '/admin/users',
    name: 'AdminUsers',
    component: AdminUsers,
    meta: { requiresAdmin: true }
  },
  {
  path: '/old-projects',
  name: 'OldProjects',
  component: () => import('@/views/OldProjects.vue'),
  meta: { requiresAuth: true }
},
  {
    path: '/admin/users/:id/edit',
    name: 'AdminUserEdit',
    component: AdminUserEdit,
    meta: { requiresAdmin: true }
  },
  {
    path: '/admin/projects',
    name: 'AdminProjects',
    component: AdminProjects,
    meta: { requiresAdmin: true }
  },
  {
    path: '/admin/projects/:id/edit',
    name: 'AdminProjectEdit',
    component: AdminProjectEdit,
    meta: { requiresAdmin: true }
  },
  {
    path: '/admin/emails',
    name: 'AdminEmails',
    component: AdminEmails,
    meta: { requiresAdmin: true }
  },
  {
  path: '/invitations',
  name: 'Invitations',
  component: () => import('@/views/Invitations.vue'),
  meta: { requiresAuth: true }
},
  ]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Guard для проверки прав администратора (обновлённый синтаксис без next())
router.beforeEach(async (to, from) => {
  if (to.meta.requiresAdmin) {
    const { useAuthStore } = await import('@/stores/auth')
    const authStore = useAuthStore()
    if (!authStore.isAuthenticated) {
      await authStore.checkAuth()
    }
    if (!authStore.user?.is_admin) {
      return '/main' // перенаправляем на главную
    }
  }
  // Разрешаем переход
  return true
})

export default router