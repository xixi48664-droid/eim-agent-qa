import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 15000,
})

// 请求拦截器：注入 JWT token
request.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    if (!config.headers['Content-Type']) {
      config.headers['Content-Type'] = 'application/json'
    }
    return config
  },
  (error) => Promise.reject(error),
)

// 响应拦截器：统一结构 + 错误处理
request.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res.code !== 200) {
      const msg = res.message || '请求失败'
      if (res.code === 401) {
        const router = window.__VUE_APP_ROUTER__
        if (router) {
          const authStore = useAuthStore()
          authStore.clearAuth()
          router.push('/login')
        }
        ElMessage.error('登录已失效，请重新登录')
      } else if (res.code === 403) {
        ElMessage.error('无权限访问')
      } else if (res.code === 404) {
        // 404 通常是正常业务结果，不弹 toast
      } else {
        ElMessage.error(msg)
      }
      return Promise.reject(new Error(msg))
    }
    return res
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      if (status === 401) {
        ElMessage.error('登录已失效，请重新登录')
        const authStore = useAuthStore()
        authStore.clearAuth()
        window.__VUE_APP_ROUTER__?.push('/login')
      } else if (status === 403) {
        ElMessage.error('无权限访问')
      } else if (status >= 500) {
        ElMessage.error('服务器错误，请稍后重试')
      } else {
        ElMessage.error(data?.message || '请求失败')
      }
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请稍后重试')
    } else {
      ElMessage.error('网络异常，请检查网络连接')
    }
    return Promise.reject(error)
  },
)

export default request
