<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { askSpecQuestionApi, getStandardDetailApi } from '../../api/spec'

const asking = ref(false)
const loadingDetail = ref(false)
const result = ref(null)
const detailVisible = ref(false)
const standardDetail = ref(null)
const queryForm = reactive({
  question: '',
  category: '',
})

const categoryOptions = [
  { value: '', label: '全部类别' },
  { value: '国家标准', label: '国家标准' },
  { value: '行业标准', label: '行业标准' },
  { value: '企业标准', label: '企业标准' },
]

const hotQuestions = [
  'RoHS 指令的具体要求是什么？',
  'IPC-A-610 验收标准主要内容',
  '电子元器件的存储要求',
  'PCB 板材的阻燃等级标准',
  '静电防护的标准规范',
  '电子产品可靠性测试标准',
]

const normalizeSources = (sources = []) => {
  return (sources || []).map((item) => ({
    sourceId: item.sourceId || '',
    sourceTitle: item.sourceTitle || '规范条目',
    contentSnippet: item.contentSnippet || '',
  }))
}

const handleAsk = async (questionText = queryForm.question) => {
  const text = (questionText || '').trim()
  if (!text) {
    ElMessage.warning('请输入规范问答问题')
    return
  }

  asking.value = true
  result.value = null

  try {
    const res = await askSpecQuestionApi({ text })
    const data = res.data || {}

    result.value = {
      sessionId: data.sessionId,
      answer: data.answer || '暂无回答内容',
      intent: data.intent || '未知',
      confidence: Number(data.confidence || 0),
      sources: normalizeSources(data.sources),
      recommendedQuestions: data.recommendedQuestions || [],
    }

  } catch (error) {
    const msg = error.message || '规范问答失败，请稍后重试'
    ElMessage.error(msg)
  } finally {
    asking.value = false
  }
}

const useHotQuestion = (question) => {
  queryForm.question = question
  handleAsk(question)
}

const openStandardDetail = async (sourceId) => {
  if (!sourceId) {
    ElMessage.warning('当前引用未提供规范ID，无法查看详情')
    return
  }

  loadingDetail.value = true
  detailVisible.value = true
  standardDetail.value = null
  try {
    const res = await getStandardDetailApi(sourceId)
    standardDetail.value = res.data || null
  } catch (error) {
    ElMessage.error(error.message || '获取规范详情失败')
    detailVisible.value = false
  } finally {
    loadingDetail.value = false
  }
}
</script>

<template>
  <div class="spec-qa-page">
    <el-card class="query-card">
      <template #header>
        <div class="section-title">规范问答</div>
      </template>

      <div class="query-form-row">
        <div class="category-search-wrap">
          <span class="category-label">按类别搜索</span>
          <el-select v-model="queryForm.category" class="category-select" placeholder="全部类别">
            <el-option
              v-for="item in categoryOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </div>
        <el-input
          v-model="queryForm.question"
          class="question-input"
          placeholder="请输入规范编号、条款名称或关键问题..."
          clearable
          @keyup.enter="handleAsk()"
        />
        <el-button class="search-button" type="primary" :loading="asking" @click="handleAsk()">搜索</el-button>
      </div>
    </el-card>

    <el-row :gutter="16">
      <el-col :span="24">
        <el-card class="answer-card">
          <template #header>
            <div class="section-title">问答结果</div>
          </template>

          <div v-loading="asking" class="answer-content">
            <template v-if="result">
              <el-alert
                title="已完成问答"
                :description="`意图：${result.intent}，置信度：${Math.round(result.confidence * 100)}%`"
                type="success"
                :closable="false"
                show-icon
              />

              <div class="answer-text">{{ result.answer }}</div>

              <div class="source-block">
                <div class="sub-title">引用来源</div>
                <el-empty v-if="!result.sources.length" description="未返回引用来源" />
                <div v-else class="source-list">
                  <el-card v-for="source in result.sources" :key="source.sourceId || source.sourceTitle" class="source-item">
                    <div class="source-top">
                      <div class="source-title">{{ source.sourceTitle }}</div>
                      <el-button
                        type="primary"
                        plain
                        size="small"
                        :disabled="!source.sourceId"
                        @click="openStandardDetail(source.sourceId)"
                      >
                        查看详情
                      </el-button>
                    </div>
                    <div class="source-snippet">{{ source.contentSnippet || '暂无摘要' }}</div>
                  </el-card>
                </div>
              </div>

              <div class="source-block">
                <div class="sub-title">推荐问题</div>
                <el-empty v-if="!result.recommendedQuestions.length" description="暂无推荐问题" />
                <div v-else class="recommend-list">
                  <el-tag
                    v-for="item in result.recommendedQuestions"
                    :key="item"
                    class="recommend-item"
                    @click="useHotQuestion(item)"
                  >
                    {{ item }}
                  </el-tag>
                </div>
              </div>
            </template>

            <el-empty v-else description="输入问题后可查看规范问答结果" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="hot-card">
      <template #header>
        <div class="section-title">常见规范问题</div>
      </template>
      <div class="hot-list">
        <el-button
          v-for="item in hotQuestions"
          :key="item"
          class="hot-item"
          text
          @click="useHotQuestion(item)"
        >
          {{ item }}
        </el-button>
      </div>
    </el-card>

    <el-row :gutter="16">
      <el-col :span="24">
      </el-col>
    </el-row>

    <el-dialog v-model="detailVisible" title="规范详情" width="760px">
      <div v-loading="loadingDetail" class="detail-wrap">
        <template v-if="standardDetail">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="编号">{{ standardDetail.standardCode || '—' }}</el-descriptions-item>
            <el-descriptions-item label="名称">{{ standardDetail.standardName || '—' }}</el-descriptions-item>
            <el-descriptions-item label="章节">{{ standardDetail.section || '—' }}</el-descriptions-item>
            <el-descriptions-item label="相关工序">{{ standardDetail.relatedProcess || '—' }}</el-descriptions-item>
            <el-descriptions-item label="标签" :span="2">{{ standardDetail.tags || '—' }}</el-descriptions-item>
            <el-descriptions-item label="摘要" :span="2">{{ standardDetail.summary || '—' }}</el-descriptions-item>
          </el-descriptions>
        </template>
        <el-empty v-else description="暂无规范详情" />
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.spec-qa-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.query-card {
  border-radius: 12px;
  border: 1px solid rgba(22, 119, 255, 0.18);
  box-shadow: 0 8px 24px rgba(22, 119, 255, 0.08);
}

.query-form-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.category-search-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 0 0 auto;
}

.category-label {
  color: #1677ff;
  font-weight: 700;
  white-space: nowrap;
}

.category-select {
  width: 150px;
}

.question-input {
  flex: 1;
}

.question-input :deep(.el-input__wrapper),
.category-select :deep(.el-select__wrapper) {
  min-height: 44px;
  border-radius: 8px;
  box-shadow: 0 0 0 1px rgba(22, 119, 255, 0.18) inset;
}

.search-button {
  min-width: 84px;
  height: 44px;
  box-shadow: 0 8px 18px rgba(22, 119, 255, 0.22);
}

.section-title {
  font-weight: 700;
  color: #0f172a;
}

.answer-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 520px;
}

.answer-text {
  line-height: 1.9;
  color: #1f2937;
  white-space: pre-wrap;
  border: 1px solid #e5edf8;
  border-radius: 12px;
  padding: 14px;
  background: #fafcff;
}

.sub-title {
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 10px;
  color: #334155;
}

.source-list {
  display: grid;
  gap: 10px;
}

.source-item {
  border-radius: 10px;
  border: 1px solid rgba(22, 119, 255, 0.16);
  box-shadow: 0 6px 18px rgba(22, 119, 255, 0.06);
}

.source-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.source-title {
  font-weight: 700;
  color: #0f172a;
}

.source-snippet {
  margin-top: 8px;
  color: #64748b;
  line-height: 1.7;
}

.recommend-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.recommend-item {
  cursor: pointer;
}

.hot-card {
  position: sticky;
  bottom: 16px;
  z-index: 5;
  border-radius: 12px;
  box-shadow: 0 -4px 22px rgba(15, 23, 42, 0.08);
}

.hot-list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.hot-item {
  justify-content: flex-start;
  min-height: 42px;
  padding: 10px 12px;
  white-space: normal;
  text-align: left;
  line-height: 1.6;
  background: #f8fafc;
  border-radius: 8px;
}

.detail-wrap {
  min-height: 180px;
}
</style>
