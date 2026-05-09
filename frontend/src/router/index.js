import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/Login.vue'),
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

  if (to.path === '/login' && authStore.isLoggedIn) {
    return '/'
  }

  return true
})

export default router
