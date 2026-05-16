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
const MOCK_MODE = false

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
  return await request.patch(`/admin/users/${userId}/status`, { status })
}

export const resetUserPassword = async (userId) => {
  return await request.post(`/admin/users/${userId}/reset-password`, {})
}

export const getUserLogs = async (
  userId,
  { operationType = '', startTime = '', endTime = '', pageNum = 1, pageSize = 10 } = {},
) => {
  const params = { pageNum, pageSize }
  if (operationType) params.operationType = operationType
  if (startTime) params.startTime = startTime
  if (endTime) params.endTime = endTime
  return await request.get(`/admin/users/${userId}/logs`, { params })
}
