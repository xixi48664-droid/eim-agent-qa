import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './style.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

// 挂载 router 引用，供 request 拦截器在非组件上下文中使用
window.__VUE_APP_ROUTER__ = router

app.mount('#app')
