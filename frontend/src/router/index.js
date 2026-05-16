import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/common/Login.vue'),
    meta: { public: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/Register.vue'),
    meta: { public: true },
  },
  {
    path: '/reset-password',
    name: 'reset-password',
    component: () => import('../views/ResetPassword.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('../layouts/UserLayout.vue'),
    meta: { requiresAuth: true, requiresUser: true },
    children: [
      {
        path: '',
        redirect: '/main-chat',
      },
      {
        path: 'main-chat',
        name: 'main-chat',
        component: () => import('../views/user/MainChat.vue'),
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
        path: 'history-record',
        name: 'history-record',
        component: () => import('../views/user/HistoryRecord.vue'),
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

  if (to.meta.requiresUser && authStore.role === 'admin') {
    return '/admin'
  }

  if (to.path === '/login' && authStore.token) {
    return authStore.role === 'admin' ? '/admin' : '/'
  }

  return true
})

export default router
