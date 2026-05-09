import request from './request'

const mockComponentList = [
  {
    componentId: 'c001',
    model: 'STM32F103C8T6',
    type: 'MCU',
    packageType: 'LQFP48',
    manufacturer: 'ST',
    updatedAt: '2026-05-08 10:00:00',
  },
  {
    componentId: 'c002',
    model: 'LM358',
    type: '运放',
    packageType: 'SOP-8',
    manufacturer: 'TI',
    updatedAt: '2026-05-08 10:12:00',
  },
  {
    componentId: 'c003',
    model: 'AMS1117-3.3',
    type: '稳压器',
    packageType: 'SOT-223',
    manufacturer: 'AMS',
    updatedAt: '2026-05-08 10:25:00',
  },
]

const mockComponentDetail = {
  componentId: 'c001',
  model: 'STM32F103C8T6',
  type: 'MCU',
  packageType: 'LQFP48',
  manufacturer: 'ST',
  coreParams: {
    flash: '64KB',
    sram: '20KB',
    maxFreq: '72MHz',
    ioCount: '37',
  },
  datasheetUrl: '',
  imageUrl: '',
  updatedAt: '2026-05-08 10:00:00',
}

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

export const searchComponentsFallbackApi = async ({ keyword, pageNum = 1, pageSize = 10 }) => {
  await new Promise((resolve) => setTimeout(resolve, 250))

  const kw = (keyword || '').trim().toLowerCase()
  const filtered = mockComponentList.filter((item) => {
    if (!kw) return true
    return [item.model, item.type, item.manufacturer].some((value) =>
      String(value).toLowerCase().includes(kw),
    )
  })

  const start = (pageNum - 1) * pageSize
  const records = filtered.slice(start, start + pageSize)

  return {
    code: 200,
    message: '查询成功',
    data: {
      pageNum,
      pageSize,
      total: filtered.length,
      records,
    },
  }
}

export const getComponentDetailFallbackApi = async (componentId) => {
  await new Promise((resolve) => setTimeout(resolve, 200))
  return {
    code: 200,
    message: '查询成功',
    data: mockComponentDetail.componentId === componentId ? mockComponentDetail : null,
  }
}
