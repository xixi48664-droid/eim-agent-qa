<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getUserDetailApi } from '../api/auth'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)

const detail = reactive({
  userId: '',
  account: '',
  nickname: '',
  role: '',
  status: '',
  createdAt: '',
})

const roleMap = {
  admin: { label: '管理员', type: 'danger' },
  user: { label: '普通用户', type: 'primary' },
}

const statusMap = {
  enabled: { label: '启用', type: 'success' },
  disabled: { label: '禁用', type: 'danger' },
  pending: { label: '待审核', type: 'warning' },
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await getUserDetailApi({ userId: authStore.userId })
    Object.assign(detail, res.data)
  } catch {
    ElMessage.error('获取用户信息失败')
  } finally {
    loading.value = false
  }
})

const handleBack = () => {
  router.back()
}
</script>

<template>
  <div class="detail-page">
    <div class="page-header">
      <div class="header-left">
        <div class="back-btn" @click="handleBack">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M15 18l-6-6 6-6"/>
          </svg>
          返回
        </div>
      </div>
      <h2 class="page-title">用户详情</h2>
      <div class="header-right"></div>
    </div>

    <div class="detail-content" v-loading="loading">
      <div class="detail-card">
        <div class="card-banner">
          <div class="avatar-wrap">
            <div class="avatar">
              {{ detail.nickname ? detail.nickname.charAt(0).toUpperCase() : '?' }}
            </div>
          </div>
          <div class="banner-info">
            <div class="banner-name">{{ detail.nickname || '未设置昵称' }}</div>
            <div class="banner-account">{{ detail.account }}</div>
          </div>
        </div>

        <div class="info-grid">
          <div class="info-item">
            <div class="info-label">用户ID</div>
            <div class="info-value">{{ detail.userId || '-' }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">账号</div>
            <div class="info-value">{{ detail.account || '-' }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">昵称</div>
            <div class="info-value">{{ detail.nickname || '-' }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">角色</div>
            <div class="info-value">
              <el-tag
                v-if="detail.role"
                :type="roleMap[detail.role]?.type || 'info'"
                size="small"
              >
                {{ roleMap[detail.role]?.label || detail.role }}
              </el-tag>
              <span v-else>-</span>
            </div>
          </div>
          <div class="info-item">
            <div class="info-label">账号状态</div>
            <div class="info-value">
              <el-tag
                v-if="detail.status"
                :type="statusMap[detail.status]?.type || 'info'"
                size="small"
              >
                {{ statusMap[detail.status]?.label || detail.status }}
              </el-tag>
              <span v-else>-</span>
            </div>
          </div>
          <div class="info-item">
            <div class="info-label">注册时间</div>
            <div class="info-value">{{ detail.createdAt || '-' }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.detail-page {
  width: 100%;
  min-height: 100vh;
  background: #f3f7ff;
  box-sizing: border-box;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 28px;
  background: #fff;
  border-bottom: 1px solid #e5edf8;
}

.header-left,
.header-right {
  width: 120px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #64748b;
  font-size: 14px;
  cursor: pointer;
  transition: color 0.2s;
}

.back-btn:hover {
  color: #1677ff;
}

.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.detail-content {
  padding: 28px;
}

.detail-card {
  background: #fff;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.card-banner {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 28px 28px 24px;
  background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 55%, #3b82f6 100%);
  color: #fff;
}

.avatar-wrap {
  flex-shrink: 0;
}

.avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.22);
  border: 3px solid rgba(255, 255, 255, 0.4);
  display: grid;
  place-items: center;
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 1px;
}

.banner-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.banner-name {
  font-size: 22px;
  font-weight: 700;
}

.banner-account {
  font-size: 14px;
  opacity: 0.8;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0;
  padding: 8px 0;
}

.info-item {
  padding: 20px 28px;
  border-bottom: 1px solid #f1f5f9;
  border-right: 1px solid #f1f5f9;
}

.info-item:nth-child(3n) {
  border-right: none;
}

.info-item:nth-last-child(-n+3) {
  border-bottom: none;
}

.info-label {
  font-size: 13px;
  color: #94a3b8;
  margin-bottom: 8px;
  font-weight: 500;
}

.info-value {
  font-size: 15px;
  color: #1e293b;
  font-weight: 500;
}
</style>
