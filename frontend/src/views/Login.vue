<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { loginApi } from '../api/auth'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)

// 响应式：输入框输入（默认值）
const form = reactive({
  account: 'admin@example.com',
  password: 'admin123',
})

// 表单校验
const loginRules = {
  account: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

// 登录处理函数
const handleLogin = async () => {
  loading.value = true
  try {
    const res = await loginApi(form)
    authStore.setToken(res.data.token)
    authStore.setUserInfo({
      userId: res.data.userId,
      account: res.data.account,
      role: res.data.role,
      status: res.data.status,
    })
    ElMessage.success('登录成功')
    await router.push('/')
  } catch (error) {
    ElMessage.error(error.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-title">
        <h1>欢迎登录</h1>
        <p>请输入账号密码进行登录验证</p>
      </div>

      <el-form :model="form" :rules="loginRules" label-position="top" @submit.prevent>
        <el-form-item label="账号" prop="account">
          <el-input v-model="form.account" placeholder="admin@example.com" />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="admin123" />
        </el-form-item>

        <el-button type="primary" :loading="loading" class="login-btn" @click="handleLogin">
          登录
        </el-button>
      </el-form>

      <div class="tips">
        <p>管理员：admin@example.com / admin123</p>
        <p>普通用户：user@example.com / user123</p>
      </div>
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
  padding: 24px;
  background: linear-gradient(135deg, #eef4ff 0%, #f7f9fc 100%);
}

.login-card {
  width: 100%;
  max-width: 420px;
  background: #fff;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 12px 40px rgba(31, 41, 55, 0.08);
}

.login-title h1 {
  margin: 0 0 8px;
  font-size: 28px;
}

.login-title p,
.tips p {
  margin: 0;
  color: #6b7280;
}

.login-title {
  margin-bottom: 24px;
}

.login-btn {
  width: 100%;
  margin-top: 8px;
}

.tips {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #eef2f7;
  font-size: 14px;
  line-height: 1.8;
}
</style>
