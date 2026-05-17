import request from './request'

export const askQuestionApi = ({ text, imageUrl = null }) => {
  return request.post('/chat/ask', { text, imageUrl })
}

export const continueConversationApi = (sessionId, { text, imageUrl = null }) => {
  return request.post(`/chat/sessions/${sessionId}/continue`, { text, imageUrl })
}

export const submitChatFeedbackApi = ({ messageId, feedback }) => {
  return request.post('/chat/feedback', { messageId, feedback })
}
