<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const userName = computed(() => authStore.nickname || authStore.account || '游客')

const adminMenuItems = [
  { index: '/admin/users', label: '用户管理', icon: 'user' },
  { index: '/admin/monitor', label: '服务监控', icon: 'monitor' },
  { index: '/admin/knowledge', label: '知识库管理', icon: 'book' },
]

const activeMenu = computed(() => route.path)

const handleMenuSelect = (index) => {
  if (index !== route.path) {
    router.push(index)
  }
}

const handleLogout = () => {
  authStore.clearAuth()
  router.push('/login')
}
</script>

<template>
  <el-container class="admin-layout">
    <!-- 顶部导航 -->
    <el-header class="admin-header">
      <div class="header-left">
        <div class="brand-logo">E</div>
        <div class="brand-info">
          <span class="brand-title">电子信息制造业多模态问答系统</span>
          <span class="brand-sub">管理后台</span>
        </div>
      </div>

      <div class="header-right">
        <span class="welcome-text">你好，{{ userName }}</span>
        <div class="header-divider"></div>
        <el-button class="header-btn" text>个人中心</el-button>
        <el-button class="header-btn" text>帮助</el-button>
        <el-button class="header-btn exit-btn" text @click="handleLogout">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 4px">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
            <polyline points="16 17 21 12 16 7"/>
            <line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
          退出
        </el-button>
      </div>
    </el-header>

    <!-- 主体区域 -->
    <el-container class="admin-body">
      <!-- 左侧管理导航 -->
      <el-aside width="240px" class="admin-sidebar">
        <div class="sidebar-title">管理功能</div>
        <el-menu
          :default-active="activeMenu"
          class="admin-nav-menu"
          background-color="#ffffff"
          text-color="#475569"
          active-text-color="#1677ff"
          @select="handleMenuSelect"
        >
          <el-menu-item
            v-for="item in adminMenuItems"
            :key="item.index"
            :index="item.index"
          >
            <span class="menu-icon">
              <svg v-if="item.icon === 'user'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
              <svg v-else-if="item.icon === 'monitor'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
                <line x1="8" y1="21" x2="16" y2="21"/>
                <line x1="12" y1="17" x2="12" y2="21"/>
              </svg>
              <svg v-else-if="item.icon === 'book'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
              </svg>
            </span>
            <span>{{ item.label }}</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 内容区域 -->
      <el-main class="admin-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.admin-layout {
  width: 100%;
  min-height: 100vh;
  background: #f0f4f8;
  flex-direction: column;
}

/* 顶部导航 */
.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  padding: 0 28px;
  box-sizing: border-box;
  background: #1d4ed8;
  box-shadow: 0 2px 8px rgba(29, 78, 216, 0.25);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.brand-logo {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 18px;
  color: #fff;
  flex-shrink: 0;
}

.brand-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.brand-title {
  font-size: 17px;
  font-weight: 600;
  color: #fff;
  letter-spacing: 0.3px;
}

.brand-sub {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.75);
  font-weight: 400;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.welcome-text {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
  margin-right: 8px;
}

.header-divider {
  width: 1px;
  height: 20px;
  background: rgba(255, 255, 255, 0.25);
  margin: 0 10px;
}

.header-btn {
  color: rgba(255, 255, 255, 0.9) !important;
  font-size: 14px;
  border-radius: 6px;
  padding: 6px 12px;
}

.header-btn:hover {
  color: #fff !important;
  background: rgba(255, 255, 255, 0.15) !important;
}

.exit-btn {
  display: flex;
  align-items: center;
}

/* 主体区域 */
.admin-body {
  flex: 1;
  overflow: hidden;
}

/* 侧边栏 */
.admin-sidebar {
  background: #fff;
  border-right: 1px solid #e2e8f0;
  overflow-y: auto;
  flex-shrink: 0;
}

.sidebar-title {
  padding: 20px 22px 12px;
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
  letter-spacing: 1.2px;
  text-transform: uppercase;
}

.admin-nav-menu {
  border-right: none;
  padding: 0 8px;
}

:deep(.el-menu-item) {
  height: 48px;
  margin: 2px 0;
  border-radius: 10px;
  font-size: 15px;
  display: flex;
  align-items: center;
  gap: 10px;
}

:deep(.el-menu-item.is-active) {
  background: #eff6ff;
  font-weight: 600;
}

:deep(.el-menu-item:hover:not(.is-active)) {
  background: #f8fafc;
}

.menu-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

/* 内容区 */
.admin-content {
  padding: 24px;
  overflow-y: auto;
  box-sizing: border-box;
}
</style>
