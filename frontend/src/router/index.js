import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
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

  if (to.path === '/login' && authStore.token) {
    return '/'
  }

  return true
})

export default router
