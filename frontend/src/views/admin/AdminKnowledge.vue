<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getKnowledgeList, addKnowledge, updateKnowledge, deleteKnowledge, syncKnowledge, exportKnowledge, importKnowledge, typeOptions } from '../../api/admin/knowledge'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchKeyword = ref('')
const activeType = ref('all')

const syncLoading = ref(false)
const syncingId = ref(null)

// 分类选项（与原型一致）
const typeTabs = [
  { value: 'all', label: '全部' },
  { value: 'product', label: '产品文档' },
  { value: 'standard', label: '行业规范' },
  { value: 'param', label: '参数数据' },
  { value: 'process', label: '工艺流程' },
]

// 新增/编辑弹窗
const dialogVisible = ref(false)
const dialogTitle = ref('新增知识库')
const formRef = ref(null)
const submitting = ref(false)
const editingId = ref(null)

const form = reactive({
  name: '',
  type: 'product',
  description: '',
})

const formRules = {
  name: [{ required: true, message: '请输入知识库名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择知识库类型', trigger: 'change' }],
}

// 加载数据
const fetchData = async () => {
  loading.value = true
  try {
    const res = await getKnowledgeList({
      search: searchKeyword.value,
      type: activeType.value,
      pageNum: currentPage.value,
      pageSize: pageSize.value,
    })
    tableData.value = res.data.records || []
    total.value = res.data.total || 0
  } catch {
    // 错误由拦截器统一处理
  } finally {
    loading.value = false
  }
}

// 分类切换
const handleTypeChange = (type) => {
  activeType.value = type
  currentPage.value = 1
  fetchData()
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1
  fetchData()
}

// 分页
const handlePageChange = (page) => {
  currentPage.value = page
  fetchData()
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  fetchData()
}

// 新增
const openAddDialog = () => {
  editingId.value = null
  dialogTitle.value = '新增知识库'
  Object.assign(form, { name: '', type: 'product', description: '' })
  dialogVisible.value = true
}

// 编辑
const handleEdit = (row) => {
  editingId.value = row.id
  dialogTitle.value = '编辑知识库'
  Object.assign(form, { name: row.name, type: row.type, description: '' })
  dialogVisible.value = true
}

// 提交表单
const handleSubmit = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    if (editingId.value) {
      await updateKnowledge(editingId.value, { name: form.name, type: form.type })
      ElMessage.success('更新成功')
    } else {
      await addKnowledge({ name: form.name, type: form.type })
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch {
    // 错误由拦截器统一处理
  } finally {
    submitting.value = false
  }
}

// 删除
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除知识库「${row.name}」吗？`, '删除知识库', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteKnowledge(row.id, row)
    ElMessage.success('删除成功')
    fetchData()
  } catch {
    // 用户取消或错误由拦截器处理
  }
}

// 同步
const handleSync = async (row) => {
  syncingId.value = row.id
  try {
    await syncKnowledge(row.id)
    ElMessage.success('同步完成')
    fetchData()
  } catch {
    // 错误由拦截器统一处理
  } finally {
    syncingId.value = null
  }
}

// 导入
const importInputRef = ref(null)
const handleImport = () => {
  importInputRef.value?.click()
}

const handleImportFile = async (event) => {
  const file = event.target.files?.[0]
  if (!file) return
  try {
    const formData = new FormData()
    formData.append('file', file)
    await importKnowledge(formData)
    ElMessage.success('导入成功')
    fetchData()
  } catch {
    // 错误由拦截器处理
  } finally {
    // 重置 input 以允许重复选择同一文件
    event.target.value = ''
  }
}

// 导出
const exportLoading = ref(false)
const handleExport = async () => {
  try {
    await ElMessageBox.confirm('确定要导出所有知识库吗？', '导出知识库', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })
    exportLoading.value = true
    const ids = tableData.value.map(t => t.id)
    const blob = await exportKnowledge(ids)
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `知识库导出_${new Date().toISOString().substring(0, 10)}.xlsx`
    link.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch {
    // 用户取消或错误由拦截器处理
  } finally {
    exportLoading.value = false
  }
}

// 状态标签
const statusClass = (status) => status === 'active' ? 'status-active' : 'status-disabled'
const statusText = (status) => status === 'active' ? '● 已启用' : '○ 已停用'

// 类型颜色
const typeTagClass = (type) => ({
  product: 'tag-blue',
  standard: 'tag-purple',
  param: 'tag-orange',
  process: 'tag-green',
}[type] || 'tag-default')

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="admin-knowledge">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-title">
        <h2>知识库管理</h2>
        <span class="total-count">共 {{ total }} 条知识条目</span>
      </div>
      <div class="header-actions">
        <input
          ref="importInputRef"
          type="file"
          accept=".json,.xlsx,.xls"
          style="display:none"
          @change="handleImportFile"
        />
        <el-button @click="handleImport">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:4px">
            <polyline points="8 17 12 21 16 17"/><line x1="12" y1="12" x2="12" y2="21"/>
            <path d="M20.88 18.09A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.29"/>
          </svg>
          导入
        </el-button>
        <el-button :loading="exportLoading" @click="handleExport">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:4px">
            <polyline points="8 17 12 21 16 17"/><line x1="12" y1="12" x2="12" y2="21"/>
            <path d="M3 15V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10"/>
          </svg>
          导出
        </el-button>
        <el-button type="primary" @click="openAddDialog">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="margin-right:4px">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          新增
        </el-button>
      </div>
    </div>

    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索知识库名称或关键词..."
        class="search-input"
        clearable
        @clear="handleSearch"
        @keyup.enter="handleSearch"
      >
        <template #prefix>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
        </template>
      </el-input>
      <el-button type="primary" @click="handleSearch">搜索</el-button>
    </div>

    <!-- 分类标签 -->
    <div class="type-tabs">
      <button
        v-for="tab in typeTabs"
        :key="tab.value"
        :class="['type-tab', { active: activeType === tab.value }]"
        @click="handleTypeChange(tab.value)"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- 知识库列表 -->
    <div class="table-card">
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="name" label="名称" min-width="260">
          <template #default="{ row }">
            <span class="kb-name">{{ row.name }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="type" label="类型" width="120" align="center">
          <template #default="{ row }">
            <span :class="['type-tag', typeTagClass(row.type)]">{{ row.typeLabel }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="count" label="条目数" width="100" align="center">
          <template #default="{ row }">
            <span class="count-num">{{ row.count }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <span :class="['status-label', statusClass(row.status)]">{{ statusText(row.status) }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="lastUpdate" label="最后更新" width="120" align="center" />

        <el-table-column prop="updater" label="更新者" width="110" align="center" />

        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button size="small" text type="primary" @click="handleEdit(row)">编辑</el-button>
              <el-button
                size="small"
                text
                :loading="syncingId === row.id"
                @click="handleSync(row)"
              >
                同步
              </el-button>
              <el-button size="small" text type="danger" @click="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-bar">
        <span class="pagination-info">共 {{ total }} 个知识库，显示第 {{ (currentPage - 1) * pageSize + 1 }}-{{ Math.min(currentPage * pageSize, total) }} 个</span>
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

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="480px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="90px">
        <el-form-item label="知识库名称" prop="name">
          <el-input v-model="form.name" placeholder="例如：LM358运算放大器手册" />
        </el-form-item>
        <el-form-item label="知识库类型" prop="type">
          <el-select v-model="form.type" style="width:100%">
            <el-option v-for="t in typeTabs.filter(t => t.value !== 'all')" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.admin-knowledge {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 页面标题 */
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

.header-actions {
  display: flex;
  gap: 8px;
}

/* 搜索栏 */
.search-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.search-input {
  width: 300px;
}

/* 分类标签 */
.type-tabs {
  display: flex;
  gap: 8px;
}

.type-tab {
  padding: 7px 18px;
  border-radius: 20px;
  border: 1px solid #e2e8f0;
  background: #fff;
  color: #64748b;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.type-tab:hover {
  border-color: #3b82f6;
  color: #3b82f6;
}

.type-tab.active {
  background: #1d4ed8;
  border-color: #1d4ed8;
  color: #fff;
}

/* 表格卡片 */
.table-card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

:deep(.el-table) {
  font-size: 14px;
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

.kb-name {
  font-weight: 600;
  color: #1e293b;
}

/* 类型标签 */
.type-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.tag-blue { background: #eff6ff; color: #2563eb; }
.tag-purple { background: #f5f3ff; color: #7c3aed; }
.tag-orange { background: #fff7ed; color: #ea580c; }
.tag-green { background: #f0fdf4; color: #16a34a; }

/* 条目数 */
.count-num {
  font-weight: 600;
  color: #334155;
}

/* 状态 */
.status-label {
  font-size: 13px;
  font-weight: 500;
}

.status-active { color: #16a34a; }
.status-disabled { color: #94a3b8; }

/* 操作按钮 */
.action-btns {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

/* 分页 */
.pagination-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-top: 1px solid #f1f5f9;
}

.pagination-info {
  font-size: 13px;
  color: #64748b;
}
</style>
