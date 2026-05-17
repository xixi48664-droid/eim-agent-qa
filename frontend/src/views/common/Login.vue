<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { loginApi } from '../../api/auth'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const formRef = ref()

const form = reactive({
  account: 'admin@example.com',
  password: 'admin123',
  role: 'admin',
  remember: true,
})

const loginRules = {
  account: [
    { required: true, message: '请输入账号', trigger: 'blur' },
    { min: 6, message: '账号长度不能少于 6 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' },
  ],
  role: [{ required: true, message: '请选择登录角色', trigger: 'change' }],
}

const handleLogin = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      const res = await loginApi({
        account: form.account,
        password: form.password,
      })

      const backendRole = res.data.role
      if (backendRole !== form.role) {
        ElMessage.error('所选登录身份与账号实际身份不一致')
        return
      }

      authStore.setToken(res.data.token)
      authStore.setUserInfo({
        userId: res.data.userid || res.data.userId,
        account: res.data.account,
        role: backendRole,
        status: res.data.status,
        nickname: res.data.account,
      })

      ElMessage.success('登录成功')
      const isAdmin = backendRole === 'admin'
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
    <div class="login-card">
      <section class="intro-panel">
        <div class="system-brand">
          <div class="brand-icon">▣</div>
          <div class="brand-name">电子信息制造业<br />多模态问答系统</div>
        </div>

        <h1 class="intro-title">智能赋能电子<br />制造全流程</h1>
        <p class="intro-desc">
          基于多模态大模型，为电子信息制造业提供专业的图文问答、元器件识别与工艺流程服务。
        </p>

        <ul class="feature-list">
          <li><span class="feature-icon">◎</span>多模态图文智能问答</li>
          <li><span class="feature-icon">▣</span>元器件拍照识别</li>
          <li><span class="feature-icon">⌕</span>参数精准查询</li>
          <li><span class="feature-icon">⌁</span>生产流程智能指导</li>
          <li><span class="feature-icon">□</span>行业规范问答支持</li>
        </ul>

        <div class="intro-footer">© 2026 电子信息制造业多模态问答系统</div>
      </section>

      <section class="login-panel">
        <div class="form-card">
          <div class="form-tag">安全登录</div>
          <h2 class="welcome-title">欢迎回来</h2>
          <p class="welcome-subtitle">请输入您的账户信息以继续使用系统</p>

          <el-form
            ref="formRef"
            :model="form"
            :rules="loginRules"
            label-position="top"
            class="login-form"
            @submit.prevent
          >
            <el-form-item label="账号" prop="account">
              <el-input v-model="form.account" placeholder="请输入邮箱或手机号" size="large" />
            </el-form-item>

            <el-form-item label="密码" prop="password">
              <el-input
                v-model="form.password"
                type="password"
                show-password
                placeholder="请输入密码（至少六位）"
                size="large"
                @keyup.enter="handleLogin"
              />
            </el-form-item>

            <el-form-item label="登录角色" prop="role">
              <el-select v-model="form.role" placeholder="请选择用户角色" size="large">
                <el-option label="管理员" value="admin" />
                <el-option label="普通用户" value="user" />
              </el-select>
            </el-form-item>

            <div class="login-meta">
              <el-checkbox v-model="form.remember">记住我</el-checkbox>
              <el-button link type="primary" class="forgot-link" @click="goResetPassword">
                忘记密码？
              </el-button>
            </div>

            <el-button type="primary" :loading="loading" class="login-btn" size="large" @click="handleLogin">
              登录系统
            </el-button>
          </el-form>

          <div class="divider-text">还没有账户？</div>

          <div class="bottom-links">
            <el-button link type="primary" @click="goRegister">立即注册</el-button>
            <span>以使用完整功能</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  width: 100%;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  padding: 38px;
  overflow: hidden;
  background:
    radial-gradient(circle at 8% 82%, rgba(255, 255, 255, 0.08) 0 70px, transparent 72px),
    radial-gradient(circle at 92% 2%, rgba(255, 255, 255, 0.12) 0 130px, transparent 132px),
    linear-gradient(135deg, #0c5bc3 0%, #1d7ddf 48%, #48aaf2 100%);
}

.login-card {
  width: min(860px, 100%);
  min-height: 520px;
  display: grid;
  grid-template-columns: 0.9fr 1fr;
  overflow: hidden;
  border-radius: 16px;
  background: #ffffff;
  box-shadow: 0 26px 70px rgba(14, 57, 120, 0.35);
}

.intro-panel {
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 36px 30px;
  color: #ffffff;
  background:
    radial-gradient(circle at 18% 10%, rgba(255, 255, 255, 0.11), transparent 80px),
    linear-gradient(180deg, #1067d7 0%, #1682e7 60%, #239bf1 100%);
}

.system-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 34px;
}

.brand-icon {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.16);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.12);
  font-size: 15px;
}

.brand-name {
  font-size: 13px;
  line-height: 1.35;
  font-weight: 700;
}

.intro-title {
  margin: 0;
  color: #ffffff;
  font-size: 27px;
  line-height: 1.35;
  font-weight: 800;
  letter-spacing: 0.5px;
}

.intro-desc {
  margin: 16px 0 24px;
  color: rgba(255, 255, 255, 0.9);
  font-size: 13px;
  line-height: 1.8;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
}

.feature-list li {
  display: flex;
  align-items: center;
  gap: 11px;
  min-height: 42px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.95);
  font-size: 13px;
}

.feature-icon {
  width: 24px;
  height: 24px;
  flex: 0 0 auto;
  border-radius: 8px;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.14);
  font-size: 12px;
}

.intro-footer {
  margin-top: auto;
  color: rgba(255, 255, 255, 0.65);
  font-size: 11px;
}

.login-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
  background: #ffffff;
}

.form-card {
  width: min(350px, 100%);
}

.form-tag {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border-radius: 999px;
  background: #edf6ff;
  color: #2d7cf1;
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 22px;
}

.welcome-title {
  margin: 0;
  color: #111827;
  font-size: 30px;
  line-height: 1.2;
  font-weight: 800;
}

.welcome-subtitle {
  margin: 8px 0 20px;
  color: #8b95a5;
  font-size: 13px;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 14px;
}

.login-form :deep(.el-form-item__label) {
  color: #374151;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.4;
  margin-bottom: 6px;
}

.login-form :deep(.el-input__wrapper),
.login-form :deep(.el-select__wrapper) {
  border-radius: 9px;
  background: #f7f9fc;
  box-shadow: 0 0 0 1px #edf1f7 inset;
}

.login-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 0 0 12px;
}

.login-meta :deep(.el-checkbox__label),
.forgot-link {
  font-size: 12px;
}

.forgot-link {
  padding: 0;
}

.login-btn {
  width: 100%;
  height: 44px;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 700;
  box-shadow: 0 12px 24px rgba(45, 124, 241, 0.28);
}

.divider-text {
  position: relative;
  margin: 18px 0 12px;
  text-align: center;
  color: #c0c7d2;
  font-size: 12px;
}

.divider-text::before,
.divider-text::after {
  content: '';
  position: absolute;
  top: 50%;
  width: 30%;
  height: 1px;
  background: #edf1f7;
}

.divider-text::before {
  left: 0;
}

.divider-text::after {
  right: 0;
}

.bottom-links {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 4px;
  color: #8b95a5;
  font-size: 12px;
}

@media (max-width: 860px) {
  .login-page {
    padding: 20px;
  }

  .login-card {
    grid-template-columns: 1fr;
    min-height: auto;
  }

  .intro-panel {
    padding: 28px;
  }

  .login-panel {
    padding: 28px;
  }
}
</style>
