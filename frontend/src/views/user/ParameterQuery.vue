<script setup>
import { computed, reactive, ref, onMounted } from 'vue'
import {
  searchComponentsApi,
  searchComponentsFallbackApi,
  getComponentDetailApi,
  getComponentDetailFallbackApi,
} from '../../api/parameter'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const detailLoading = ref(false)
const hasRealListApi = ref(true)
const hasRealDetailApi = ref(true)
const tableData = ref([])
const total = ref(0)
const selectedDetail = ref(null)
const queryHistory = ref([])

const queryForm = reactive({
  keyword: '',
  pageNum: 1,
  pageSize: 10,
})

const columns = [
  { prop: 'model', label: '型号' },
  { prop: 'type', label: '类型' },
  { prop: 'packageType', label: '封装' },
  { prop: 'manufacturer', label: '厂商' },
]
const pageCount = computed(() => Math.max(1, Math.ceil(total.value / queryForm.pageSize)))

const saveMessage = (message) => {
  queryHistory.value.unshift({
    time: new Date().toLocaleString(),
    message,
  })
}

const loadList = async () => {
  loading.value = true
  try {
    const keyword = queryForm.keyword.trim()
    const shouldUseFallback = !keyword || !hasRealListApi.value
    const api = shouldUseFallback ? searchComponentsFallbackApi : searchComponentsApi
    // keyword 为空时后端会返回 400，因此空关键词只走写死数据，不调用真实接口
    const res = await api({ ...queryForm, keyword })
    const data = res.data || {}
    tableData.value = data.records || data.list || []
    total.value = data.total || 0

    const message = `查询关键词：${queryForm.keyword || '全部'}，返回 ${total.value} 条结果`
    saveMessage(message)

    if (
      selectedDetail.value &&
      !tableData.value.some((item) => item.componentId === selectedDetail.value.componentId)
    ) {
      selectedDetail.value = null
    }

    if (tableData.value.length && !selectedDetail.value) {
      await handleRowClick(tableData.value[0])
    }
  } catch (error) {
    if (hasRealListApi.value) {
      hasRealListApi.value = false
      ElMessage.warning('真实查询接口暂不可用，已切换为写死数据占位')
      return loadList()
    }           //如果真实接口报错
    ElMessage.error(error.message || '查询失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  queryForm.pageNum = 1
  loadList()
}

const handleReset = () => {
  queryForm.keyword = ''
  queryForm.pageNum = 1
  queryForm.pageSize = 10
  loadList()
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

const handleRowClick = async (row) => {
  detailLoading.value = true
  try {
    const api = hasRealDetailApi.value ? getComponentDetailApi : getComponentDetailFallbackApi
    const res = await api(row.componentId)
    selectedDetail.value = res.data
  } catch (error) {
    if (hasRealDetailApi.value) {
      hasRealDetailApi.value = false
      ElMessage.warning('元器件详情接口暂不可用，已切换为写死数据占位')
      const fallbackRes = await getComponentDetailFallbackApi(row.componentId)
      selectedDetail.value = fallbackRes.data
      return
    }
    ElMessage.error(error.message || '获取详情失败')
  } finally {
    detailLoading.value = false
  }
}

onMounted(() => {
  loadList()
})
</script>

<template>
  <div class="parameter-query-page">
    <el-card class="query-card">
      <template #header>
        <div class="card-header">
          <span>参数查询</span>
          <span class="hint">支持真实接口联调，若接口未就绪则自动回退写死数据</span>
        </div>
      </template>

      <el-form :inline="true" :model="queryForm" class="query-form">
        <el-form-item label="型号/关键词">
          <el-input v-model="queryForm.keyword" placeholder="如 STM32、LM358" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-row :gutter="16" class="content-grid">
      <el-col :span="15">
        <el-card>
          <template #header>
            <div class="table-header">
              <span>查询结果</span>
              <span class="meta">共 {{ total }} 条</span>
            </div>
          </template>

          <el-table
            :data="tableData"
            v-loading="loading"
            border
            stripe
            highlight-current-row
            @row-click="handleRowClick"
          >
            <el-table-column
              v-for="column in columns"
              :key="column.prop"
              :prop="column.prop"
              :label="column.label"
              min-width="120"
            />
          </el-table>

          <div class="pagination-wrap">
            <el-pagination
              background
              layout="total, sizes, prev, pager, next, jumper"
              :current-page="queryForm.pageNum"
              :page-size="queryForm.pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="total"
              :page-count="pageCount"
              @current-change="handleCurrentChange"
              @size-change="handleSizeChange"
            />
          </div>
        </el-card>
      </el-col>

      <el-col :span="9">
        <el-card class="detail-card">
          <template #header>
            <div class="table-header">
              <span>参数详情</span>
              <span class="meta">点击左侧结果查看</span>
            </div>
          </template>

          <div v-loading="detailLoading" class="detail-body">
            <template v-if="selectedDetail">
              <div class="detail-title">
                {{ selectedDetail.model }}
              </div>
              <el-descriptions :column="1" border>
                <el-descriptions-item label="型号">{{ selectedDetail.model }}</el-descriptions-item>
                <el-descriptions-item label="类型">{{ selectedDetail.type }}</el-descriptions-item>
                <el-descriptions-item label="封装">{{ selectedDetail.packageType }}</el-descriptions-item>
                <el-descriptions-item label="厂商">{{ selectedDetail.manufacturer }}</el-descriptions-item>
                <el-descriptions-item label="数据手册">
                  <el-link v-if="selectedDetail.datasheetUrl" :href="selectedDetail.datasheetUrl" target="_blank">
                    查看
                  </el-link>
                  <span v-else>暂无</span>
                </el-descriptions-item>
                <el-descriptions-item label="图片">
                  <span>{{ selectedDetail.imageUrl || '暂无' }}</span>
                </el-descriptions-item>
                <el-descriptions-item label="创建时间">{{ selectedDetail.updatedAt }}</el-descriptions-item>
              </el-descriptions>

              <div class="params-title">核心参数</div>
              <el-descriptions :column="1" border>
                <el-descriptions-item
                  v-for="(value, key) in selectedDetail.coreParams"
                  :key="key"
                  :label="key"
                >
                  {{ value }}
                </el-descriptions-item>
              </el-descriptions>
            </template>

            <el-empty v-else description="请选择左侧某个型号查看详情" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="history-card">
      <template #header>
        <div class="table-header">
          <span>查询历史</span>
          <span class="meta">保存最近查询记录</span>
        </div>
      </template>
      <el-timeline v-if="queryHistory.length">
        <el-timeline-item v-for="(item, index) in queryHistory" :key="index" :timestamp="item.time">
          {{ item.message }}
        </el-timeline-item>
      </el-timeline>
      <el-empty v-else description="暂无查询记录" />
    </el-card>
  </div>
</template>

<style scoped>
.parameter-query-page {
  display: grid;
  gap: 16px;
}

.card-header,
.table-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.hint,
.meta {
  color: #6b7280;
  font-size: 13px;
}

.query-form {
  margin-bottom: -8px;
}

.content-grid {
  align-items: stretch;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.detail-card,
.detail-body {
  height: 100%;
}

.detail-body {
  display: grid;
  gap: 16px;
}

.detail-title {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.params-title {
  font-size: 15px;
  font-weight: 600;
  color: #334155;
}

.history-card {
  margin-top: 4px;
}
</style>
