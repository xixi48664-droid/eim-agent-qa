<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const userName = computed(() => authStore.userInfo?.nickname || '游客')

const handleLogout = async () => {
  authStore.clearAuth()
  await router.push('/login')
}
</script>

<template>
  <el-container class="layout-shell">
    <el-aside width="220px" class="sidebar">
      <div class="brand">EIM Agent QA</div>
      <el-menu default-active="1" class="menu">
        <el-menu-item index="1">首页</el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div>欢迎你，{{ userName }}</div>
        <el-button type="danger" plain @click="handleLogout">退出登录</el-button>
      </el-header>

      <el-main class="main-content">
        <el-card>
          <h1>基础布局已完成</h1>
          <p>下一步可以开始接入第一个写死的业务模块页面。</p>
        </el-card>
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout-shell {
  min-height: 100vh;
  background: #f5f7fb;
}

.sidebar {
  background: #1f2937;
  color: #fff;
  padding: 20px 16px;
}

.brand {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 20px;
}

.menu {
  border-right: none;
  background: transparent;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
}

.main-content {
  padding: 24px;
}
</style>
