import request from './request'

export const getHistorySessionsApi = () => {
  return request.get('/chat/sessions')
}

export const getHistoryDetailApi = (sessionId) => {
  return request.get(`/chat/sessions/${sessionId}`)
}

export const deleteHistorySessionApi = (sessionId) => {
  return request.delete(`/chat/sessions/${sessionId}`)
}

export const batchDeleteHistorySessionsApi = (sessionIds) => {
  return request.post('/chat/sessions/batch-delete', sessionIds)
}
