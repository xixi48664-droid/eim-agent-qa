<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUserList, toggleUserStatus, resetUserPassword } from '../../api/admin/user'
import { getUserLogs } from '../../api/admin/logs'

// 列表状态
const tableData = ref([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)

// 筛选状态
const filterUsername = ref('')
const filterEmail = ref('')
const filterStatus = ref('')

// 新增/编辑弹窗
const dialogVisible = ref(false)
const dialogTitle = ref('添加用户')
const formRef = ref(null)
const submitting = ref(false)
const editingId = ref(null)

const form = reactive({
  account: '',
  nickname: '',
  role: 'user',
  dept: '',
})

const formRules = {
  account: [
    { required: true, message: '请输入邮箱或手机号', trigger: 'blur' },
    {
      pattern: /^[\w.-]+@[\w.-]+\.\w+$|^\d{11}$/,
      message: '请输入正确的邮箱地址或11位手机号',
      trigger: 'blur',
    },
  ],
  nickname: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

// 操作日志抽屉
const logDrawerVisible = ref(false)
const logTableData = ref([])
const logLoading = ref(false)
const logTotal = ref(0)
const logPage = ref(1)
const logPageSize = ref(10)
const currentLogUser = ref(null)
const filterOpType = ref('')

const operationTypeOptions = [
  { value: '', label: '全部操作' },
  { value: 'login', label: '登录' },
  { value: 'query', label: '参数查询' },
  { value: 'recognize', label: '拍照识别' },
  { value: 'qa', label: '问答' },
]

const deptOptions = [
  '生产技术部', 'SMT生产线', '质量检测部', '信息技术部',
  '产品测试部', '研发部', '采购部', '销售部',
]

const roleOptions = [
  { value: 'user', label: '普通用户' },
  { value: 'admin', label: '管理员' },
]

// 加载用户列表
const fetchUsers = async () => {
  loading.value = true
  try {
    const res = await getUserList({
      username: filterUsername.value,
      email: filterEmail.value,
      status: filterStatus.value,
      pageNum: currentPage.value,
      pageSize: pageSize.value,
    })
    tableData.value = res.data.records || []
    total.value = res.data.total || 0
  } catch {
    // 错误由 request 拦截器统一处理
  } finally {
    loading.value = false
  }
}

// 分页
const handlePageChange = (page) => {
  currentPage.value = page
  fetchUsers()
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  fetchUsers()
}

// 搜索 & 筛选
const handleSearch = () => {
  currentPage.value = 1
  fetchUsers()
}

const resetFilters = () => {
  filterUsername.value = ''
  filterEmail.value = ''
  filterStatus.value = ''
  currentPage.value = 1
  fetchUsers()
}

// 打开新增弹窗
const openAddDialog = () => {
  editingId.value = null
  dialogTitle.value = '添加用户'
  Object.assign(form, { account: '', nickname: '', role: 'user', dept: '' })
  dialogVisible.value = true
}

// 提交表单
const handleSubmit = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    // TODO: 调用实际新增接口
    // await addUser({ ...form })
    ElMessage.success('添加成功')
    dialogVisible.value = false
    fetchUsers()
  } catch {
    // 错误由拦截器处理
  } finally {
    submitting.value = false
  }
}

// 启用/禁用
const handleToggleStatus = async (row) => {
  const action = row.status === 'enabled' ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(
      `确定要${action}用户「${row.username}」吗？${action === '禁用' ? '禁用后该用户将无法登录。' : ''}`,
      `${action}用户`,
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' },
    )
    const newStatus = row.status === 'enabled' ? 'disabled' : 'enabled'
    await toggleUserStatus(row.userId, newStatus)
    ElMessage.success(`用户已${action}`)
    fetchUsers()
  } catch {
    // 用户取消或错误
  }
}

// 重置密码
const handleResetPassword = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要重置用户「${row.username}」的密码吗？`,
      '重置密码',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' },
    )
    const res = await resetUserPassword(row.userId)
    ElMessage.success(`密码已重置${res.data?.tempPassword ? `，新密码：${res.data.tempPassword}` : '成功'}`)
  } catch {
    // 用户取消或错误
  }
}

// 打开操作日志
const handleOpenLogs = (row) => {
  currentLogUser.value = row
  logPage.value = 1
  logTableData.value = []
  logDrawerVisible.value = true
  fetchLogs()
}

const fetchLogs = async () => {
  if (!currentLogUser.value) return
  logLoading.value = true
  try {
    const res = await getUserLogs(currentLogUser.value.userId, {
      operationType: filterOpType.value,
      pageNum: logPage.value,
      pageSize: logPageSize.value,
    })
    logTableData.value = res.data.records || []
    logTotal.value = res.data.total || 0
  } catch {
    // 错误由拦截器处理
  } finally {
    logLoading.value = false
  }
}

const handleLogPageChange = (page) => {
  logPage.value = page
  fetchLogs()
}

const handleLogFilterChange = () => {
  logPage.value = 1
  fetchLogs()
}

// 状态显示
const statusTagType = (status) => status === 'enabled' ? 'success' : 'info'
const statusText = (status) => status === 'enabled' ? '● 正常' : '○ 禁用'

// 角色标签颜色
const roleTagType = (role) => role === 'admin' ? 'danger' : 'default'

onMounted(() => {
  fetchUsers()
})
</script>

<template>
  <div class="admin-users">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-title">
        <h2>用户管理</h2>
        <span class="total-count">共 {{ total }} 位用户</span>
      </div>
      <el-button type="primary" @click="openAddDialog">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="margin-right:6px">
          <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        添加用户
      </el-button>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-input
        v-model="filterUsername"
        placeholder="搜索用户名..."
        class="filter-input"
        clearable
        @keyup.enter="handleSearch"
      />
      <el-input
        v-model="filterEmail"
        placeholder="搜索邮箱..."
        class="filter-input"
        clearable
        @keyup.enter="handleSearch"
      />
      <el-select v-model="filterStatus" placeholder="全部状态" clearable @change="handleSearch">
        <el-option label="正常" value="enabled" />
        <el-option label="禁用" value="disabled" />
      </el-select>
      <el-button @click="resetFilters">重置</el-button>
      <el-button type="primary" @click="handleSearch">搜索</el-button>
    </div>

    <!-- 用户列表 -->
    <div class="table-card">
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="username" label="用户名" min-width="140">
          <template #default="{ row }">
            <div class="user-cell">
              <div class="avatar">{{ row.username?.[0]?.toUpperCase() || '?' }}</div>
              <div class="user-info">
                <span class="nickname">{{ row.username }}</span>
                <span class="account">{{ row.email }}</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="email" label="邮箱" min-width="200" />

        <el-table-column prop="role" label="角色" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="roleTagType(row.role)" size="small" effect="plain">
              {{ row.role === 'admin' ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <span :class="['status-dot', row.status]">{{ statusText(row.status) }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="registerTime" label="注册时间" width="170" align="center">
          <template #default="{ row }">
            <span class="time-cell">{{ row.registerTime || '—' }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="lastLoginTime" label="最近登录" width="170" align="center">
          <template #default="{ row }">
            <span class="time-cell">{{ row.lastLoginTime || '—' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="280" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button size="small" text type="primary" @click="handleOpenLogs(row)">日志</el-button>
              <el-button size="small" text @click="handleResetPassword(row)">重置密码</el-button>
              <el-button
                v-if="row.status === 'enabled'"
                size="small"
                text
                type="danger"
                @click="handleToggleStatus(row)"
              >禁用</el-button>
              <el-button
                v-else
                size="small"
                text
                type="success"
                @click="handleToggleStatus(row)"
              >启用</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-bar">
        <span class="pagination-info">
          共 {{ total }} 条记录，显示第 {{ (currentPage - 1) * pageSize + 1 }}-{{ Math.min(currentPage * pageSize, total) }} 条
        </span>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="total"
          layout="prev, pager, next, jumper, sizes"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </div>

    <!-- 新增用户弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="520px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="90px">
        <el-form-item label="账号" prop="account">
          <el-input v-model="form.account" placeholder="邮箱或手机号" />
        </el-form-item>
        <el-form-item label="姓名" prop="nickname">
          <el-input v-model="form.nickname" placeholder="真实姓名或昵称" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" style="width:100%">
            <el-option v-for="r in roleOptions" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="部门" prop="dept">
          <el-select v-model="form.dept" placeholder="请选择部门" style="width:100%" allow-create filterable clearable>
            <el-option v-for="d in deptOptions" :key="d" :label="d" :value="d" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确认</el-button>
      </template>
    </el-dialog>

    <!-- 操作日志抽屉 -->
    <el-drawer
      v-model="logDrawerVisible"
      :title="`操作日志 - ${currentLogUser?.username || ''}`"
      size="600px"
    >
      <div class="log-filters">
        <el-select v-model="filterOpType" placeholder="操作类型" clearable @change="handleLogFilterChange">
          <el-option v-for="t in operationTypeOptions" :key="t.value" :label="t.label" :value="t.value" />
        </el-select>
      </div>

      <el-table :data="logTableData" v-loading="logLoading" stripe size="small">
        <el-table-column prop="operationType" label="操作类型" width="110" align="center">
          <template #default="{ row }">
            <el-tag
              size="small"
              :type="{
                login: 'success',
                query: 'primary',
                recognize: 'warning',
                qa: 'info',
              }[row.operationType] || 'default'"
            >
              {{ {
                login: '登录',
                query: '参数查询',
                recognize: '拍照识别',
                qa: '问答',
              }[row.operationType] || row.operationType }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="operationDesc" label="操作描述" min-width="200" />
        <el-table-column prop="operationTime" label="操作时间" width="160" align="center" />
      </el-table>

      <div class="pagination-bar">
        <el-pagination
          v-model:current-page="logPage"
          :page-size="logPageSize"
          :total="logTotal"
          layout="prev, pager, next"
          @current-change="handleLogPageChange"
        />
      </div>
    </el-drawer>
  </div>
</template>

<style scoped>
.admin-users {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.page-title {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.page-title h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
}

.total-count {
  font-size: 14px;
  color: #64748b;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.filter-input {
  width: 200px;
}

.table-card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  flex: 1;
  display: flex;
  flex-direction: column;
}

:deep(.el-table th) {
  background: #f8fafc !important;
  color: #64748b;
  font-weight: 600;
  font-size: 13px;
  padding: 12px 8px !important;
}

:deep(.el-table td) {
  padding: 14px 8px !important;
  border-bottom: 1px solid #f1f5f9;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 15px;
  flex-shrink: 0;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.nickname {
  font-weight: 600;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.account {
  font-size: 12px;
  color: #94a3b8;
}

.status-dot {
  font-size: 13px;
  font-weight: 500;
}

.status-dot.enabled { color: #16a34a; }
.status-dot.disabled { color: #94a3b8; }

.time-cell {
  font-size: 13px;
  color: #64748b;
}

.action-btns {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.pagination-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-top: 1px solid #f1f5f9;
  flex-shrink: 0;
}

.pagination-info {
  font-size: 13px;
  color: #64748b;
}

.log-filters {
  margin-bottom: 14px;
}
</style>
