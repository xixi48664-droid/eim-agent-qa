import request from './request'

export const askSpecQuestionApi = ({ text, imageUrl = null }) => {
  return request.post('/chat/ask', { text, imageUrl })
}

export const getStandardDetailApi = (standardId) => {
  return request.get(`/standards/${standardId}`)
}
