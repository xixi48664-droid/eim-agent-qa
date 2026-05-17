<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getMonitorOverview, getMonitorTrend, getServiceList, refreshMonitor } from '../../api/admin/monitor'

const loading = ref(false)
const refreshing = ref(false)
const overview = ref(null)
const trend = ref({ requestTrend: [], responseTimeTrend: [] })
const services = ref([])
const lastRefresh = ref('')

// 自动刷新定时器
let autoRefreshTimer = null

// 加载所有监控数据
const fetchData = async () => {
  loading.value = true
  try {
    const [overviewRes, trendRes, serviceRes] = await Promise.all([
      getMonitorOverview(),
      getMonitorTrend(),
      getServiceList(),
    ])
    overview.value = overviewRes.data
    trend.value = trendRes.data
    services.value = serviceRes.data.list
    lastRefresh.value = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch (e) {
    ElMessage.error(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

// 手动刷新
const handleRefresh = async () => {
  refreshing.value = true
  try {
    await refreshMonitor()
    await fetchData()
    ElMessage.success('刷新成功')
  } catch (e) {
    ElMessage.error(e.message || '刷新失败')
  } finally {
    refreshing.value = false
  }
}

// 状态颜色
const statusClass = (status) => {
  if (status === 'running') return 'status-running'
  if (status === 'warning') return 'status-warning'
  return 'status-stopped'
}

// 绘制简单柱状图（Canvas）
const drawBarChart = (canvasId, data, color) => {
  const canvas = document.getElementById(canvasId)
  if (!canvas) return
  const container = canvas.parentElement
  const W = container ? container.clientWidth : canvas.width
  const H = 160
  canvas.width = W * window.devicePixelRatio
  canvas.height = H * window.devicePixelRatio
  canvas.style.width = W + 'px'
  canvas.style.height = H + 'px'
  const ctx = canvas.getContext('2d')
  ctx.scale(window.devicePixelRatio, window.devicePixelRatio)
  ctx.clearRect(0, 0, W, H)

  if (!data || data.length === 0) return

  const maxVal = Math.max(...data.map(d => d.value))
  const barWidth = (W - 40) / data.length - 4
  const paddingLeft = 20
  const paddingBottom = 24

  data.forEach((d, i) => {
    const barH = ((d.value / maxVal) * (H - paddingBottom - 20))
    const x = paddingLeft + i * ((W - 40) / data.length)
    const y = H - paddingBottom - barH

    ctx.fillStyle = color
    ctx.beginPath()
    ctx.roundRect(x, y, barWidth, barH, [3, 3, 0, 0])
    ctx.fill()

    // 底部时间标签
    ctx.fillStyle = '#94a3b8'
    ctx.font = '10px Inter, sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(d.label, x + barWidth / 2, H - 6)
  })
}

// 绘制折线图
const drawLineChart = (canvasId, data, color) => {
  const canvas = document.getElementById(canvasId)
  if (!canvas) return
  const container = canvas.parentElement
  const W = container ? container.clientWidth : canvas.width
  const H = 160
  canvas.width = W * window.devicePixelRatio
  canvas.height = H * window.devicePixelRatio
  canvas.style.width = W + 'px'
  canvas.style.height = H + 'px'
  const ctx = canvas.getContext('2d')
  ctx.scale(window.devicePixelRatio, window.devicePixelRatio)
  ctx.clearRect(0, 0, W, H)

  if (!data || data.length === 0) return

  const maxVal = Math.max(...data.map(d => d.value))
  const minVal = Math.min(...data.map(d => d.value))
  const range = maxVal - minVal || 1
  const paddingLeft = 20
  const paddingBottom = 24
  const paddingTop = 10

  // 绘制折线
  ctx.strokeStyle = color
  ctx.lineWidth = 2.5
  ctx.lineJoin = 'round'
  ctx.lineCap = 'round'
  ctx.beginPath()

  data.forEach((d, i) => {
    const x = paddingLeft + i * ((W - 40) / (data.length - 1))
    const y = H - paddingBottom - ((d.value - minVal) / range) * (H - paddingTop - paddingBottom)
    if (i === 0) ctx.moveTo(x, y)
    else ctx.lineTo(x, y)
  })
  ctx.stroke()

  // 绘制数据点
  data.forEach((d, i) => {
    const x = paddingLeft + i * ((W - 40) / (data.length - 1))
    const y = H - paddingBottom - ((d.value - minVal) / range) * (H - paddingTop - paddingBottom)
    ctx.fillStyle = '#fff'
    ctx.beginPath()
    ctx.arc(x, y, 3.5, 0, Math.PI * 2)
    ctx.fill()
    ctx.strokeStyle = color
    ctx.lineWidth = 2
    ctx.stroke()

    // 底部标签
    ctx.fillStyle = '#94a3b8'
    ctx.font = '10px Inter, sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(d.label, x, H - 6)
  })

  // Y轴范围
  ctx.fillStyle = '#94a3b8'
  ctx.font = '10px Inter, sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText(maxVal, 0, paddingTop + 2)
  ctx.fillText(minVal, 0, H - paddingBottom)
}

const redrawCharts = () => {
  if (trend.value.requestTrend?.length) {
    drawBarChart('request-chart', trend.value.requestTrend, '#3b82f6')
  }
  if (trend.value.responseTimeTrend?.length) {
    drawLineChart('response-chart', trend.value.responseTimeTrend, '#10b981')
  }
}

let chartTimer = null
let resizeObserver = null

const scheduleChartDraw = () => {
  if (chartTimer) clearTimeout(chartTimer)
  chartTimer = setTimeout(redrawCharts, 100)
}

onMounted(async () => {
  await fetchData()
  scheduleChartDraw()

  // 监听容器大小变化重绘图表
  resizeObserver = new ResizeObserver(() => {
    scheduleChartDraw()
  })
  const requestChart = document.getElementById('request-chart')
  const responseChart = document.getElementById('response-chart')
  if (requestChart) resizeObserver.observe(requestChart.parentElement)
  if (responseChart) resizeObserver.observe(responseChart.parentElement)

  // 每60秒自动刷新一次
  autoRefreshTimer = setInterval(async () => {
    try {
      await refreshMonitor()
      await fetchData()
      scheduleChartDraw()
    } catch (e) {
      // silent
    }
  }, 60000)
})

onUnmounted(() => {
  if (autoRefreshTimer) clearInterval(autoRefreshTimer)
  if (chartTimer) clearTimeout(chartTimer)
  if (resizeObserver) resizeObserver.disconnect()
})

// 监听 trend 变化重绘图表
watch(() => trend.value, scheduleChartDraw, { deep: true })
</script>

<template>
  <div class="admin-monitor" v-loading="loading">
    <!-- 系统状态 & 刷新 -->
    <div class="status-bar">
      <div class="status-indicator">
        <span class="status-dot running"></span>
        <span class="status-text">{{ overview?.systemStatusLabel || '加载中...' }}</span>
      </div>
      <div class="refresh-bar">
        <span class="refresh-time">最后刷新：{{ lastRefresh }}</span>
        <el-button :loading="refreshing" @click="handleRefresh" size="small">
          <svg v-if="!refreshing" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:4px">
            <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
          </svg>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 指标卡片 -->
    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-label">当前 QPS</div>
        <div class="metric-value">{{ overview?.qps || '—' }}</div>
        <div class="metric-change" :class="overview?.qpsChange?.startsWith('+') ? 'up' : 'down'">
          较昨日 {{ overview?.qpsChange || '—' }}
        </div>
      </div>
      <div class="metric-card">
        <div class="metric-label">平均响应时间 (ms)</div>
        <div class="metric-value">{{ overview?.avgResponseTime || '—' }}</div>
        <div class="metric-change" :class="overview?.responseTimeChange?.startsWith('-') ? 'up' : 'down'">
          较昨日 {{ overview?.responseTimeChange || '—' }}
        </div>
      </div>
      <div class="metric-card">
        <div class="metric-label">错误率 (%)</div>
        <div class="metric-value">{{ overview?.errorRate || '—' }}</div>
        <div class="metric-change good">{{ overview?.errorRateStatus || '—' }}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">在线用户数</div>
        <div class="metric-value">{{ overview?.onlineUsers || '—' }}</div>
        <div class="metric-change good">峰值 {{ overview?.peakUsers || '—' }} 人</div>
      </div>
    </div>

    <!-- 趋势图 -->
    <div class="charts-row">
      <div class="chart-card">
        <div class="chart-title">今日请求量（近12小时）</div>
        <div class="chart-area">
          <canvas id="request-chart"></canvas>
        </div>
      </div>
      <div class="chart-card">
        <div class="chart-title">响应时间趋势（ms）</div>
        <div class="chart-area" v-if="trend.responseTimeTrend && trend.responseTimeTrend.length">
          <canvas id="response-chart"></canvas>
        </div>
        <div class="chart-area chart-empty" v-else>
          <span class="empty-text">暂无逐小时响应时间数据</span>
          <span class="empty-sub">后端不支持此统计维度，当前仅提供汇总均值</span>
        </div>
      </div>
    </div>

    <!-- 微服务状态表 -->
    <div class="service-table-card">
      <div class="section-header">
        <span class="section-title">微服务状态</span>
      </div>
      <el-table :data="services" stripe>
        <el-table-column prop="name" label="服务名称" min-width="130" />
        <el-table-column prop="statusLabel" label="状态" width="110" align="center">
          <template #default="{ row }">
            <span :class="['service-status', statusClass(row.status)]">{{ row.statusLabel }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" width="80" align="center" />
        <el-table-column prop="cpu" label="CPU 使用率" width="130" align="center">
          <template #default="{ row }">
            <div class="progress-cell">
              <span class="progress-text">{{ row.cpu }}%</span>
              <el-progress :percentage="row.cpu" :stroke-width="6" :show-text="false"
                :color="row.cpu > 80 ? '#ef4444' : row.cpu > 60 ? '#f59e0b' : '#3b82f6'" />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="memory" label="内存使用率" width="130" align="center">
          <template #default="{ row }">
            <div class="progress-cell">
              <span class="progress-text">{{ row.memory }}%</span>
              <el-progress :percentage="row.memory" :stroke-width="6" :show-text="false"
                :color="row.memory > 80 ? '#ef4444' : row.memory > 60 ? '#f59e0b' : '#10b981'" />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="requests" label="今日请求" width="110" align="center">
          <template #default="{ row }">
            <span class="requests-num">{{ row.requests.toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="errorRate" label="错误率" width="90" align="center">
          <template #default="{ row }">
            <span :class="['error-rate', parseFloat(row.errorRate) > 1 ? 'high' : '']">{{ row.errorRate }}</span>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.admin-monitor {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 状态栏 */
.status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.status-dot.running { background: #22c55e; box-shadow: 0 0 6px rgba(34, 197, 94, 0.5); }
.status-dot.warning { background: #f59e0b; box-shadow: 0 0 6px rgba(245, 158, 11, 0.5); }
.status-dot.stopped { background: #ef4444; box-shadow: 0 0 6px rgba(239, 68, 68, 0.5); }

.status-text {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}

.refresh-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.refresh-time {
  font-size: 13px;
  color: #64748b;
}

/* 指标卡片 */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.metric-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.metric-label {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 10px;
  font-weight: 500;
}

.metric-value {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 6px;
  line-height: 1;
}

.metric-change {
  font-size: 12px;
  color: #64748b;
}

.metric-change.up { color: #16a34a; }
.metric-change.down { color: #dc2626; }
.metric-change.good { color: #16a34a; }

/* 趋势图 */
.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.chart-card {
  background: #fff;
  border-radius: 12px;
  padding: 18px 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.chart-title {
  font-size: 14px;
  font-weight: 600;
  color: #334155;
  margin-bottom: 14px;
}

.chart-area {
  width: 100%;
  overflow: hidden;
}

.chart-area canvas {
  width: 100% !important;
  height: auto;
}

.chart-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 160px;
  gap: 6px;
}

.empty-text {
  font-size: 14px;
  color: #94a3b8;
  font-weight: 500;
}

.empty-sub {
  font-size: 12px;
  color: #cbd5e1;
}

/* 服务状态表 */
.service-table-card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.section-header {
  padding: 16px 20px;
  border-bottom: 1px solid #f1f5f9;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}

:deep(.el-table th) {
  background: #f8fafc !important;
  color: #64748b;
  font-weight: 600;
  font-size: 13px;
  padding: 11px 8px !important;
}

:deep(.el-table td) {
  padding: 12px 8px !important;
  border-bottom: 1px solid #f1f5f9;
}

.service-status {
  font-size: 13px;
  font-weight: 600;
}

.status-running { color: #16a34a; }
.status-warning { color: #d97706; }
.status-stopped { color: #ef4444; }

.progress-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: flex-end;
}

.progress-text {
  font-size: 12px;
  color: #334155;
  font-weight: 600;
}

:deep(.el-progress-bar__outer) {
  border-radius: 4px;
}

.requests-num {
  font-weight: 600;
  color: #334155;
}

.error-rate {
  font-size: 13px;
  font-weight: 500;
  color: #16a34a;
}

.error-rate.high {
  color: #dc2626;
}
</style>
