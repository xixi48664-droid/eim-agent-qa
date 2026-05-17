import request from './request'

export const recognizeComponentApi = (file) => {
  const formData = new FormData()
  formData.append('imageFile', file)
  return request.post('/recognize', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const submitRecognitionFeedbackApi = ({ sessionId, isCorrect, correction = '' }) => {
  return request.post('/recognize/feedback', {
    sessionId,
    isCorrect,
    correction,
  })
}
