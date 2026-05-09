import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/',
  timeout: 10000,
})
//请求拦截器：如果token存在，则将token添加到请求头
request.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers = config.headers || {}
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)
//响应拦截器：如果响应状态码不是200，则提示错误信息
request.interceptors.response.use(
  (response) => {
    const res = response.data         //后端返回的包放在response.data中

    if (res?.code !== 200) {
      const message = res?.message || '请求失败'
      ElMessage.error(message)
      return Promise.reject(new Error(message))
    }

    return res
  },
  //http状态码异常处理
  (error) => {
    const status = error?.response?.status
    const message = error?.response?.data?.message || error.message || '网络错误'

    if (status === 401) {
      const authStore = useAuthStore()
      authStore.clearAuth()
      window.location.href = '/login'      //硬转跳到登录页，清掉所有残留状态
    }

    ElMessage.error(message)
    return Promise.reject(error)      //错误抛出
  },
)

export default request
