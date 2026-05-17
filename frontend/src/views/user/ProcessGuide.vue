<script setup>
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getTutorialByProcessApi, getTutorialDetailApi } from '../../api/tutorial'

const loading = ref(false)
const detailLoading = ref(false)
const processName = ref('')
const tutorial = ref(null)
const activeStep = ref(0)

const processOptions = [
  '贴片生产工序',
  '焊接工序',
  '装配工序',
  '检测工序',
  '返修工序',
]

const steps = computed(() => tutorial.value?.steps || [])
const currentStep = computed(() => steps.value[activeStep.value] || null)
const canPrevious = computed(() => activeStep.value > 0)
const canNext = computed(() => activeStep.value < steps.value.length - 1)

const searchTutorial = async () => {
  const keyword = processName.value.trim()
  if (!keyword) {
    ElMessage.warning('请选择或输入工序名称')
    return
  }

  loading.value = true
  tutorial.value = null
  activeStep.value = 0

  try {
    const res = await getTutorialByProcessApi(keyword)
    tutorial.value = res.data
    activeStep.value = 0

    if (!steps.value.length) {
      ElMessage.warning('已找到工序，但暂无步骤信息')
    }
  } catch (error) {
    ElMessage.error(error.message || '未查询到相关工序指导')
  } finally {
    loading.value = false
  }
}

const refreshDetail = async () => {
  if (!tutorial.value?.tutorialId) return

  detailLoading.value = true
  try {
    const res = await getTutorialDetailApi(tutorial.value.tutorialId)
    tutorial.value = res.data
    if (activeStep.value >= steps.value.length) activeStep.value = 0
  } catch (error) {
    ElMessage.error(error.message || '获取工序详情失败')
  } finally {
    detailLoading.value = false
  }
}

const handlePrevious = () => {
  if (canPrevious.value) activeStep.value -= 1
}

const handleNext = () => {
  if (canNext.value) activeStep.value += 1
}

const choosePreset = (name) => {
  processName.value = name
  searchTutorial()
}
</script>

<template>
  <div class="process-guide-page">
    <el-card class="search-card">
      <div class="search-row">
        <div class="search-left">
          <div class="section-title">流程指导</div>
          <div class="section-desc">选择或输入生产工序，查看对应操作步骤与注意事项。</div>
        </div>
        <div class="search-controls">
          <el-select
            v-model="processName"
            filterable
            allow-create
            clearable
            default-first-option
            placeholder="请选择生产工序"
            class="process-select"
            @keyup.enter="searchTutorial"
          >
            <el-option v-for="item in processOptions" :key="item" :label="item" :value="item" />
          </el-select>
          <el-button type="primary" :loading="loading" @click="searchTutorial">查询指导</el-button>
        </div>
      </div>
    </el-card>

    <el-card class="quick-card">
      <template #header>常用工序</template>
      <div class="quick-list">
        <el-button v-for="item in processOptions" :key="item" plain @click="choosePreset(item)">
          {{ item }}
        </el-button>
      </div>
    </el-card>

    <el-card class="guide-card">
      <template #header>
        <div class="guide-header">
          <span>{{ tutorial?.processName || '工序步骤' }}</span>
          <div class="guide-meta" v-if="tutorial">
            <el-tag type="primary">共 {{ tutorial.totalSteps || steps.length }} 步</el-tag>
            <el-tag v-if="tutorial.estimatedTime" type="success">预计 {{ tutorial.estimatedTime }}</el-tag>
            <el-button text type="primary" :loading="detailLoading" @click="refreshDetail">刷新详情</el-button>
          </div>
        </div>
      </template>

      <div v-loading="loading || detailLoading" class="guide-body">
        <template v-if="tutorial && steps.length">
          <div class="step-visual">
            <el-steps :active="activeStep" finish-status="success" align-center>
              <el-step
                v-for="step in steps"
                :key="step.stepId"
                :title="`步骤 ${step.stepNo}`"
                :description="step.stepTitle || '操作步骤'"
              />
            </el-steps>
          </div>

          <div class="step-detail">
            <div class="step-image-wrap">
              <el-image
                v-if="currentStep?.imageUrl"
                class="step-image"
                :src="currentStep.imageUrl"
                fit="contain"
                :preview-src-list="[currentStep.imageUrl]"
              />
              <div v-else class="image-placeholder">
                <span class="placeholder-icon">▧</span>
                <span>暂无步骤图片</span>
              </div>
            </div>

            <div class="step-content-card">
              <div class="step-title-row">
                <el-tag>步骤 {{ currentStep.stepNo }}</el-tag>
                <h3>{{ currentStep.stepTitle || '操作步骤' }}</h3>
              </div>
              <p class="step-content">{{ currentStep.stepContent }}</p>

              <el-alert
                v-if="currentStep.note"
                :title="currentStep.note"
                type="warning"
                show-icon
                :closable="false"
                class="step-alert"
              />

              <el-collapse v-if="currentStep.faq" class="faq-collapse">
                <el-collapse-item title="常见问题" name="faq">
                  <div class="faq-content">{{ currentStep.faq }}</div>
                </el-collapse-item>
              </el-collapse>
            </div>
          </div>
        </template>

        <template v-else-if="tutorial && !steps.length">
          <el-empty description="该工序暂无步骤信息" />
        </template>

        <template v-else>
          <div class="empty-guide">
            <div class="empty-image-icon">▧</div>
            <div class="empty-text">请选择生产工序后查看步骤图片与操作说明</div>
            <div class="empty-subtext">可从上方下拉框选择工序，或点击常用工序快速查询。</div>
          </div>
        </template>
      </div>
    </el-card>

    <el-card class="nav-card">
      <div class="step-nav">
        <el-button :disabled="!tutorial || !canPrevious" @click="handlePrevious">上一步</el-button>
        <span class="step-status">
          <template v-if="tutorial && steps.length">第 {{ activeStep + 1 }} / {{ steps.length }} 步</template>
          <template v-else>请选择工序</template>
        </span>
        <el-button type="primary" :disabled="!tutorial || !canNext" @click="handleNext">下一步</el-button>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.process-guide-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.search-card,
.quick-card,
.guide-card,
.nav-card {
  border-radius: 12px;
}

.search-row,
.guide-header,
.step-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.section-title {
  font-size: 18px;
  font-weight: 800;
  color: #0f172a;
}

.section-desc {
  margin-top: 6px;
  color: #64748b;
  font-size: 13px;
}

.search-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.process-select {
  width: 360px;
}

.quick-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.guide-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.guide-body {
  min-height: 430px;
}

.step-visual {
  padding: 10px 0 24px;
}

.step-detail {
  display: grid;
  grid-template-columns: minmax(320px, 1fr) 1fr;
  gap: 18px;
  align-items: stretch;
}

.step-image-wrap {
  min-height: 260px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  border: 1px solid #e5edf8;
  background: #f8fafc;
  overflow: hidden;
}

.step-image {
  width: 100%;
  height: 300px;
}

.image-placeholder,
.empty-guide {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #94a3b8;
  text-align: center;
}

.placeholder-icon,
.empty-image-icon {
  font-size: 34px;
  color: #94a3b8;
}

.step-content-card {
  padding: 20px;
  border-radius: 12px;
  background: #f8fbff;
  border: 1px solid #e5edf8;
}

.step-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.step-title-row h3 {
  margin: 0;
  color: #0f172a;
  font-size: 20px;
}

.step-content {
  margin: 0;
  color: #334155;
  line-height: 1.9;
  white-space: pre-wrap;
}

.step-alert,
.faq-collapse {
  margin-top: 16px;
}

.faq-content {
  color: #475569;
  line-height: 1.8;
  white-space: pre-wrap;
}

.empty-guide {
  min-height: 390px;
}

.empty-text {
  color: #64748b;
  font-size: 16px;
  font-weight: 700;
}

.empty-subtext {
  color: #94a3b8;
  font-size: 13px;
}

.step-status {
  color: #64748b;
}

@media (max-width: 960px) {
  .search-row,
  .guide-header,
  .step-nav {
    align-items: stretch;
    flex-direction: column;
  }

  .search-controls,
  .process-select {
    width: 100%;
  }

  .step-detail {
    grid-template-columns: 1fr;
  }
}
</style>
