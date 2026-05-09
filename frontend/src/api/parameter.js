import request from './request'

export const searchComponentsApi = async ({ keyword, pageNum = 1, pageSize = 10 }) => {
  const result = await request.get('/api/v1/components/search', {
    params: { keyword, pageNum, pageSize },
  })
  return result
}

export const getComponentDetailApi = async (componentId) => {
  const result = await request.get(`/api/v1/components/${componentId}`)
  return result
}
