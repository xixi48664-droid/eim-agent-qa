<script setup>
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { resetPasswordApi } from '../api/auth'

const router = useRouter()
const route = useRoute()
const loading = ref(false)

const form = reactive({
  account: route.query.account || '',
  newPassword: '',
  confirmPassword: '',
})

const validateConfirm = (rule, value, callback) => {
  if (value !== form.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  account: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' },
  ],
}

const handleReset = async () => {
  if (form.newPassword !== form.confirmPassword) {
    ElMessage.error('两次输入的密码不一致')
    return
  }
  loading.value = true
  try {
    await resetPasswordApi({ account: form.account, newPassword: form.newPassword })
    ElMessage.success('密码重置成功，请使用新密码登录')
    await router.push('/login')
  } catch {
    // 错误消息由 request 拦截器统一处理
  } finally {
    loading.value = false
  }
}

const handleBack = () => {
  router.push('/login')
}
</script>

<template>
  <div class="reset-page">
    <div class="reset-card">
      <div class="card-header">
        <div class="back-btn" @click="handleBack">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M15 18l-6-6 6-6"/>
          </svg>
          返回登录
        </div>
      </div>

      <div class="card-title">
        <div class="title-icon">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
          </svg>
        </div>
        <h1>重置密码</h1>
        <p>请设置您的新密码</p>
      </div>

      <el-form :model="form" :rules="rules" label-position="top" class="reset-form">
        <el-form-item label="账号" prop="account">
          <el-input
            v-model="form.account"
            placeholder="请输入邮箱或手机号"
            clearable
            :disabled="!!route.query.account"
          >
            <template #prefix>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="form.newPassword"
            type="password"
            show-password
            placeholder="请输入新密码（至少6位）"
          >
            <template #prefix>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            show-password
            placeholder="请再次输入新密码"
          >
            <template #prefix>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
            </template>
          </el-input>
        </el-form-item>

        <el-button type="primary" :loading="loading" class="reset-btn" @click="handleReset">
          确认重置
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.reset-page {
  width: 100%;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  padding: 24px;
  background: linear-gradient(135deg, #eef4ff 0%, #f7f9fc 100%);
}

.reset-card {
  width: 100%;
  max-width: 440px;
  background: #fff;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 12px 40px rgba(31, 41, 55, 0.08);
}

.card-header {
  margin-bottom: 8px;
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

.card-title {
  margin-bottom: 28px;
}

.title-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: linear-gradient(135deg, #e8f1ff, #dbeafe);
  display: grid;
  place-items: center;
  color: #1d4ed8;
  margin-bottom: 16px;
}

.card-title h1 {
  margin: 0 0 6px;
  font-size: 26px;
  font-weight: 700;
  color: #1e293b;
}

.card-title p {
  margin: 0;
  color: #64748b;
  font-size: 14px;
}

.reset-form {
  margin-top: 4px;
}

.reset-btn {
  width: 100%;
  margin-top: 8px;
  height: 42px;
  font-size: 16px;
}
</style>
