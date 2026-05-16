<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const userName = computed(() => authStore.nickname || authStore.account || '游客')

const menuItems = [
  { index: '/main-chat', label: '主问答' },
  { index: '/photo-recognition', label: '拍照识件' },
  { index: '/parameter-query', label: '参数查询' },
  { index: '/spec-qa', label: '规范问答' },
  { index: '/process-guide', label: '流程指导' },
  { index: '/history-record', label: '历史记录' },
]

const isAdmin = computed(() => authStore.isAdmin)

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
  <el-container class="user-layout">
    <el-header class="topbar">
      <div class="brand-wrap">
        <div class="brand-logo">
          <svg width="26" height="26" viewBox="0 0 48 48" fill="none">
            <rect x="4" y="8" width="40" height="32" rx="4" stroke="currentColor" stroke-width="1.5"/>
            <rect x="8" y="14" width="14" height="8" rx="1.5" stroke="currentColor" stroke-width="1.2"/>
            <rect x="26" y="14" width="14" height="6" rx="1.5" stroke="currentColor" stroke-width="1.2"/>
            <rect x="8" y="26" width="8" height="10" rx="1.5" stroke="currentColor" stroke-width="1.2"/>
            <rect x="20" y="26" width="8" height="10" rx="1.5" stroke="currentColor" stroke-width="1.2"/>
            <rect x="32" y="24" width="8" height="12" rx="1.5" stroke="currentColor" stroke-width="1.2"/>
            <circle cx="12" cy="12" r="1" fill="currentColor" opacity="0.6"/>
            <circle cx="24" cy="12" r="1" fill="currentColor" opacity="0.6"/>
            <circle cx="36" cy="12" r="1" fill="currentColor" opacity="0.6"/>
            <line x1="12" y1="4" x2="12" y2="8" stroke="currentColor" stroke-width="1" opacity="0.4"/>
            <line x1="24" y1="4" x2="24" y2="8" stroke="currentColor" stroke-width="1" opacity="0.4"/>
            <line x1="36" y1="4" x2="36" y2="8" stroke="currentColor" stroke-width="1" opacity="0.4"/>
          </svg>
        </div>
        <div class="brand-text">
          <div class="brand-title">电子信息制造业多模态问答系统</div>
        </div>
      </div>

      <div class="topbar-actions">
        <span class="welcome">你好，{{ userName }}</span>
        <el-button class="topbar-text-btn" text>帮助</el-button>
        <el-button class="logout-btn" type="danger" plain @click="handleLogout">退出</el-button>
      </div>
    </el-header>

    <el-container class="body-area">
      <el-aside width="300px" class="sidebar">
        <div class="sidebar-inner">
          <div class="nav-title">功能导航</div>
          <el-menu
            :default-active="route.path"
            class="nav-menu"
            background-color="#ffffff"
            text-color="#334155"
            active-text-color="#1677ff"
            @select="handleMenuSelect"
          >
            <el-menu-item v-for="item in menuItems" :key="item.index" :index="item.index">
              {{ item.label }}
            </el-menu-item>

            <div v-if="isAdmin" class="nav-divider">
              <span class="nav-divider-text">系统</span>
            </div>

            <el-menu-item v-if="isAdmin" index="/admin/users">
              <span class="menu-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                  <circle cx="12" cy="12" r="3"/>
                  <path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
                  <path d="M4.93 4.93a10 10 0 0 0 0 14.14"/>
                </svg>
              </span>
              管理后台
            </el-menu-item>
          </el-menu>
        </div>
      </el-aside>

      <el-main class="content-area">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.user-layout {
  width: 100%;
  min-height: 100vh;
  background: #f3f7ff;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  height: 72px;
  box-sizing: border-box;
  padding: 0 28px;
  color: #fff;
  background: linear-gradient(90deg, #1d4ed8 0%, #2563eb 55%, #3b82f6 100%);
  box-shadow: 0 2px 12px rgba(29, 78, 216, 0.18);
}

.brand-wrap {
  display: flex;
  align-items: center;
  gap: 14px;
}

.brand-logo {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
  flex: 0 0 auto;
}

.brand-text {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.brand-title {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.welcome {
  font-size: 14px;
  color: #fff;
  white-space: nowrap;
}

.topbar-text-btn {
  color: #fff !important;
  border-radius: 8px;
  padding: 8px 12px;
}

.topbar-text-btn:hover,
.topbar-text-btn:focus {
  color: #fff !important;
  background: #1e3a8a !important;
  opacity: 1;
}

.logout-btn {
  margin-left: 4px;
  background: #ef4444;
  border-color: #ef4444;
  color: #fff;
}

.logout-btn:hover,
.logout-btn:focus {
  background: #dc2626;
  border-color: #dc2626;
  color: #fff;
}

.body-area {
  width: 100%;
  min-height: calc(100vh - 72px);
}

.sidebar {
  background: #fff;
  border-right: 1px solid #e5edf8;
}

.sidebar-inner {
  height: 100%;
  padding: 18px 0;
}

.nav-title {
  padding: 0 22px 12px;
  color: #64748b;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 1px;
}

.nav-menu {
  border-right: none;
}

:deep(.el-menu-item) {
  height: 56px;
  margin: 4px 12px;
  border-radius: 12px;
  font-size: 16px;
}

:deep(.el-menu-item.is-active) {
  background: #e8f1ff;
  font-weight: 600;
}

:deep(.el-menu-item:hover) {
  background: #f2f7ff;
}

.nav-divider {
  padding: 16px 22px 4px;
}

.nav-divider-text {
  font-size: 11px;
  font-weight: 600;
  color: #94a3b8;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.menu-icon {
  display: flex;
  align-items: center;
  margin-right: 6px;
}

.content-area {
  width: 100%;
  padding: 28px;
  box-sizing: border-box;
}
</style>
