/**
 * 服务监控 API - Mock 数据
 */

const delay = (ms = 300) => new Promise(resolve => setTimeout(resolve, ms))

// 模拟微服务状态数据
let mockServices = [
  { id: 1, name: '问答引擎', version: 'v2.4.1', status: 'running', statusLabel: '● 运行中', cpu: 68, memory: 52, requests: 18432, errorRate: '0.08%' },
  { id: 2, name: '图像识别', version: 'v1.8.3', status: 'running', statusLabel: '● 运行中', cpu: 45, memory: 38, requests: 4218, errorRate: '0.21%' },
  { id: 3, name: '知识库检索', version: 'v3.1.0', status: 'running', statusLabel: '● 运行中', cpu: 31, memory: 61, requests: 22106, errorRate: '0.05%' },
  { id: 4, name: '规范解析', version: 'v1.5.2', status: 'warning', statusLabel: '⚠ 警告', cpu: 88, memory: 74, requests: 8503, errorRate: '1.42%' },
  { id: 5, name: '用户认证', version: 'v2.2.0', status: 'running', statusLabel: '● 运行中', cpu: 18, memory: 25, requests: 1284, errorRate: '0.00%' },
]

// 模拟请求量趋势数据（过去12小时）
const generateRequestTrend = () => {
  const hours = []
  const now = new Date()
  for (let i = 11; i >= 0; i--) {
    const h = new Date(now.getTime() - i * 3600000)
    hours.push({
      label: `${h.getHours().toString().padStart(2, '0')}:00`,
      value: Math.floor(Math.random() * 3000 + 500),
    })
  }
  return hours
}

// 模拟响应时间趋势数据
const generateResponseTimeTrend = () => {
  const hours = []
  const now = new Date()
  for (let i = 11; i >= 0; i--) {
    const h = new Date(now.getTime() - i * 3600000)
    hours.push({
      label: `${h.getHours().toString().padStart(2, '0')}:00`,
      value: Math.floor(Math.random() * 100 + 150),
    })
  }
  return hours
}

/**
 * 获取监控概览数据
 */
export const getMonitorOverview = async () => {
  await delay(200)
  return {
    code: 0,
    message: 'success',
    data: {
      systemStatus: 'running',
      systemStatusLabel: '系统运行正常',
      lastRefresh: '刚刚',
      qps: 42.6,
      qpsChange: '+8.3%',
      avgResponseTime: 186,
      responseTimeChange: '-12ms',
      errorRate: 0.12,
      errorRateStatus: '低于阈值',
      onlineUsers: 38,
      peakUsers: 112,
    },
  }
}

/**
 * 获取趋势数据
 */
export const getMonitorTrend = async () => {
  await delay(200)
  return {
    code: 0,
    message: 'success',
    data: {
      requestTrend: generateRequestTrend(),
      responseTimeTrend: generateResponseTimeTrend(),
    },
  }
}

/**
 * 获取微服务状态列表
 */
export const getServiceList = async () => {
  await delay()
  return {
    code: 0,
    message: 'success',
    data: { list: mockServices },
  }
}

/**
 * 刷新监控数据
 */
export const refreshMonitor = async () => {
  await delay(500)
  // 模拟数据小幅波动
  mockServices = mockServices.map(s => ({
    ...s,
    cpu: Math.max(10, Math.min(95, s.cpu + Math.floor(Math.random() * 10 - 5))),
    memory: Math.max(10, Math.min(95, s.memory + Math.floor(Math.random() * 10 - 5))),
    requests: s.requests + Math.floor(Math.random() * 200 - 100),
  }))
  return {
    code: 0,
    message: '刷新成功',
    data: { timestamp: new Date().toISOString() },
  }
}
