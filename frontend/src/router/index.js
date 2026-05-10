import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/reset-password',
    name: 'reset-password',
    component: () => import('../views/common/ResetPassword.vue'),
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/common/Login.vue'),
    meta: { public: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/common/Register.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('../layouts/UserLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'home',
        component: () => import('../views/user/Home.vue'),
      },
      {
        path: 'photo-recognition',
        name: 'photo-recognition',
        component: () => import('../views/user/PhotoRecognition.vue'),
      },
      {
        path: 'parameter-query',
        name: 'parameter-query',
        component: () => import('../views/user/ParameterQuery.vue'),
      },
      {
        path: 'spec-qa',
        name: 'spec-qa',
        component: () => import('../views/user/SpecQA.vue'),
      },
      {
        path: 'process-guide',
        name: 'process-guide',
        component: () => import('../views/user/ProcessGuide.vue'),
      },
      {
        path: 'history',
        name: 'history',
        component: () => import('../views/user/History.vue'),
      },
      {
        path: 'detail',
        name: 'detail',
        component: () => import('../views/admin/DetailView.vue'),
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
  authStore.hydrateAuth()

  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
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
