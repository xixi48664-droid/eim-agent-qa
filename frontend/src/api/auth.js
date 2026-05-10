/**
 * 用户认证 API（严格按接口文档 V1.0）
 * 路由前缀：/api/v1/auth
 *
 * 响应结构：{ code: 200, message: 'success', data: { token, userId, account, role, status } }
 */
import request from './request'

/**
 * POST /api/v1/auth/login
 * 请求：{ account, password }
 * 成功响应：{ code: 200, data: { token, userId, account, role, status } }
 */
export const loginApi = ({ account, password }) => {
  return request.post('/auth/login', { account, password })
}

/**
 * POST /api/v1/auth/register
 * 请求：{ account, password, role }
 * 成功响应：{ code: 200, data: { userId, account, role } }
 */
export const registerApi = ({ account, password, role = 'user' }) => {
  return request.post('/auth/register', { account, password, role })
}

/**
 * POST /api/v1/auth/reset-password
 * 请求：{ account, newPassword }
 * 成功响应：{ code: 200, data: { message: '密码重置成功' } }
 */
export const resetPasswordApi = ({ account, newPassword }) => {
  return request.post('/auth/reset-password', { account, newPassword })
}

/**
 * GET /api/v1/auth/detail
 * 请求：{ userId }
 * 成功响应：{ code: 200, data: { userId, account, nickname, role, status, createdAt } }
 */
export const getUserDetailApi = ({ userId }) => {
  return request.get('/auth/detail', { params: { userId } })
}
