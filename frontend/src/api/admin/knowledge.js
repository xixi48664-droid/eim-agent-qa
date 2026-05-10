/**
 * 知识库管理 API
 * 路由前缀：/api/v1/admin/knowledge
 * 列表分页：{ pageNum, pageSize, total, records: [] }
 */
import request from '../request'

// ============================================================
// Mock 数据
// ============================================================
const MOCK_MODE = true

const mockKnowledgeBases = [
  { id: 1, name: 'LM358运算放大器手册', type: 'product', typeLabel: '产品文档', count: 42, status: 'active', lastUpdate: '2026-03-20', updater: '陈管理员' },
  { id: 2, name: 'IPC-2221A印制板设计规范', type: 'standard', typeLabel: '行业规范', count: 118, status: 'active', lastUpdate: '2026-03-15', updater: '陈管理员' },
  { id: 3, name: '电子元器件参数数据库', type: 'param', typeLabel: '参数数据', count: 245, status: 'active', lastUpdate: '2026-03-28', updater: '系统自动' },
  { id: 4, name: 'SMT贴片工艺流程库', type: 'process', typeLabel: '工艺流程', count: 36, status: 'active', lastUpdate: '2026-02-28', updater: '陈管理员' },
  { id: 5, name: 'RoHS有害物质限量标准', type: 'standard', typeLabel: '行业规范', count: 28, status: 'active', lastUpdate: '2026-01-10', updater: '陈管理员' },
  { id: 6, name: '旧版元器件型录（2022）', type: 'product', typeLabel: '产品文档', count: 17, status: 'disabled', lastUpdate: '2022-12-31', updater: '陈管理员' },
]

const typeOptions = [
  { value: 'all', label: '全部' },
  { value: 'product', label: '产品文档' },
  { value: 'standard', label: '行业规范' },
  { value: 'param', label: '参数数据' },
  { value: 'process', label: '工艺流程' },
]

let nextId = 7
const delay = (ms = 300) => new Promise(resolve => setTimeout(resolve, ms))
const throwMockError = (code, message) => {
  const err = new Error(message)
  err.response = { data: { code, message, data: null } }
  throw err
}

// ============================================================
// API 函数
// ============================================================

/**
 * GET /api/v1/admin/knowledge
 */
export const getKnowledgeList = async ({
  search = '',
  type = 'all',
  pageNum = 1,
  pageSize = 10,
} = {}) => {
  if (MOCK_MODE) {
    await delay()
    let filtered = [...mockKnowledgeBases]
    if (search) filtered = filtered.filter(k => k.name.toLowerCase().includes(search.toLowerCase()))
    if (type && type !== 'all') filtered = filtered.filter(k => k.type === type)
    const total = filtered.length
    const start = (pageNum - 1) * pageSize
    return {
      code: 200,
      message: '查询成功',
      data: { pageNum, pageSize, total, records: filtered.slice(start, start + pageSize) },
    }
  }
  const params = { pageNum, pageSize }
  if (search) params.search = search
  if (type && type !== 'all') params.type = type
  return await request.get('/admin/knowledge', { params })
}

/**
 * POST /api/v1/admin/knowledge
 */
export const addKnowledge = async (data) => {
  if (MOCK_MODE) {
    await delay()
    const item = {
      id: nextId++,
      ...data,
      typeLabel: typeOptions.find(t => t.value === data.type)?.label || data.type,
      count: 0,
      status: 'active',
      lastUpdate: new Date().toISOString().split('T')[0],
      updater: '陈管理员',
    }
    mockKnowledgeBases.unshift(item)
    return { code: 200, message: '添加成功', data: item }
  }
  return await request.post('/admin/knowledge', data)
}

/**
 * PUT /api/v1/admin/knowledge/{id}
 */
export const updateKnowledge = async (id, data) => {
  if (MOCK_MODE) {
    await delay()
    const idx = mockKnowledgeBases.findIndex(k => k.id === id)
    if (idx === -1) throwMockError(404, '知识库不存在')
    mockKnowledgeBases[idx] = { ...mockKnowledgeBases[idx], ...data }
    return { code: 200, message: '更新成功', data: mockKnowledgeBases[idx] }
  }
  return await request.put(`/admin/knowledge/${id}`, data)
}

/**
 * DELETE /api/v1/admin/knowledge/{id}
 */
export const deleteKnowledge = async (id) => {
  if (MOCK_MODE) {
    await delay()
    const idx = mockKnowledgeBases.findIndex(k => k.id === id)
    if (idx === -1) throwMockError(404, '知识库不存在')
    mockKnowledgeBases.splice(idx, 1)
    return { code: 200, message: '删除成功', data: null }
  }
  return await request.delete(`/admin/knowledge/${id}`)
}

/**
 * POST /api/v1/admin/knowledge/{id}/sync
 */
export const syncKnowledge = async (id) => {
  if (MOCK_MODE) {
    await delay(800)
    const kb = mockKnowledgeBases.find(k => k.id === id)
    if (!kb) throwMockError(404, '知识库不存在')
    kb.lastUpdate = new Date().toISOString().split('T')[0]
    return { code: 200, message: '同步完成', data: null }
  }
  return await request.post(`/admin/knowledge/${id}/sync`)
}

/**
 * POST /api/v1/admin/knowledge/export
 */
export const exportKnowledge = async (ids) => {
  if (MOCK_MODE) {
    await delay(500)
    return { code: 200, message: `已导出 ${ids.length} 个知识库`, data: null }
  }
  return await request.post('/admin/knowledge/export', { ids })
}

/**
 * POST /api/v1/admin/knowledge/import
 */
export const importKnowledge = async (formData) => {
  if (MOCK_MODE) {
    await delay(1000)
    const item = {
      id: nextId++,
      name: '新导入知识库_' + Date.now(),
      type: 'product',
      typeLabel: '产品文档',
      count: 0,
      status: 'active',
      lastUpdate: new Date().toISOString().split('T')[0],
      updater: '陈管理员',
    }
    mockKnowledgeBases.unshift(item)
    return { code: 200, message: '导入成功', data: item }
  }
  return await request.post('/admin/knowledge/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export { typeOptions }
