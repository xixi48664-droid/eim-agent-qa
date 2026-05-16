/**
 * 服务监控 API — 后端 GET /api/v1/admin/monitor
 */
import request from '../request'

const serviceNameMap = {
  modelService: '问答引擎',
  ocrService: '图像识别',
  vectorStore: '知识库检索',
  fileStorage: '规范解析',
  database: '用户认证',
}

const serviceVersionMap = {
  modelService: 'v2.4.1',
  ocrService: 'v1.8.3',
  vectorStore: 'v3.1.0',
  fileStorage: 'v1.5.2',
  database: 'v2.2.0',
}

let cachedData = null

const fetchMonitorData = async () => {
  const res = await request.get('/admin/monitor')
  cachedData = res.data
  return cachedData
}

const toServiceItem = (key, svc) => ({
  id: key,
  name: serviceNameMap[key] || key,
  version: serviceVersionMap[key] || '—',
  status: svc?.status === 'available' ? 'running' : svc?.status === 'degraded' ? 'warning' : 'stopped',
  statusLabel: svc?.status === 'available' ? '● 运行中' : svc?.status === 'degraded' ? '⚠ 警告' : '✕ 不可用',
  cpu: svc?.cpu ?? 0,
  memory: svc?.memory ?? 0,
  requests: svc?.requests ?? 0,
  errorRate: svc?.errorRate ?? '0.00%',
})

/**
 * 获取监控概览
 */
export const getMonitorOverview = async () => {
  const data = cachedData || await fetchMonitorData()
  return {
    code: 200,
    data: {
      systemStatus: data.overall === 'healthy' ? 'running' : 'warning',
      systemStatusLabel: data.overall === 'healthy' ? '系统运行正常' : '部分服务异常',
      lastRefresh: data.checkedAt || '—',
      qps: data.apiStats?.qps ?? '—',
      qpsChange: '—',
      avgResponseTime: data.latencyStats?.avgMs ?? '—',
      responseTimeChange: '—',
      errorRate: data.recentErrors?.total ?? 0,
      errorRateStatus: (data.recentErrors?.total ?? 0) > 10 ? '超过阈值' : '低于阈值',
      onlineUsers: '—',
      peakUsers: '—',
    },
  }
}

/**
 * 获取趋势数据
 *
 * 说明：后端 GET /admin/monitor 的 timeSeries 提供逐小时请求量（用于柱状图）。
 * 后端目前不返回逐小时响应时间序列（仅 latencyStats.avgMs 汇总值），
 * 因此 responseTimeTrend 为空；后续后端新增接口后可自动展示。
 */
export const getMonitorTrend = async () => {
  const data = cachedData || await fetchMonitorData()
  const series = data.timeSeries || []
  const latencySeries = data.latencyTimeSeries || []
  return {
    code: 200,
    data: {
      requestTrend: series.map(p => ({ label: p.time?.substring(11, 16) || p.time || '—', value: p.count })),
      responseTimeTrend: latencySeries.map(p => ({ label: p.time?.substring(11, 16) || p.time || '—', value: p.avgMs })),
    },
  }
}

/**
 * 获取微服务状态列表
 */
export const getServiceList = async () => {
  const data = cachedData || await fetchMonitorData()
  const services = data.services || {}
  const list = Object.entries(services).map(([key, svc]) => toServiceItem(key, svc))
  return { code: 200, data: { list } }
}

/**
 * 刷新监控数据
 */
export const refreshMonitor = async () => {
  await fetchMonitorData()
  return { code: 200, message: '刷新成功', data: { timestamp: new Date().toISOString() } }
}
