import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/reset-password',
    name: 'reset-password',
    component: () => import('../views/ResetPassword.vue'),
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/Login.vue'),
  },
  {
    path: '/',
    component: () => import('../layouts/UserLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'home',
        component: () => import('../views/Home.vue'),
      },
      {
        path: 'photo-recognition',
        name: 'photo-recognition',
        component: () => import('../views/PhotoRecognition.vue'),
      },
      {
        path: 'parameter-query',
        name: 'parameter-query',
        component: () => import('../views/ParameterQuery.vue'),
      },
      {
        path: 'spec-qa',
        name: 'spec-qa',
        component: () => import('../views/SpecQA.vue'),
      },
      {
        path: 'process-guide',
        name: 'process-guide',
        component: () => import('../views/ProcessGuide.vue'),
      },
      {
        path: 'history',
        name: 'history',
        component: () => import('../views/History.vue'),
      },
      {
        path: 'detail',
        name: 'detail',
        component: () => import('../views/DetailView.vue'),
      },
    ],
  },
  {
    path: '/admin',
    component: () => import('../layouts/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: '',
        redirect: '/admin/users',
      },
      {
        path: 'users',
        name: 'admin-users',
        component: () => import('../views/admin/AdminUsers.vue'),
      },
      {
        path: 'monitor',
        name: 'admin-monitor',
        component: () => import('../views/admin/AdminMonitor.vue'),
      },
      {
        path: 'knowledge',
        name: 'admin-knowledge',
        component: () => import('../views/admin/AdminKnowledge.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.token) {
    return '/login'
  }

  if (to.meta.requiresAdmin && authStore.role !== 'admin') {
    return '/'
  }

  if (to.path === '/login' && authStore.token) {
    return '/'
  }

  return true
})

export default router
