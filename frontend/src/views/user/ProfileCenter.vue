<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  changePasswordApi,
  getProfileApi,
  getUserActivitiesApi,
  getUserStatsApi,
  updateProfileApi,
} from '../../api/profile'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()
const profileFormRef = ref(null)
const passwordFormRef = ref(null)
const profileLoading = ref(false)
const saveLoading = ref(false)
const passwordLoading = ref(false)
const activitiesLoading = ref(false)
const profile = ref({})
const activities = ref([])
const activityTotal = ref(0)
const activityPage = ref(1)
const activityPageSize = ref(8)

const profileForm = reactive({
  username: '',
  email: '',
  phone: '',
  department: '',
  avatar: '',
})

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const stats = reactive({
  totalOperations: 0,
  loginCount: 0,
  questionCount: 0,
  savedRecordCount: 0,
  exportReportCount: 0,
  satisfactionScore: 0,
})

const profileRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [{ type: 'email', message: '邮箱格式不正确', trigger: 'blur' }],
  phone: [{ pattern: /^$|^1\d{10}$/, message: '手机号格式不正确', trigger: 'blur' }],
}

const validateConfirmPassword = (_rule, value, callback) => {
  if (!value) {
    callback(new Error('请再次输入新密码'))
    return
  }
  if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入的新密码不一致'))
    return
  }
  callback()
}

const passwordRules = {
  oldPassword: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '新密码不能少于 6 个字符', trigger: 'blur' },
  ],
  confirmPassword: [{ validator: validateConfirmPassword, trigger: 'blur' }],
}

const displayName = computed(() => profile.value.username || authStore.nickname || authStore.account || '用户')
const displayRole = computed(() => (profile.value.role === 'admin' ? '管理员' : '普通用户'))
const avatarText = computed(() => displayName.value.slice(0, 1).toUpperCase())

const formatDateTime = (value) => {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString()
}

const syncProfileForm = (data) => {
  profileForm.username = data.username || ''
  profileForm.email = data.email || ''
  profileForm.phone = data.phone || ''
  profileForm.department = data.department || ''
  profileForm.avatar = data.avatar || ''
}

const loadProfile = async () => {
  profileLoading.value = true
  try {
    const res = await getProfileApi()
    profile.value = res.data || {}
    syncProfileForm(profile.value)
    authStore.setUserInfo({
      username: profile.value.username,
      account: profile.value.username || authStore.account,
      role: profile.value.role,
      status: profile.value.status,
    })
  } catch (error) {
    ElMessage.error(error.message || '获取个人资料失败')
  } finally {
    profileLoading.value = false
  }
}

const loadStats = async () => {
  try {
    const res = await getUserStatsApi()
    Object.assign(stats, res.data || {})
  } catch (error) {
    ElMessage.error(error.message || '获取活动统计失败')
  }
}

const loadActivities = async () => {
  activitiesLoading.value = true
  try {
    const res = await getUserActivitiesApi({ pageNum: activityPage.value, pageSize: activityPageSize.value })
    const data = res.data || {}
    activities.value = data.records || data.list || []
    activityTotal.value = data.total || activities.value.length
  } catch (error) {
    ElMessage.error(error.message || '获取活动记录失败')
  } finally {
    activitiesLoading.value = false
  }
}

const saveProfile = async () => {
  if (!profileFormRef.value) return
  await profileFormRef.value.validate(async (valid) => {
    if (!valid) return

    saveLoading.value = true
    try {
      const res = await updateProfileApi({ ...profileForm })
      profile.value = res.data || { ...profile.value, ...profileForm }
      syncProfileForm(profile.value)
      authStore.setUserInfo({
        userId: profile.value.userId || authStore.userId,
        account: profile.value.username || authStore.account,
        nickname: profile.value.username || authStore.nickname,
        role: profile.value.role,
        status: profile.value.status,
      })
      ElMessage.success('个人资料已保存')
      loadActivities()
    } catch (error) {
      ElMessage.error(error.message || '保存个人资料失败')
    } finally {
      saveLoading.value = false
    }
  })
}

const resetProfile = () => {
  syncProfileForm(profile.value)
}

const resetPasswordForm = () => {
  passwordForm.oldPassword = ''
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
  passwordFormRef.value?.clearValidate()
}

const submitPassword = async () => {
  if (!passwordFormRef.value) return
  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return

    if (passwordForm.oldPassword === passwordForm.newPassword) {
      ElMessage.warning('新密码不能与当前密码相同')
      return
    }

    passwordLoading.value = true
    try {
      await changePasswordApi({ ...passwordForm })
      ElMessage.success('密码修改成功，请使用新密码重新登录')
      resetPasswordForm()
      authStore.clearAuth()
      window.__VUE_APP_ROUTER__?.push('/login')
    } catch (error) {
      ElMessage.error(error.message || '密码修改失败')
    } finally {
      passwordLoading.value = false
    }
  })
}

const handleActivityPageChange = (page) => {
  activityPage.value = page
  loadActivities()
}

onMounted(() => {
  loadProfile()
  loadStats()
  loadActivities()
})
</script>

<template>
  <div class="profile-page" v-loading="profileLoading">
    <section class="profile-hero">
      <div class="avatar-wrap">
        <el-avatar :size="92" :src="profile.avatar || profileForm.avatar">
          {{ avatarText }}
        </el-avatar>
        <span class="online-dot"></span>
      </div>
      <div class="hero-info">
        <h2>{{ displayName }}</h2>
        <el-tag effect="dark" round>{{ displayRole }}</el-tag>
        <div class="hero-meta">
          <span>{{ profile.email || '未填写邮箱' }}</span>
          <span>注册于 {{ formatDateTime(profile.registerTime) }}</span>
          <span>最近登录 {{ formatDateTime(profile.lastLoginTime) }}</span>
        </div>
      </div>
    </section>

    <section class="stats-grid">
      <div class="stat-card">
        <strong>{{ stats.questionCount || profile.questionCount || 0 }}</strong>
        <span>累计提问</span>
      </div>
      <div class="stat-card">
        <strong>{{ stats.savedRecordCount || profile.savedRecordCount || 0 }}</strong>
        <span>保存记录</span>
      </div>
      <div class="stat-card">
        <strong>{{ stats.exportReportCount || profile.exportReportCount || 0 }}</strong>
        <span>导出报告</span>
      </div>
      <div class="stat-card">
        <strong>{{ stats.satisfactionScore || profile.satisfactionScore || 0 }}%</strong>
        <span>满意度</span>
      </div>
    </section>

    <section class="content-grid">
      <el-card class="profile-card">
        <template #header>基本信息</template>
        <el-form ref="profileFormRef" :model="profileForm" :rules="profileRules" label-position="top">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="profileForm.username" placeholder="请输入用户名" />
          </el-form-item>
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="profileForm.email" placeholder="请输入邮箱" />
          </el-form-item>
          <el-form-item label="手机号" prop="phone">
            <el-input v-model="profileForm.phone" placeholder="请输入手机号" />
          </el-form-item>
          <el-form-item label="部门" prop="department">
            <el-input v-model="profileForm.department" placeholder="请输入部门" />
          </el-form-item>
          <el-form-item label="头像地址" prop="avatar">
            <el-input v-model="profileForm.avatar" placeholder="请输入头像图片地址" />
          </el-form-item>
          <div class="form-actions">
            <el-button type="primary" :loading="saveLoading" @click="saveProfile">保存修改</el-button>
            <el-button @click="resetProfile">重置</el-button>
          </div>
        </el-form>
      </el-card>

      <div class="side-column">
        <el-card class="password-card">
          <template #header>修改密码</template>
          <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-position="top">
            <el-form-item label="当前密码" prop="oldPassword">
              <el-input v-model="passwordForm.oldPassword" type="password" show-password placeholder="请输入当前密码" />
            </el-form-item>
            <el-form-item label="新密码" prop="newPassword">
              <el-input v-model="passwordForm.newPassword" type="password" show-password placeholder="请输入新密码" />
            </el-form-item>
            <el-form-item label="确认新密码" prop="confirmPassword">
              <el-input v-model="passwordForm.confirmPassword" type="password" show-password placeholder="请再次输入新密码" />
            </el-form-item>
            <el-button type="primary" :loading="passwordLoading" @click="submitPassword">确认修改</el-button>
          </el-form>
        </el-card>

        <el-card class="activity-card">
          <template #header>
            <div class="activity-header">
              <span>最近活动</span>
              <el-button text type="primary" :loading="activitiesLoading" @click="loadActivities">刷新</el-button>
            </div>
          </template>
          <div v-loading="activitiesLoading" class="activity-list">
            <template v-if="activities.length">
              <div v-for="item in activities" :key="item.logId" class="activity-item">
                <div class="activity-icon"></div>
                <div class="activity-info">
                  <div class="activity-title">{{ item.operationDesc || item.operationType }}</div>
                  <div class="activity-time">{{ formatDateTime(item.operationTime) }}</div>
                </div>
              </div>
              <el-pagination
                v-model:current-page="activityPage"
                small
                layout="prev, pager, next"
                :page-size="activityPageSize"
                :total="activityTotal"
                @current-change="handleActivityPageChange"
              />
            </template>
            <el-empty v-else description="暂无活动记录" />
          </div>
        </el-card>
      </div>
    </section>
  </div>
</template>

<style scoped>
.profile-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.profile-hero {
  display: flex;
  align-items: center;
  gap: 24px;
  min-height: 150px;
  padding: 28px;
  border-radius: 16px;
  color: #fff;
  background: linear-gradient(135deg, #0f66d8 0%, #1297f4 100%);
  box-shadow: 0 16px 36px rgba(15, 102, 216, 0.25);
}

.avatar-wrap {
  position: relative;
}

.online-dot {
  position: absolute;
  right: 4px;
  bottom: 8px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 3px solid #fff;
  background: #22c55e;
}

.hero-info h2 {
  margin: 0 0 8px;
  font-size: 26px;
}

.hero-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  margin-top: 14px;
  color: rgba(255, 255, 255, 0.88);
  font-size: 13px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}

.stat-card {
  min-height: 76px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
}

.stat-card strong {
  color: #1684e8;
  font-size: 23px;
}

.stat-card span {
  color: #64748b;
  font-size: 13px;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.profile-card,
.password-card,
.activity-card {
  border-radius: 12px;
}

.side-column {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-actions,
.activity-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.activity-header {
  justify-content: space-between;
}

.activity-list {
  min-height: 220px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 10px;
  background: #f8fafc;
}

.activity-icon {
  width: 28px;
  height: 28px;
  flex: 0 0 auto;
  border-radius: 8px;
  background: #e6f4ff;
}

.activity-title {
  color: #334155;
  font-weight: 600;
}

.activity-time {
  margin-top: 3px;
  color: #94a3b8;
  font-size: 12px;
}

@media (max-width: 980px) {
  .stats-grid,
  .content-grid {
    grid-template-columns: 1fr;
  }

  .hero-meta {
    flex-direction: column;
    gap: 8px;
  }
}
</style>
