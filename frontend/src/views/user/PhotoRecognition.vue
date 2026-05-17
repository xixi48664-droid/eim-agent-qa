<script setup>
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { recognizeComponentApi, submitRecognitionFeedbackApi } from '../../api/recognition'

const MAX_FILE_SIZE = 10 * 1024 * 1024
const MAX_CORRECTION_LENGTH = 200
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp']

const fileInputRef = ref(null)
const selectedFile = ref(null)
const previewUrl = ref('')
const recognizing = ref(false)
const feedbackLoading = ref(false)
const result = ref(null)
const feedbackType = ref('')
const correction = ref('')
const feedbackSubmitted = ref(false)
const flowLogs = ref([])

const confidencePercent = computed(() => {
  if (!result.value) return 0
  return Math.round(Number(result.value.confidence || 0) * 100)
})

const confidenceStatus = computed(() => {
  if (confidencePercent.value >= 80) return 'success'
  if (confidencePercent.value >= 50) return 'warning'
  return 'exception'
})

const addFlowLog = (message, type = 'info') => {
  flowLogs.value.unshift({
    id: `${Date.now()}-${Math.random()}`,
    message,
    type,
    time: new Date().toLocaleTimeString(),
  })
}

const triggerChooseFile = () => {
  fileInputRef.value?.click()
}

const validateImageFile = (file) => {
  if (!file) return '请选择图片文件'
  if (!ALLOWED_TYPES.includes(file.type)) {
    return '图片格式不支持，请上传 JPG、PNG、GIF、WEBP 或 BMP 图片'
  }
  if (file.size > MAX_FILE_SIZE) {
    return '图片大小不能超过 10MB'
  }
  return ''
}

const clearPreview = () => {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  selectedFile.value = null
  previewUrl.value = ''
  result.value = null
  feedbackType.value = ''
  correction.value = ''
  feedbackSubmitted.value = false
}

const handleFileChange = (event) => {
  const file = event.target.files?.[0]
  event.target.value = ''
  const error = validateImageFile(file)
  if (error) {
    ElMessage.warning(error)
    addFlowLog(error, 'warning')
    return
  }

  clearPreview()
  selectedFile.value = file
  previewUrl.value = URL.createObjectURL(file)
  addFlowLog(`已选择图片：${file.name}`)
}

const handleDrop = (event) => {
  const file = event.dataTransfer.files?.[0]
  const error = validateImageFile(file)
  if (error) {
    ElMessage.warning(error)
    addFlowLog(error, 'warning')
    return
  }

  clearPreview()
  selectedFile.value = file
  previewUrl.value = URL.createObjectURL(file)
  addFlowLog(`已拖拽上传图片：${file.name}`)
}

const handleRecognize = async () => {
  const error = validateImageFile(selectedFile.value)
  if (error) {
    ElMessage.warning(error)
    addFlowLog(error, 'warning')
    return
  }

  recognizing.value = true
  result.value = null
  feedbackType.value = ''
  correction.value = ''
  feedbackSubmitted.value = false
  addFlowLog('开始上传图片并请求识别服务')

  try {
    const res = await recognizeComponentApi(selectedFile.value)
    result.value = res.data
    addFlowLog('识别完成，已生成识别结果', 'success')

    if (!result.value?.componentId || Number(result.value.confidence || 0) < 0.5) {
      addFlowLog('识别置信度较低，请核对结果并提交反馈', 'warning')
    }
  } catch (err) {
    ElMessage.error(err.message || '识别失败，请稍后重试')
    addFlowLog(err.message || '识别失败，请稍后重试', 'danger')
  } finally {
    recognizing.value = false
  }
}

const handleFeedback = async (isCorrect) => {
  if (!result.value?.sessionId) {
    ElMessage.warning('缺少识别会话，无法提交反馈')
    return
  }

  const correctionText = correction.value.trim()

  if (!isCorrect && !correctionText) {
    ElMessage.warning('请填写正确型号或问题说明')
    return
  }

  if (!isCorrect && correctionText.length > MAX_CORRECTION_LENGTH) {
    ElMessage.warning(`反馈内容不能超过 ${MAX_CORRECTION_LENGTH} 个字符`)
    return
  }

  feedbackLoading.value = true
  try {
    await submitRecognitionFeedbackApi({
      sessionId: result.value.sessionId,
      isCorrect,
      correction: correctionText,
    })
    feedbackSubmitted.value = true
    feedbackType.value = isCorrect ? 'correct' : 'incorrect'
    ElMessage.success('反馈已提交')
    addFlowLog(isCorrect ? '用户确认识别结果正确' : '用户提交识别纠错反馈', 'success')
  } catch (err) {
    ElMessage.error(err.message || '反馈提交失败')
  } finally {
    feedbackLoading.value = false
  }
}
</script>

<template>
  <div class="photo-recognition-page">
    <el-card class="upload-card">
      <div class="upload-area" @dragover.prevent @drop.prevent="handleDrop">
        <input ref="fileInputRef" type="file" class="hidden-input" accept="image/*" @change="handleFileChange" />

        <template v-if="previewUrl">
          <img class="preview-image" :src="previewUrl" alt="元器件图片预览" />
          <div class="file-info">
            <div class="file-name">{{ selectedFile?.name }}</div>
            <div class="file-meta">支持 JPG、PNG、GIF、WEBP、BMP，最大 10MB</div>
          </div>
          <div class="upload-actions">
            <el-button @click="triggerChooseFile">重新选择</el-button>
            <el-button @click="clearPreview">清除图片</el-button>
            <el-button type="primary" :loading="recognizing" @click="handleRecognize">开始识别</el-button>
          </div>
        </template>

        <template v-else>
          <div class="upload-icon">▣</div>
          <h2>上传元器件图片</h2>
          <p>支持 JPG、PNG、WEBP 格式，可拖拽图片到此处或点击按钮选择图片</p>
          <el-button type="primary" @click="triggerChooseFile">选择图片</el-button>
        </template>
      </div>
    </el-card>

    <el-row :gutter="16">
      <el-col :span="15">
        <el-card class="result-card">
          <template #header>
            <div class="card-header">
              <span>识别结果</span>
            </div>
          </template>

          <div v-loading="recognizing" class="result-body">
            <template v-if="result">
              <div class="result-title-row">
                <div>
                  <div class="model-name">{{ result.model || '未知型号' }}</div>
                  <div class="model-subtitle">{{ result.manufacturer || '未知厂商' }}</div>
                </div>
                <el-tag :type="confidenceStatus">置信度 {{ confidencePercent }}%</el-tag>
              </div>

              <el-descriptions :column="2" border>
                <el-descriptions-item label="元器件ID">{{ result.componentId || '未匹配' }}</el-descriptions-item>
                <el-descriptions-item label="类型">{{ result.type || '—' }}</el-descriptions-item>
                <el-descriptions-item label="封装">{{ result.packageType || '—' }}</el-descriptions-item>
                <el-descriptions-item label="厂商">{{ result.manufacturer || '—' }}</el-descriptions-item>
              </el-descriptions>

              <el-alert
                v-if="confidencePercent < 50"
                title="识别置信度较低，请检查图片清晰度，或在下方提交正确型号反馈。"
                type="warning"
                show-icon
                :closable="false"
                class="low-confidence-alert"
              />

              <div class="feedback-panel">
                <div class="feedback-title">识别结果是否正确？</div>
                <div class="feedback-actions">
                  <el-button
                    type="success"
                    plain
                    :loading="feedbackLoading"
                    :disabled="feedbackSubmitted"
                    @click="handleFeedback(true)"
                  >
                    正确
                  </el-button>
                  <el-button
                    type="danger"
                    plain
                    :disabled="feedbackSubmitted"
                    @click="feedbackType = 'incorrect'"
                  >
                    不正确，提交纠错
                  </el-button>
                </div>

                <div v-if="feedbackType === 'incorrect' && !feedbackSubmitted" class="correction-box">
                  <el-input
                    v-model="correction"
                    type="textarea"
                    :rows="3"
                    placeholder="请输入正确型号、器件名称或问题说明"
                    maxlength="200"
                    show-word-limit
                  />
                  <el-button
                    type="primary"
                    :loading="feedbackLoading"
                    class="correction-submit"
                    @click="handleFeedback(false)"
                  >
                    提交反馈
                  </el-button>
                </div>

                <el-alert
                  v-if="feedbackSubmitted"
                  title="反馈已记录，感谢您的纠错与确认。"
                  type="success"
                  show-icon
                  :closable="false"
                />
              </div>
            </template>

            <el-empty v-else description="上传图片后将在这里展示识别结果" />
          </div>
        </el-card>
      </el-col>

      <el-col :span="9">
        <el-card class="log-card">
          <template #header>操作记录</template>
          <el-timeline v-if="flowLogs.length">
            <el-timeline-item
              v-for="item in flowLogs"
              :key="item.id"
              :timestamp="item.time"
              :type="item.type"
            >
              {{ item.message }}
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else description="暂无操作记录" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.photo-recognition-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.upload-card,
.result-card,
.log-card {
  border-radius: 12px;
}

.upload-area {
  min-height: 190px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  border: 2px dashed #cfe0f6;
  border-radius: 14px;
  background: #f8fbff;
  text-align: center;
  padding: 24px;
}

.upload-icon {
  width: 50px;
  height: 50px;
  display: grid;
  place-items: center;
  border-radius: 16px;
  background: #e8f1ff;
  color: #1677ff;
  font-size: 24px;
}

.upload-area h2 {
  margin: 0;
  font-size: 20px;
  color: #0f172a;
}

.upload-area p,
.file-meta,
.hint,
.model-subtitle {
  margin: 0;
  color: #64748b;
  font-size: 13px;
}

.hidden-input {
  display: none;
}

.preview-image {
  max-width: 280px;
  max-height: 150px;
  object-fit: contain;
  border-radius: 10px;
  border: 1px solid #e5edf8;
  background: #fff;
}

.file-name {
  font-weight: 700;
  color: #0f172a;
}

.upload-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: center;
}

.card-header,
.result-title-row,
.feedback-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.result-body {
  min-height: 300px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.model-name {
  font-size: 22px;
  font-weight: 800;
  color: #0f172a;
}

.low-confidence-alert {
  margin-top: 4px;
}

.feedback-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px;
  border-radius: 12px;
  background: #f8fafc;
}

.feedback-title {
  font-weight: 700;
  color: #334155;
}

.correction-box {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.correction-submit {
  align-self: flex-end;
}

.log-card {
  margin-bottom: 16px;
}
</style>
