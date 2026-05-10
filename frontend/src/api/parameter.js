import request from './request'

export const searchComponentsApi = async ({ keyword, pageNum = 1, pageSize = 10, category = '' }) => {
  const params = { keyword, pageNum, pageSize }
  if (category) params.type = category
  const result = await request.get('/components/search', { params })
  return result
}

export const getComponentDetailApi = async (componentId) => {
  const result = await request.get(`/components/${componentId}`)
  return result
}
