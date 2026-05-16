<script setup>
import { computed, reactive, ref, onMounted } from 'vue'
import { searchComponentsApi, getComponentDetailApi } from '../../api/parameter'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const detailLoading = ref(false)
const tableData = ref([])
const total = ref(0)
const detailVisible = ref(false)
const currentDetail = ref(null)

const queryForm = reactive({
  keyword: '',
  category: '',
  pageNum: 1,
  pageSize: 10,
})

const categoryOptions = [
  { value: '', label: '全部类别' },
  { value: 'MCU', label: 'MCU' },
  { value: '运放', label: '运放' },
  { value: '稳压器', label: '稳压器' },
  { value: '接口芯片', label: '接口芯片' },
  { value: '电阻', label: '电阻' },
  { value: '电容', label: '电容' },
]

const validateSearchCondition = (_rule, _value, callback) => {
  if (!queryForm.keyword.trim() && !queryForm.category) {
    callback(new Error('请输入关键词或选择类别'))
    return
  }
  callback()
}

const rules = {
  keyword: [{ validator: validateSearchCondition, trigger: 'blur' }],
}

const formRef = ref(null)

const pageCount = computed(() => Math.max(1, Math.ceil(total.value / queryForm.pageSize)))

const showingStart = computed(() => (queryForm.pageNum - 1) * queryForm.pageSize + 1)
const showingEnd = computed(() => Math.min(queryForm.pageNum * queryForm.pageSize, total.value))

const getParam = (row, name) => {
  const params = row.coreParams || {}
  for (const [key, value] of Object.entries(params)) {
    if (key.includes(name) || name.includes(key)) return value
  }
  return null
}

const formatCsvCell = (value) => {
  const text = value === null || value === undefined || value === '' ? '—' : String(value)
  return `"${text.replaceAll('"', '""')}"`
}

const handleExportData = () => {
  if (!tableData.value.length) {
    ElMessage.warning('暂无可导出的数据，请先查询元器件参数')
    return
  }

  const headers = ['型号', '厂商', '封装', '额定电压', '额定电流', '功率']
  const rows = tableData.value.map((row) => [
    row.model,
    row.manufacturer,
    row.packageType,
    getParam(row, '额定电压') || getParam(row, '电压'),
    getParam(row, '额定电流') || getParam(row, '电流'),
    getParam(row, '功率'),
  ])

  const csvContent = [headers, ...rows]
    .map((line) => line.map(formatCsvCell).join(','))
    .join('\n')
  const blob = new Blob([`\uFEFF${csvContent}`], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  const keyword = queryForm.keyword.trim() || '全部'
  const timestamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')

  link.href = url
  link.download = `元器件参数_${keyword}_${timestamp}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  ElMessage.success('数据导出成功')
}

const loadList = async () => {
  loading.value = true
  try {
    const res = await searchComponentsApi({ ...queryForm, keyword: queryForm.keyword.trim() })
    const data = res.data || {}
    tableData.value = data.records || []
    total.value = data.total || 0
  } catch (error) {
    ElMessage.error(error.message || '查询失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  queryForm.pageNum = 1
  loadList()
}

const handleReset = () => {
  queryForm.keyword = ''
  queryForm.category = ''
  queryForm.pageNum = 1
  queryForm.pageSize = 10
  tableData.value = []
  total.value = 0
}

const handleCurrentChange = (page) => {
  queryForm.pageNum = page
  loadList()
}

const handleSizeChange = (size) => {
  queryForm.pageSize = size
  queryForm.pageNum = 1
  loadList()
}

const handleViewDetail = async (row) => {
  detailVisible.value = true
  detailLoading.value = true
  try {
    const res = await getComponentDetailApi(row.componentId)
    currentDetail.value = res.data
  } catch (error) {
    ElMessage.error(error.message || '获取详情失败')
  } finally {
    detailLoading.value = false
  }
}

onMounted(() => {
  if (queryForm.keyword) loadList()
})
</script>

<template>
  <div class="parameter-query-page">
    <!-- 搜索区域 -->
    <el-card class="search-card">
      <el-form ref="formRef" :inline="true" :model="queryForm" :rules="rules" class="search-form">
        <el-form-item prop="keyword">
          <el-input
            v-model="queryForm.keyword"
            placeholder="输入元器件型号、厂商或封装..."
            class="keyword-input"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item prop="keyword">
          <el-select v-model="queryForm.category" placeholder="全部类别" class="category-select" clearable>
            <el-option
              v-for="opt in categoryOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleSearch">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="margin-right:5px">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            搜索
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card">
      <div class="table-header-bar">
        <span class="table-title">元器件参数表</span>
        <el-button text type="primary" :disabled="!tableData.length" @click="handleExportData">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:4px">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          导出数据
        </el-button>
      </div>

      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column prop="model" label="型号" min-width="150" sortable />
        <el-table-column prop="manufacturer" label="厂商" min-width="160" />
        <el-table-column prop="packageType" label="封装" min-width="120" />
        <el-table-column label="额定电压" min-width="110" align="center">
          <template #default="{ row }">
            {{ getParam(row, '额定电压') || getParam(row, '电压') || '—' }}
          </template>
        </el-table-column>
        <el-table-column label="额定电流" min-width="110" align="center">
          <template #default="{ row }">
            {{ getParam(row, '额定电流') || getParam(row, '电流') || '—' }}
          </template>
        </el-table-column>
        <el-table-column label="功率" min-width="100" align="center">
          <template #default="{ row }">
            {{ getParam(row, '功率') || '—' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" text @click="handleViewDetail(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-bar">
        <span class="pagination-summary">
          共找到 {{ total }} 条记录，显示第 {{ showingStart }}-{{ showingEnd }} 条
        </span>
        <el-pagination
          background
          :current-page="queryForm.pageNum"
          :page-size="queryForm.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          :page-count="pageCount"
          layout="prev, pager, next, sizes"
          @current-change="handleCurrentChange"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <!-- 详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      title="元器件参数详情"
      width="620px"
      :close-on-click-modal="false"
    >
      <div v-loading="detailLoading" class="detail-content">
        <template v-if="currentDetail">
          <div class="detail-model">{{ currentDetail.model }}</div>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="型号">{{ currentDetail.model }}</el-descriptions-item>
            <el-descriptions-item label="类型">{{ currentDetail.type || '—' }}</el-descriptions-item>
            <el-descriptions-item label="封装">{{ currentDetail.packageType || '—' }}</el-descriptions-item>
            <el-descriptions-item label="厂商">{{ currentDetail.manufacturer || '—' }}</el-descriptions-item>
            <el-descriptions-item label="数据手册">
              <el-link v-if="currentDetail.datasheetUrl" :href="currentDetail.datasheetUrl" target="_blank">
                查看
              </el-link>
              <span v-else>暂无</span>
            </el-descriptions-item>
            <el-descriptions-item label="更新时间">{{ currentDetail.updatedAt || '—' }}</el-descriptions-item>
          </el-descriptions>

          <div v-if="currentDetail.coreParams && Object.keys(currentDetail.coreParams).length" class="params-section">
            <div class="params-title">核心参数</div>
            <el-descriptions :column="2" border>
              <el-descriptions-item
                v-for="(value, key) in currentDetail.coreParams"
                :key="key"
                :label="key"
              >
                {{ value }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </template>
        <el-empty v-else description="暂无数据" />
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.parameter-query-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 搜索区域 */
.search-card {
  background: #fff;
  border-radius: 12px;
}

.search-form {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0;
}

.keyword-input {
  width: 320px;
}

.category-select {
  width: 140px;
}

/* 表格区域 */
.table-card {
  background: #fff;
  border-radius: 12px;
}

.table-header-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.table-title {
  font-size: 17px;
  font-weight: 700;
  color: #1e293b;
}

/* 表格样式 */
:deep(.el-table th) {
  background: #f8fafc !important;
  color: #64748b;
  font-weight: 600;
  font-size: 13px;
  padding: 12px 8px !important;
}

:deep(.el-table td) {
  padding: 12px 8px !important;
  border-bottom: 1px solid #f1f5f9;
}

:deep(.el-table__row:hover > td) {
  background: #f8faff !important;
}

/* 分页 */
.pagination-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid #f1f5f9;
}

.pagination-summary {
  font-size: 13px;
  color: #64748b;
}

/* 详情弹窗 */
.detail-content {
  min-height: 200px;
}

.detail-model {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e2e8f0;
}

.params-section {
  margin-top: 16px;
}

.params-title {
  font-size: 15px;
  font-weight: 600;
  color: #334155;
  margin-bottom: 10px;
  padding-left: 8px;
  border-left: 3px solid #1677ff;
}
</style>
