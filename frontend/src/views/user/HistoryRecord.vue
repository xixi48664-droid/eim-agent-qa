<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  batchDeleteHistorySessionsApi,
  deleteHistorySessionApi,
  getHistoryDetailApi,
  getHistorySessionsApi,
} from '../../api/history'

const loading = ref(false)
const detailLoading = ref(false)
const deleting = ref(false)
const sessions = ref([])
const selectedIds = ref([])
const restoredSession = ref(null)
const currentPage = ref(1)
const pageSize = ref(10)

const selectedSet = computed(() => new Set(selectedIds.value))
const total = computed(() => sessions.value.length)
const pageSessions = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return sessions.value.slice(start, start + pageSize.value)
})
const currentPageIds = computed(() => pageSessions.value.map((item) => item.sessionId))
const allCurrentSelected = computed(() => {
  return currentPageIds.value.length > 0 && currentPageIds.value.every((id) => selectedSet.value.has(id))
})
const partiallySelected = computed(() => {
  return currentPageIds.value.some((id) => selectedSet.value.has(id)) && !allCurrentSelected.value
})

const formatDateTime = (value) => {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString()
}

const getSessionSummary = (session) => {
  if (session.latestMessage) return session.latestMessage
  const count = session.messageCount || 0
  return count ? `共 ${count} 条消息` : '暂无消息摘要'
}

const getAvatarText = (title) => {
  const text = title || '历史'
  return text.slice(0, 1)
}

const loadSessions = async () => {
  loading.value = true
  try {
    const res = await getHistorySessionsApi()
    sessions.value = Array.isArray(res.data) ? res.data : []
    selectedIds.value = selectedIds.value.filter((id) => sessions.value.some((item) => item.sessionId === id))
    if ((currentPage.value - 1) * pageSize.value >= sessions.value.length) {
      currentPage.value = Math.max(1, Math.ceil(sessions.value.length / pageSize.value))
    }
  } catch (error) {
    ElMessage.error(error.message || '获取历史记录失败')
  } finally {
    loading.value = false
  }
}

const toggleSession = (sessionId, checked) => {
  if (checked) {
    if (!selectedSet.value.has(sessionId)) selectedIds.value.push(sessionId)
    return
  }
  selectedIds.value = selectedIds.value.filter((id) => id !== sessionId)
}

const toggleCurrentPage = (checked) => {
  if (checked) {
    const merged = new Set(selectedIds.value)
    currentPageIds.value.forEach((id) => merged.add(id))
    selectedIds.value = [...merged]
    return
  }
  const pageIdSet = new Set(currentPageIds.value)
  selectedIds.value = selectedIds.value.filter((id) => !pageIdSet.has(id))
}

const restoreSession = async (session) => {
  detailLoading.value = true
  try {
    const res = await getHistoryDetailApi(session.sessionId)
    restoredSession.value = res.data
    ElMessage.success('历史对话已恢复')
  } catch (error) {
    ElMessage.error(error.message || '恢复历史对话失败')
  } finally {
    detailLoading.value = false
  }
}

const deleteSession = async (session) => {
  try {
    await ElMessageBox.confirm(`确认删除「${session.title || '未命名会话'}」吗？`, '删除历史记录', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }

  deleting.value = true
  try {
    await deleteHistorySessionApi(session.sessionId)
    ElMessage.success('删除成功')
    selectedIds.value = selectedIds.value.filter((id) => id !== session.sessionId)
    if (restoredSession.value?.sessionId === session.sessionId) restoredSession.value = null
    await loadSessions()
  } catch (error) {
    ElMessage.error(error.message || '删除失败')
  } finally {
    deleting.value = false
  }
}

const batchDelete = async () => {
  if (!selectedIds.value.length) {
    ElMessage.warning('请先选择要删除的历史记录')
    return
  }

  try {
    await ElMessageBox.confirm(`确认删除已选中的 ${selectedIds.value.length} 条历史记录吗？`, '批量删除', {
      confirmButtonText: '批量删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }

  deleting.value = true
  try {
    const ids = [...selectedIds.value]
    const res = await batchDeleteHistorySessionsApi(ids)
    const successCount = res.data?.successCount
    ElMessage.success(successCount === undefined ? '批量删除成功' : `成功删除 ${successCount} 条历史记录`)
    if (ids.includes(restoredSession.value?.sessionId)) restoredSession.value = null
    selectedIds.value = []
    await loadSessions()
  } catch (error) {
    ElMessage.error(error.message || '批量删除失败')
  } finally {
    deleting.value = false
  }
}

const clearSelection = () => {
  selectedIds.value = []
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
}

onMounted(loadSessions)
</script>

<template>
  <div class="history-page">
    <el-card class="toolbar-card">
      <div class="toolbar">
        <div class="toolbar-left">
          <el-checkbox
            :model-value="allCurrentSelected"
            :indeterminate="partiallySelected"
            @change="toggleCurrentPage"
          >
            全选本页
          </el-checkbox>
          <el-button type="danger" plain :disabled="!selectedIds.length" :loading="deleting" @click="batchDelete">
            批量删除
          </el-button>
          <el-button :disabled="!selectedIds.length" @click="clearSelection">清空选择</el-button>
        </div>
        <div class="toolbar-right">
          <span class="selected-tip">已选择 {{ selectedIds.length }} 条</span>
          <el-button type="primary" plain :loading="loading" @click="loadSessions">刷新</el-button>
        </div>
      </div>
    </el-card>

    <el-row :gutter="16" class="history-content">
      <el-col :span="15">
        <el-card class="list-card">
          <template #header>
            <div class="card-header">
              <span>历史记录</span>
              <span class="meta">按时间排序，共 {{ total }} 条</span>
            </div>
          </template>

          <div v-loading="loading" class="history-list">
            <template v-if="pageSessions.length">
              <div
                v-for="session in pageSessions"
                :key="session.sessionId"
                class="history-item"
                :class="{ active: restoredSession?.sessionId === session.sessionId }"
              >
                <el-checkbox
                  :model-value="selectedSet.has(session.sessionId)"
                  @change="(checked) => toggleSession(session.sessionId, checked)"
                />

                <div class="history-avatar">{{ getAvatarText(session.title) }}</div>

                <div class="history-main" @click="restoreSession(session)">
                  <div class="history-title">{{ session.title || '未命名会话' }}</div>
                  <div class="history-summary">{{ getSessionSummary(session) }}</div>
                  <div class="history-time">{{ formatDateTime(session.updateTime || session.createTime) }}</div>
                </div>

                <div class="history-actions">
                  <el-button size="small" plain :loading="detailLoading" @click="restoreSession(session)">
                    恢复
                  </el-button>
                  <el-button size="small" text type="danger" :loading="deleting" @click="deleteSession(session)">
                    删除
                  </el-button>
                </div>
              </div>
            </template>
            <el-empty v-else description="暂无历史记录" />
          </div>

          <div class="pagination-wrap">
            <el-pagination
              v-model:current-page="currentPage"
              :page-size="pageSize"
              :page-sizes="[5, 10, 20, 50]"
              :total="total"
              background
              layout="prev, pager, next, sizes"
              @size-change="handleSizeChange"
            />
          </div>
        </el-card>
      </el-col>

      <el-col :span="9">
        <el-card class="detail-card">
          <template #header>
            <div class="card-header">
              <span>对话内容</span>
              <span v-if="restoredSession" class="meta">{{ restoredSession.title || '未命名会话' }}</span>
            </div>
          </template>

          <div v-loading="detailLoading" class="message-panel">
            <template v-if="restoredSession?.messages?.length">
              <div
                v-for="message in restoredSession.messages"
                :key="message.messageId"
                class="message-item"
                :class="message.senderType === 'user' ? 'user-message' : 'bot-message'"
              >
                <div class="message-role">{{ message.senderType === 'user' ? '我' : '助手' }}</div>
                <div class="message-bubble">
                  <div>{{ message.content || '—' }}</div>
                  <el-image
                    v-if="message.imageUrl"
                    class="message-image"
                    :src="message.imageUrl"
                    fit="contain"
                    :preview-src-list="[message.imageUrl]"
                  />
                  <div class="message-time">{{ formatDateTime(message.createTime) }}</div>
                </div>
              </div>
            </template>
            <el-empty v-else description="点击左侧恢复历史对话" />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.history-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.toolbar-card,
.list-card,
.detail-card {
  border-radius: 12px;
}

.toolbar,
.toolbar-left,
.toolbar-right,
.card-header,
.history-item,
.history-actions {
  display: flex;
  align-items: center;
}

.toolbar,
.card-header {
  justify-content: space-between;
  gap: 12px;
}

.toolbar-left,
.toolbar-right,
.history-actions {
  gap: 10px;
}

.selected-tip,
.meta,
.history-summary,
.history-time,
.message-time {
  color: #64748b;
  font-size: 13px;
}

.history-content {
  align-items: stretch;
}

.history-list {
  min-height: 470px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.history-item {
  gap: 12px;
  padding: 14px;
  border: 1px solid #e5edf8;
  border-radius: 12px;
  background: #fff;
  transition: all 0.18s ease;
}

.history-item:hover,
.history-item.active {
  border-color: #91caff;
  background: #eaf6ff;
}

.history-avatar {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  border-radius: 10px;
  background: #eef6ff;
  color: #1677ff;
  font-weight: 800;
}

.history-main {
  min-width: 0;
  flex: 1;
  cursor: pointer;
}

.history-title {
  margin-bottom: 4px;
  color: #0f172a;
  font-weight: 700;
}

.history-summary {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.history-time {
  margin-top: 4px;
}

.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

.detail-card,
.message-panel {
  height: 100%;
}

.message-panel {
  min-height: 540px;
  max-height: 660px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-right: 4px;
}

.message-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.user-message {
  align-items: flex-end;
}

.bot-message {
  align-items: flex-start;
}

.message-role {
  color: #94a3b8;
  font-size: 12px;
}

.message-bubble {
  max-width: 88%;
  padding: 12px;
  border-radius: 12px;
  color: #334155;
  line-height: 1.7;
  white-space: pre-wrap;
  background: #f1f5f9;
}

.user-message .message-bubble {
  color: #fff;
  background: #1677ff;
}

.user-message .message-time {
  color: rgba(255, 255, 255, 0.75);
}

.message-image {
  width: 180px;
  height: 120px;
  margin-top: 8px;
  border-radius: 8px;
  background: #fff;
}

.message-time {
  margin-top: 6px;
  font-size: 12px;
}

@media (max-width: 1100px) {
  .history-content :deep(.el-col) {
    max-width: 100%;
    flex: 0 0 100%;
  }
}
</style>
