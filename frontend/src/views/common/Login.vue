<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { loginApi } from '../../api/auth'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const formRef = ref()

const form = reactive({
  account: '',
  password: '',
  remember: false,
})

const loginRules = {
  account: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const features = [
  '多模态图文智能问答',
  '元器件拍照识别',
  '参数精准查询',
  '生产流程智能指导',
  '行业规范问答支持',
]

const handleLogin = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const res = await loginApi(form)
      authStore.setToken(res.data.token)
      authStore.setUserInfo({
        userId: res.data.userid || res.data.userId,
        account: res.data.account,
        role: res.data.role,
        status: res.data.status,
      })
      ElMessage.success('登录成功')
      const isAdmin = res.data.role === 'admin'
      await router.push(isAdmin ? '/admin' : '/')
    } catch (error) {
      ElMessage.error(error.message || '登录失败')
    } finally {
      loading.value = false
    }
  })
}

const goRegister = () => router.push('/register')
const goResetPassword = () => router.push('/reset-password')
</script>

<template>
  <div class="login-page">
    <!-- 左侧品牌区 -->
    <div class="brand-panel">
      <div class="brand-overlay">
        <div class="brand-content">
          <div class="brand-header">
            <div class="brand-chip-icon">
              <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
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
            <p class="brand-title-main">电子信息制造业</p>
            <p class="brand-title-sub">多模态问答系统</p>
          </div>

          <div class="brand-tagline">
            <span class="tagline-item">智能赋能电子</span>
            <span class="tagline-divider"></span>
            <span class="tagline-item">制造全流程</span>
          </div>

          <p class="brand-desc">
            基于多模态大模型，为电子信息制造业提供专业的图文问答、元器件识别与工艺指导服务。
          </p>

          <ul class="feature-list">
            <li v-for="feature in features" :key="feature" class="feature-item">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              <span>{{ feature }}</span>
            </li>
          </ul>

          <div class="brand-footer">
            © 2026 电子信息制造业多模态问答系统
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧登录区 -->
    <div class="login-panel">
      <div class="login-form-wrap">
        <div class="login-badge">安全登录</div>
        <h1 class="login-heading">欢迎回来</h1>
        <p class="login-subtitle">请输入您的账户信息以继续使用系统</p>

        <el-form ref="formRef" :model="form" :rules="loginRules" @submit.prevent>
          <el-form-item prop="account">
            <el-input
              v-model="form.account"
              placeholder="账号"
              size="large"
              :prefix-icon="User"
            />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              show-password
              placeholder="密码"
              size="large"
              :prefix-icon="Lock"
              @keyup.enter="handleLogin"
            />
          </el-form-item>

          <div class="form-extra">
            <el-checkbox v-model="form.remember">记住我</el-checkbox>
            <el-button link type="primary" @click="goResetPassword">忘记密码？</el-button>
          </div>

          <el-button
            type="primary"
            :loading="loading"
            size="large"
            class="login-btn"
            @click="handleLogin"
          >
            登录系统
          </el-button>
        </el-form>

        <div class="register-hint">
          <span>还没有账户？</span>
          <el-button link type="primary" @click="goRegister">立即注册</el-button>
          <span>以使用完整功能</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  width: 100%;
  min-height: 100vh;
  display: flex;
}

/* ===== 左侧品牌区 ===== */
.brand-panel {
  flex: 1;
  background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 40%, #2563eb 70%, #3b82f6 100%);
  position: relative;
  overflow: hidden;
  min-width: 0;
}

.brand-panel::before {
  content: '';
  position: absolute;
  top: -30%;
  right: -15%;
  width: 500px;
  height: 500px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.03);
  pointer-events: none;
}

.brand-panel::after {
  content: '';
  position: absolute;
  bottom: -20%;
  left: -10%;
  width: 400px;
  height: 400px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.03);
  pointer-events: none;
}

.brand-overlay {
  position: relative;
  z-index: 1;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 48px;
  box-sizing: border-box;
}

.brand-content {
  max-width: 520px;
  width: 100%;
}

.brand-header {
  margin-bottom: 16px;
}

.brand-chip-icon {
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 28px;
}

.brand-title-main {
  font-size: 36px;
  font-weight: 700;
  color: #fff;
  margin: 0;
  line-height: 1.3;
  letter-spacing: 2px;
}

.brand-title-sub {
  font-size: 28px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
  line-height: 1.3;
  letter-spacing: 2px;
}

.brand-tagline {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.tagline-item {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 500;
  letter-spacing: 1px;
}

.tagline-divider {
  width: 1px;
  height: 14px;
  background: rgba(255, 255, 255, 0.3);
}

.brand-desc {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.65);
  line-height: 1.8;
  margin: 0 0 36px;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 0 0 48px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 15px;
  color: rgba(255, 255, 255, 0.85);
  font-weight: 500;
}

.feature-item svg {
  flex-shrink: 0;
  color: rgba(255, 255, 255, 0.6);
}

.brand-footer {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

/* ===== 右侧登录区 ===== */
.login-panel {
  width: 500px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  padding: 48px;
  box-sizing: border-box;
  flex-shrink: 0;
}

.login-form-wrap {
  width: 100%;
  max-width: 380px;
}

.login-badge {
  display: inline-block;
  padding: 4px 14px;
  border-radius: 20px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 16px;
  letter-spacing: 1px;
}

.login-heading {
  font-size: 32px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 8px;
}

.login-subtitle {
  font-size: 14px;
  color: #64748b;
  margin: 0 0 32px;
}

.form-extra {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.login-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 1px;
}

.register-hint {
  text-align: center;
  margin-top: 24px;
  font-size: 14px;
  color: #64748b;
}

.register-hint .el-button {
  padding: 0 4px;
  font-size: 14px;
}

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .brand-panel {
    display: none;
  }
  .login-panel {
    width: 100%;
    padding: 32px;
  }
}
</style>
