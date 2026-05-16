/**
 * 知识库管理 API — 聚合后端 components / standards / tutorials 三组真实接口
 */
import request from '../request'

const typeOptions = [
  { value: 'all', label: '全部' },
  { value: 'product', label: '产品文档' },
  { value: 'standard', label: '行业规范' },
  { value: 'param', label: '参数数据' },
  { value: 'process', label: '工艺流程' },
]

// type 到后端资源的映射
const resourceApi = (type) => {
  if (type === 'standard') return 'standards'
  if (type === 'process') return 'tutorials'
  return 'components' // product / param / 默认
}

// 后端记录 → 知识库统一行格式
const toRow = (item, api) => {
  if (api === 'standards') {
    return {
      id: item.standardId, name: item.standardName, type: 'standard', typeLabel: '行业规范',
      count: 1, status: 'active', lastUpdate: '', updater: '管理员', _api: 'standards',
    }
  }
  if (api === 'tutorials') {
    return {
      id: item.tutorialId, name: item.processName, type: 'process', typeLabel: '工艺流程',
      count: item.totalSteps ?? 0, status: 'active',
      lastUpdate: (item.createTime || '').substring(0, 10), updater: '管理员', _api: 'tutorials',
    }
  }
  return {
    id: item.componentId, name: item.model, type: item.type || 'param', typeLabel: '参数数据',
    count: item.paramCount ?? 0, status: 'active',
    lastUpdate: (item.updateTime || item.createTime || '').substring(0, 10),
    updater: '管理员', _api: 'components',
  }
}

/**
 * GET 列表
 */
export const getKnowledgeList = async ({
  search = '',
  type = 'all',
  pageNum = 1,
  pageSize = 10,
} = {}) => {
  if (type !== 'all') {
    const api = resourceApi(type)
    const params = { pageNum, pageSize }
    if (search) {
      if (api === 'standards') params.standardName = search
      else if (api === 'tutorials') params.processName = search
      else params.model = search
    }
    const res = await request.get(`/admin/${api}`, { params })
    return { code: 200, data: { pageNum, pageSize, total: res.data.total, records: (res.data.records || []).map(r => toRow(r, api)) } }
  }

  const [compRes, stdRes, tutRes] = await Promise.all([
    request.get('/admin/components', { params: { pageNum: 1, pageSize: 1000 } }),
    request.get('/admin/standards', { params: { pageNum: 1, pageSize: 1000 } }),
    request.get('/admin/tutorials', { params: { pageNum: 1, pageSize: 1000 } }),
  ])

  let all = [
    ...(compRes.data.records || []).map(r => toRow(r, 'components')),
    ...(stdRes.data.records || []).map(r => toRow(r, 'standards')),
    ...(tutRes.data.records || []).map(r => toRow(r, 'tutorials')),
  ]

  if (search) {
    const kw = search.toLowerCase()
    all = all.filter(i => i.name.toLowerCase().includes(kw))
  }

  const total = all.length
  const start = (pageNum - 1) * pageSize
  return { code: 200, data: { pageNum, pageSize, total, records: all.slice(start, start + pageSize) } }
}

/**
 * POST 新增
 */
export const addKnowledge = async (data) => {
  const api = resourceApi(data.type)
  let payload
  if (api === 'standards') {
    payload = { standardName: data.name, standardCode: '', section: '', summary: '', tags: '', relatedProcess: '' }
  } else if (api === 'tutorials') {
    payload = { processName: data.name, estimatedTime: '', steps: [] }
  } else {
    payload = { model: data.name, type: '', packageType: '', manufacturer: '', datasheetUrl: '', params: [] }
  }
  return await request.post(`/admin/${api}`, payload)
}

/**
 * PUT 更新
 */
export const updateKnowledge = async (id, data) => {
  const api = resourceApi(data.type)
  let payload
  if (api === 'standards') {
    payload = { standardName: data.name }
  } else if (api === 'tutorials') {
    payload = { processName: data.name }
  } else {
    payload = { model: data.name }
  }
  return await request.put(`/admin/${api}/${id}`, payload)
}

/**
 * DELETE 删除 — 需要传 row 对象（含 _api 字段）
 */
export const deleteKnowledge = async (id, row) => {
  const api = row?._api || 'components'
  return await request.delete(`/admin/${api}/${id}`)
}

/**
 * 同步（暂无后端接口）
 */
export const syncKnowledge = async (id) => {
  return { code: 200, message: '同步请求已提交', data: null }
}

/**
 * 导出（暂无后端接口）
 */
export const exportKnowledge = async (ids) => {
  return { code: 200, message: `已导出 ${ids.length} 个知识库`, data: null }
}

/**
 * 导入（暂无后端接口）
 */
export const importKnowledge = async (formData) => {
  return { code: 200, message: '导入成功', data: null }
}

export { typeOptions }
