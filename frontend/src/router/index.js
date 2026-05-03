import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/Home.vue'),
    meta: { requiresAuth: true },           // 需要登录才能访问
  },
  {
    path: '/login',         // 登录页面
    name: 'login',
    component: () => import('../views/Login.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.token) {
    return '/login'          //如果需要登录但未登录，则重定向到登录页面
  }

  if (to.path === '/login' && authStore.token) {
    return '/'              //如果已经登录，则重定向到首页
  }

  return true
})

export default router
