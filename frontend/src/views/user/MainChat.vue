<script setup>
import { computed, nextTick, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { askQuestionApi, continueConversationApi, submitChatFeedbackApi } from '../../api/chat'

const inputText = ref('')
const loading = ref(false)
const feedbackSubmitting = ref(false)
const sessionId = ref('')
const messageListRef = ref(null)
const feedbackDialogVisible = ref(false)
const feedbackTarget = ref(null)
const feedbackForm = ref({ type: 'like', comment: '' })

const recommendedQuestions = [
  '元器件参数查询',
  '封装类型识别',
  '贴片工艺指导',
  '测试标准查询',
  '故障诊断报告',
]

const messages = ref([
  {
    id: 'welcome-bot',
    role: 'assistant',
    content: '您好！我是电子制造业智能助手，可以帮您解答关于元器件、工艺、测试等方面的问题，也可以查询制造过程中的行业规范和操作流程。',
    time: new Date(),
    sources: [],
    recommendedQuestions: [],
  },
])

const canSend = computed(() => inputText.value.trim().length > 0 && !loading.value)

const formatTime = (value) => {
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const scrollToBottom = async () => {
  await nextTick()
  const el = messageListRef.value
  if (el) el.scrollTop = el.scrollHeight
}

const normalizeSources = (sources) => {
  if (!Array.isArray(sources)) return []
  return sources.filter((item) => item?.sourceTitle || item?.contentSnippet)
}

const appendAssistantMessage = (data) => {
  messages.value.push({
    id: data.messageId || `assistant-${Date.now()}`,
    messageId: data.messageId || '',
    role: 'assistant',
    content: data.answer || '暂未获取到回答内容。',
    time: new Date(),
    intent: data.intent,
    confidence: data.confidence,
    sources: normalizeSources(data.sources),
    recommendedQuestions: data.recommendedQuestions || [],
  })
}

const sendQuestion = async (questionText = inputText.value) => {
  const text = questionText.trim()
  if (!text) {
    ElMessage.warning('请输入问题')
    return
  }

  messages.value.push({
    id: `user-${Date.now()}`,
    role: 'user',
    content: text,
    time: new Date(),
  })
  inputText.value = ''
  loading.value = true
  await scrollToBottom()

  try {
    const res = sessionId.value
      ? await continueConversationApi(sessionId.value, { text })
      : await askQuestionApi({ text })

    const data = res.data || {}
    if (data.sessionId) sessionId.value = data.sessionId
    appendAssistantMessage(data)
  } catch (error) {
    messages.value.push({
      id: `assistant-error-${Date.now()}`,
      role: 'assistant',
      content: error.message || '问答服务暂时不可用，请稍后重试。',
      time: new Date(),
      isError: true,
      sources: [],
      recommendedQuestions: [],
    })
    ElMessage.error(error.message || '发送失败')
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

const handleQuickQuestion = (label) => {
  const questionMap = {
    元器件参数查询: '请帮我查询常用元器件的关键参数。',
    封装类型识别: '请介绍常见元器件封装类型及识别方法。',
    贴片工艺指导: '请说明贴片工艺中的关键操作要点。',
    测试标准查询: '请查询电子制造测试相关标准和注意事项。',
    故障诊断报告: '请说明电子制造常见故障的诊断思路。',
  }
  sendQuestion(questionMap[label] || label)
}

const openFeedbackDialog = (message, feedback) => {
  feedbackTarget.value = message
  feedbackForm.value = { type: feedback, comment: '' }
  feedbackDialogVisible.value = true
}

const confirmFeedback = async () => {
  const message = feedbackTarget.value
  const feedback = feedbackForm.value.type
  const comment = feedbackForm.value.comment.trim()

  if (comment.length > 200) {
    ElMessage.warning('反馈说明不能超过 200 个字符')
    return
  }

  if (!message) return

  if (!message.messageId) {
    message.feedback = feedback
    message.feedbackComment = comment
    feedbackDialogVisible.value = false
    ElMessage.success('反馈已记录')
    return
  }

  feedbackSubmitting.value = true
  try {
    await submitChatFeedbackApi({ messageId: message.messageId, feedback })
    message.feedback = feedback
    message.feedbackComment = comment
    feedbackDialogVisible.value = false
    ElMessage.success('反馈已提交')
  } catch (error) {
    ElMessage.error(error.message || '反馈提交失败')
  } finally {
    feedbackSubmitting.value = false
  }
}

const exportConversation = () => {
  const lines = messages.value.map((item) => {
    const role = item.role === 'user' ? '用户' : '助手'
    return `[${formatTime(item.time)}] ${role}:\n${item.content}`
  })
  const blob = new Blob([lines.join('\n\n')], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `主问答记录_${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.txt`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="main-chat-page">
    <el-card class="chat-card">
      <div class="quick-area">
        <span class="quick-label">快捷指令</span>
        <el-button
          v-for="item in recommendedQuestions"
          :key="item"
          round
          size="small"
          class="quick-btn"
          @click="handleQuickQuestion(item)"
        >
          {{ item }}
        </el-button>
      </div>

      <div ref="messageListRef" class="message-list">
        <div v-for="message in messages" :key="message.id" class="message-row" :class="message.role">
          <div class="avatar" :class="message.role">
            {{ message.role === 'user' ? '我' : 'AI' }}
          </div>

          <div class="message-content-wrap">
            <div class="message-bubble" :class="{ error: message.isError }">
              <div class="message-text">{{ message.content }}</div>

              <div v-if="message.sources?.length" class="source-list">
                <div class="source-title">参考来源</div>
                <div v-for="source in message.sources" :key="source.sourceId || source.sourceTitle" class="source-item">
                  <div class="source-name">{{ source.sourceTitle || '来源信息' }}</div>
                  <div class="source-snippet">{{ source.contentSnippet }}</div>
                </div>
              </div>

              <div v-if="message.recommendedQuestions?.length" class="recommend-list">
                <el-button
                  v-for="question in message.recommendedQuestions"
                  :key="question"
                  size="small"
                  round
                  @click="sendQuestion(question)"
                >
                  {{ question }}
                </el-button>
              </div>

              <div v-if="message.role === 'assistant' && message.id !== 'welcome-bot'" class="message-tools">
                <el-button
                  text
                  size="small"
                  :disabled="feedbackSubmitting"
                  @click="openFeedbackDialog(message, 'like')"
                >
                  {{ message.feedback === 'like' ? '已赞' : '赞' }}
                </el-button>
                <el-button
                  text
                  size="small"
                  :disabled="feedbackSubmitting"
                  @click="openFeedbackDialog(message, 'dislike')"
                >
                  {{ message.feedback === 'dislike' ? '已踩' : '踩' }}
                </el-button>
              </div>
            </div>
            <div class="message-time">{{ formatTime(message.time) }}</div>
          </div>
        </div>

        <div v-if="loading" class="message-row assistant">
          <div class="avatar assistant">AI</div>
          <div class="message-content-wrap">
            <div class="message-bubble loading-bubble">
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="dot"></span>
            </div>
          </div>
        </div>
      </div>

      <el-dialog v-model="feedbackDialogVisible" title="回答反馈" width="420px">
        <el-form label-position="top">
          <el-form-item label="反馈类型">
            <el-radio-group v-model="feedbackForm.type">
              <el-radio-button label="like">有帮助</el-radio-button>
              <el-radio-button label="dislike">需改进</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="补充说明">
            <el-input
              v-model="feedbackForm.comment"
              type="textarea"
              :rows="4"
              maxlength="200"
              show-word-limit
              placeholder="可补充说明这条回答哪里有帮助，或需要改进的地方"
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="feedbackDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="feedbackSubmitting" @click="confirmFeedback">
            提交反馈
          </el-button>
        </template>
      </el-dialog>

      <div class="input-area">
        <div class="input-avatar"></div>
        <el-input
          v-model="inputText"
          class="question-input"
          placeholder="输入您的问题，如上传图片进行识别..."
          clearable
          @keyup.enter="sendQuestion()"
        />
        <el-button type="primary" round :disabled="!canSend" :loading="loading" @click="sendQuestion()">
          发送
        </el-button>
        <el-button round @click="exportConversation">导出</el-button>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.main-chat-page {
  height: calc(100vh - 112px);
  min-height: 620px;
}

.chat-card {
  height: 100%;
  border-radius: 12px;
}

.chat-card :deep(.el-card__body) {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 0;
}

.quick-area {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 58px;
  padding: 0 24px;
  border-bottom: 1px solid #edf1f7;
  flex-wrap: wrap;
}

.quick-label {
  color: #475569;
  font-size: 13px;
  font-weight: 700;
}

.quick-btn {
  color: #1677ff;
  background: #eef7ff;
  border-color: #d6ebff;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 32px 28px 20px;
  background: #fff;
}

.message-row {
  display: flex;
  gap: 12px;
  margin-bottom: 28px;
}

.message-row.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  border-radius: 50%;
  color: #fff;
  font-size: 11px;
  font-weight: 800;
}

.avatar.assistant {
  background: #1684e8;
}

.avatar.user {
  background: #21a558;
}

.message-content-wrap {
  max-width: min(560px, 72%);
}

.message-row.user .message-content-wrap {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.message-bubble {
  padding: 14px 16px;
  border-radius: 14px;
  color: #0f172a;
  background: #fff;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
  border: 1px solid #edf1f7;
}

.message-row.user .message-bubble {
  color: #fff;
  background: #1684e8;
  border-color: #1684e8;
  box-shadow: 0 8px 22px rgba(22, 132, 232, 0.22);
}

.message-bubble.error {
  border-color: #fecaca;
  background: #fff7f7;
  color: #b91c1c;
}

.message-text {
  line-height: 1.75;
  white-space: pre-wrap;
}

.message-time {
  margin-top: 6px;
  color: #94a3b8;
  font-size: 12px;
}

.message-row.user .message-time {
  text-align: right;
}

.source-list {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid #edf1f7;
}

.source-title {
  margin-bottom: 8px;
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
}

.source-item {
  padding: 8px;
  border-radius: 8px;
  background: #f8fafc;
  margin-bottom: 6px;
}

.source-name {
  color: #0f172a;
  font-size: 13px;
  font-weight: 700;
}

.source-snippet {
  color: #64748b;
  font-size: 12px;
  line-height: 1.6;
}

.recommend-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.message-tools {
  display: flex;
  gap: 4px;
  margin-top: 10px;
}

.loading-bubble {
  display: flex;
  gap: 6px;
  align-items: center;
  min-width: 58px;
}

.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #94a3b8;
  animation: blink 1.2s infinite ease-in-out;
}

.dot:nth-child(2) {
  animation-delay: 0.2s;
}

.dot:nth-child(3) {
  animation-delay: 0.4s;
}

.input-area {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #edf1f7;
  background: #fff;
}

.input-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  flex: 0 0 auto;
  background: #e6f4ff;
}

.question-input {
  flex: 1;
}

.question-input :deep(.el-input__wrapper) {
  border-radius: 999px;
  background: #f8fafc;
  box-shadow: 0 0 0 1px #edf1f7 inset;
}

@keyframes blink {
  0%,
  80%,
  100% {
    opacity: 0.35;
    transform: translateY(0);
  }

  40% {
    opacity: 1;
    transform: translateY(-3px);
  }
}

@media (max-width: 860px) {
  .message-content-wrap {
    max-width: 82%;
  }

  .input-area,
  .quick-area {
    padding-left: 14px;
    padding-right: 14px;
  }
}
</style>
