/**
 * 用户管理 API（严格按接口文档 V1.0）
 *
 * 路由前缀：/api/v1/admin/users
 * 统一响应：{ code, message, data }
 * 列表分页：{ pageNum, pageSize, total, records: [] }
 */

// ============================================================
// Mock 数据（后端未部署时使用）
// ============================================================
const MOCK_MODE = true

const mockUsers = [
  { userId: 101, username: 'zhangsan', email: 'zhangsan@example.com', status: 'enabled', registerTime: '2024-01-15 09:00:00', lastLoginTime: '2026-04-24 08:55:00' },
  { userId: 102, username: 'lisi', email: 'lisi@example.com', status: 'enabled', registerTime: '2024-02-20 14:22:00', lastLoginTime: '2026-04-23 16:10:00' },
  { userId: 103, username: 'wangwu', email: 'wangwu@example.com', status: 'enabled', registerTime: '2024-03-05 10:30:00', lastLoginTime: '2026-03-25 11:10:00' },
  { userId: 104, username: 'chenadmin', email: 'chen@example.com', status: 'enabled', registerTime: '2023-11-01 08:00:00', lastLoginTime: '2026-04-24 08:55:00' },
  { userId: 105, username: 'zhaotest', email: 'zhao@example.com', status: 'disabled', registerTime: '2024-04-18 09:00:00', lastLoginTime: '2026-02-10 16:30:00' },
  { userId: 106, username: 'sundev', email: 'sun@example.com', status: 'enabled', registerTime: '2024-05-10 11:00:00', lastLoginTime: '2026-04-22 16:00:00' },
  { userId: 107, username: 'wuqc', email: 'wuqc@example.com', status: 'enabled', registerTime: '2024-06-15 13:00:00', lastLoginTime: '2026-04-24 10:15:00' },
  { userId: 108, username: 'liuzhiliang', email: 'liuzhiliang@example.com', status: 'disabled', registerTime: '2024-07-20 15:00:00', lastLoginTime: '2026-01-05 09:00:00' },
]

const mockLogs = [
  { logId: 9001, operationType: 'login', operationDesc: '用户登录系统', operationTime: '2026-04-24 08:55:00' },
  { logId: 9002, operationType: 'query', operationDesc: '查询元器件 STM32F103C8T6 参数', operationTime: '2026-04-24 09:10:12' },
  { logId: 9003, operationType: 'recognize', operationDesc: '拍照识别电子元器件', operationTime: '2026-04-24 09:25:03' },
  { logId: 9004, operationType: 'qa', operationDesc: '咨询 IPC-2221A 规范相关问题', operationTime: '2026-04-24 10:05:30' },
  { logId: 9005, operationType: 'login', operationDesc: '用户登录系统', operationTime: '2026-04-23 14:00:00' },
  { logId: 9006, operationType: 'query', operationDesc: '查询元器件 ESP32 核心参数', operationTime: '2026-04-23 14:20:00' },
]

const delay = (ms = 300) => new Promise(resolve => setTimeout(resolve, ms))

const throwMockError = (code, message) => {
  const err = new Error(message)
  err.response = { data: { code, message, data: null } }
  throw err
}

// ============================================================
// API 函数
// ============================================================
import request from '../request'

/**
 * GET /api/v1/admin/users
 * 用户列表查询（支持筛选、分页）
 */
export const getUserList = async ({
  username = '',
  email = '',
  status = '',
  registerStart = '',
  registerEnd = '',
  pageNum = 1,
  pageSize = 10,
} = {}) => {
  if (MOCK_MODE) {
    await delay()
    let filtered = [...mockUsers]
    if (username) filtered = filtered.filter(u => u.username.toLowerCase().includes(username.toLowerCase()))
    if (email) filtered = filtered.filter(u => u.email.toLowerCase().includes(email.toLowerCase()))
    if (status) filtered = filtered.filter(u => u.status === status)
    const total = filtered.length
    const start = (pageNum - 1) * pageSize
    return {
      code: 200,
      message: '查询成功',
      data: {
        pageNum,
        pageSize,
        total,
        records: filtered.slice(start, start + pageSize),
      },
    }
  }
  const params = { pageNum, pageSize }
  if (username) params.username = username
  if (email) params.email = email
  if (status) params.status = status
  if (registerStart) params.registerStart = registerStart
  if (registerEnd) params.registerEnd = registerEnd
  return await request.get('/admin/users', { params })
}

/**
 * PATCH /api/v1/admin/users/{userId}/status
 * 启用/禁用用户
 */
export const toggleUserStatus = async (userId, status) => {
  if (MOCK_MODE) {
    await delay()
    const user = mockUsers.find(u => u.userId === userId)
    if (!user) throwMockError(404, '用户不存在')
    user.status = status
    return {
      code: 200,
      message: '用户状态更新成功',
      data: { userId, status },
    }
  }
  return await request.patch(`/admin/users/${userId}/status`, { status })
}

/**
 * POST /api/v1/admin/users/{userId}/reset-password
 * 重置用户密码（返回临时密码）
 */
export const resetUserPassword = async (userId) => {
  if (MOCK_MODE) {
    await delay()
    const user = mockUsers.find(u => u.userId === userId)
    if (!user) throwMockError(404, '用户不存在')
    const tempPassword = 'Abc@2026'
    return {
      code: 200,
      message: '密码重置成功',
      data: { userId, tempPassword },
    }
  }
  return await request.post(`/admin/users/${userId}/reset-password`)
}

/**
 * GET /api/v1/admin/users/{userId}/logs
 * 查看用户操作日志（支持筛选、分页）
 */
export const getUserLogs = async (
  userId,
  { operationType = '', startTime = '', endTime = '', pageNum = 1, pageSize = 10 } = {},
) => {
  if (MOCK_MODE) {
    await delay(200)
    const user = mockUsers.find(u => u.userId === userId)
    if (!user) throwMockError(404, '用户不存在')
    let filtered = [...mockLogs]
    if (operationType) filtered = filtered.filter(l => l.operationType === operationType)
    const total = filtered.length
    const start = (pageNum - 1) * pageSize
    return {
      code: 200,
      message: '查询成功',
      data: {
        pageNum,
        pageSize,
        total,
        records: filtered.slice(start, start + pageSize),
      },
    }
  }
  const params = { pageNum, pageSize }
  if (operationType) params.operationType = operationType
  if (startTime) params.startTime = startTime
  if (endTime) params.endTime = endTime
  return await request.get(`/admin/users/${userId}/logs`, { params })
}
