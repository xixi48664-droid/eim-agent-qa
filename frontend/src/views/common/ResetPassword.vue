<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { resetPasswordApi } from '../../api/auth'

const router = useRouter()
const formRef = ref()
const loading = ref(false)

const form = reactive({
  account: '',
  newPassword: '',
  confirmPassword: '',
})

const validateConfirmPassword = (_rule, value, callback) => {
  if (!value) {
    callback(new Error('请再次输入新密码'))
    return
  }
  if (value !== form.newPassword) {
    callback(new Error('两次输入的密码不一致'))
    return
  }
  callback()
}

const rules = {
  account: [
    { required: true, message: '请输入账号', trigger: 'blur' },
    { min: 6, message: '账号长度不能少于 6 个字符', trigger: 'blur' },
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '新密码长度不能少于 6 个字符', trigger: 'blur' },
  ],
  confirmPassword: [{ validator: validateConfirmPassword, trigger: 'blur' }],
}

const handleResetPassword = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      await resetPasswordApi({
        account: form.account,
        newPassword: form.newPassword,
      })
      ElMessage.success('密码重置成功，请使用新密码登录')
      await router.push('/login')
    } catch (error) {
      ElMessage.error(error.message || '密码重置失败，请稍后重试')
    } finally {
      loading.value = false
    }
  })
}

const goLogin = () => router.push('/login')
</script>

<template>
  <div class="auth-page">
    <div class="auth-card reset-card">
      <section class="intro-panel">
        <div class="system-brand">
          <div class="brand-icon">▣</div>
          <div class="brand-name">电子信息制造业<br />多模态问答系统</div>
        </div>
        <h1 class="intro-title">重置密码<br />恢复账户访问</h1>
        <p class="intro-desc">
          通过安全校验重置账户密码，保障系统访问安全与业务数据可靠。
        </p>
        <ul class="feature-list">
          <li><span class="feature-icon">◎</span>多模态图文智能问答</li>
          <li><span class="feature-icon">▣</span>元器件拍照识别</li>
          <li><span class="feature-icon">⌕</span>参数精准查询</li>
          <li><span class="feature-icon">⌁</span>生产流程智能指导</li>
          <li><span class="feature-icon">□</span>行业规范问答支持</li>
        </ul>
      </section>

      <section class="form-panel">
        <div class="form-card">
          <div class="form-tag">密码重置</div>
          <h2 class="form-title">设置新密码</h2>
          <p class="form-subtitle">请输入账号和新密码，完成后返回登录</p>

          <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent>
            <el-form-item label="账号" prop="account">
              <el-input v-model="form.account" size="large" placeholder="请输入邮箱或手机号" />
            </el-form-item>

            <el-form-item label="新密码" prop="newPassword">
              <el-input
                v-model="form.newPassword"
                type="password"
                show-password
                size="large"
                placeholder="请输入新密码"
              />
            </el-form-item>

            <el-form-item label="确认新密码" prop="confirmPassword">
              <el-input
                v-model="form.confirmPassword"
                type="password"
                show-password
                size="large"
                placeholder="请再次输入新密码"
              />
            </el-form-item>

            <el-button
              type="primary"
              size="large"
              class="submit-btn"
              :loading="loading"
              @click="handleResetPassword"
            >
              重置密码
            </el-button>
          </el-form>

          <div class="bottom-link">
            <span>想起密码了？</span>
            <el-button link type="primary" @click="goLogin">返回登录</el-button>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  width: 100%;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  padding: 38px;
  background:
    radial-gradient(circle at 8% 82%, rgba(255, 255, 255, 0.08) 0 70px, transparent 72px),
    radial-gradient(circle at 92% 2%, rgba(255, 255, 255, 0.12) 0 130px, transparent 132px),
    linear-gradient(135deg, #0c5bc3 0%, #1d7ddf 48%, #48aaf2 100%);
}

.auth-card {
  width: min(860px, 100%);
  min-height: 520px;
  display: grid;
  grid-template-columns: 0.9fr 1fr;
  overflow: hidden;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 26px 70px rgba(14, 57, 120, 0.35);
}

.intro-panel {
  display: flex;
  flex-direction: column;
  padding: 36px 30px;
  color: #fff;
  background: linear-gradient(180deg, #1067d7 0%, #1682e7 60%, #239bf1 100%);
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
}

.brand-name {
  font-size: 13px;
  line-height: 1.35;
  font-weight: 700;
}

.intro-title {
  margin: 0;
  color: #fff;
  font-size: 27px;
  line-height: 1.35;
  font-weight: 800;
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

.form-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
}

.form-card {
  width: min(360px, 100%);
}

.form-tag {
  display: inline-flex;
  padding: 5px 10px;
  border-radius: 999px;
  background: #edf6ff;
  color: #2d7cf1;
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 20px;
}

.form-title {
  margin: 0;
  color: #111827;
  font-size: 30px;
  font-weight: 800;
}

.form-subtitle {
  margin: 8px 0 20px;
  color: #8b95a5;
  font-size: 13px;
}

:deep(.el-form-item) {
  margin-bottom: 14px;
}

:deep(.el-form-item__label) {
  color: #374151;
  font-size: 13px;
  font-weight: 600;
}

:deep(.el-input__wrapper) {
  border-radius: 9px;
  background: #f7f9fc;
  box-shadow: 0 0 0 1px #edf1f7 inset;
}

.submit-btn {
  width: 100%;
  height: 44px;
  border-radius: 10px;
  font-weight: 700;
}

.bottom-link {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 20px;
  color: #8b95a5;
  font-size: 13px;
}

@media (max-width: 860px) {
  .auth-card {
    grid-template-columns: 1fr;
  }
}
</style>
