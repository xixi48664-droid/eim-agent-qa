/**
 * 用户认证 API（严格按接口文档 V1.0）
 * 路由前缀：/api/v1/auth
 *
 * 响应结构：{ code: 200, message: 'success', data: { token, userId, account, role, status } }
 */
import request from './request'

// ============================================================
// Mock 数据（后端未部署时，使用本地 mock 响应）
// ============================================================
const MOCK_MODE = true // 切换为 false 对接真实后端

const delay = (ms = 300) => new Promise(resolve => setTimeout(resolve, ms))

// Mock 用户数据库（key = account，即邮箱或手机号）
const mockUsers = {
  'admin@example.com': {
    password: '123456',
    userId: 1,
    account: 'admin@example.com',
    nickname: '陈管理员',
    role: 'admin',
    status: 'enabled',
  },
  'user@example.com': {
    password: '123456',
    userId: 2,
    account: 'user@example.com',
    nickname: '张工程师',
    role: 'user',
    status: 'enabled',
  },
  '13800138000': {
    password: '123456',
    userId: 3,
    account: '13800138000',
    nickname: '李技术员',
    role: 'user',
    status: 'enabled',
  },
  'disabled@example.com': {
    password: '123456',
    userId: 4,
    account: 'disabled@example.com',
    nickname: '已禁用用户',
    role: 'user',
    status: 'disabled',
  },
}

const MOCK_TOKEN = 'eyJhbGciOiJIUzI1NiJ9.mock-token'

// 生成 JWT mock（格式参考，实际 token 由后端 FastAPI 生成）
const generateMockToken = (user) => {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }))
  const payload = btoa(JSON.stringify({
    sub: user.userId,
    account: user.account,
    role: user.role,
    exp: Math.floor(Date.now() / 1000) + 86400,
  }))
  const signature = btoa('mock-signature')
  return `${header}.${payload}.${signature}`
}

// ============================================================
// API 函数
// ============================================================

/**
 * POST /api/v1/auth/login
 * 请求：{ account, password }
 * 成功响应：{ code: 200, data: { token, userId, account, role, status } }
 */
export const loginApi = async ({ account, password }) => {
  if (MOCK_MODE) {
    await delay()
    const user = mockUsers[account]
    if (!user) {
      const err = new Error('账号或密码错误')
      err.response = { data: { code: 401, message: '账号或密码错误', data: null } }
      throw err
    }
    if (user.password !== password) {
      const err = new Error('账号或密码错误')
      err.response = { data: { code: 401, message: '账号或密码错误', data: null } }
      throw err
    }
    if (user.status === 'disabled') {
      const err = new Error('账号已被禁用，请联系管理员')
      err.response = { data: { code: 401, message: '账号已被禁用，请联系管理员', data: null } }
      throw err
    }
    return {
      code: 200,
      message: '登录成功',
      data: {
        token: generateMockToken(user),
        userId: user.userId,
        account: user.account,
        nickname: user.nickname,
        role: user.role,
        status: user.status,
      },
    }
  }
  return await request.post('/auth/login', { account, password })
}

/**
 * POST /api/v1/auth/register
 * 当前 MVP 阶段保留接口定义，实际注册流程待实现
 */
export const registerApi = async ({ account, password, role = 'user' }) => {
  if (MOCK_MODE) {
    await delay()
    if (mockUsers[account]) {
      const err = new Error('该账号已注册')
      err.response = { data: { code: 400, message: '该账号已注册', data: null } }
      throw err
    }
    const userId = Object.keys(mockUsers).length + 1
    mockUsers[account] = { password, userId, account, nickname: account, role, status: 'enabled' }
    return {
      code: 200,
      message: '注册成功',
      data: { userId, account, role },
    }
  }
  return await request.post('/auth/register', { account, password, role })
}

/**
 * POST /api/v1/auth/reset-password
 * 请求：{ account, newPassword }
 * 成功响应：{ code: 200, data: { message: '密码重置成功' } }
 */
export const resetPasswordApi = async ({ account, newPassword }) => {
  if (MOCK_MODE) {
    await delay()
    if (!mockUsers[account]) {
      const err = new Error('账号不存在')
      err.response = { data: { code: 404, message: '账号不存在', data: null } }
      throw err
    }
    mockUsers[account].password = newPassword
    return {
      code: 200,
      message: '密码重置成功',
      data: { message: '密码重置成功' },
    }
  }
  return await request.post('/auth/reset-password', { account, newPassword })
}

/**
 * GET /api/v1/auth/detail
 * 请求：{ userId }
 * 成功响应：{ code: 200, data: { userId, account, nickname, role, status, createdAt } }
 */
export const getUserDetailApi = async ({ userId }) => {
  if (MOCK_MODE) {
    await delay()
    const user = Object.values(mockUsers).find(u => u.userId === userId)
    if (!user) {
      const err = new Error('用户不存在')
      err.response = { data: { code: 404, message: '用户不存在', data: null } }
      throw err
    }
    return {
      code: 200,
      message: 'success',
      data: {
        userId: user.userId,
        account: user.account,
        nickname: user.nickname,
        role: user.role,
        status: user.status,
        createdAt: '2024-01-15 08:30:00',
      },
    }
  }
  return await request.get('/auth/detail', { params: { userId } })
}
