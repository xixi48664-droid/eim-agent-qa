import request from './request'

const mockComponentList = [
  {
    componentId: 'a7996aa05a6646c784769505d36316ae',
    model: 'STM32F103C8T6',
    type: 'MCU',
    packageType: 'LQFP48',
    manufacturer: 'STMicroelectronics',
  },
  {
    componentId: 'b2c3d4e5f6a7412ab3c4d5e6f7a81234',
    model: 'LM358',
    type: '运放',
    packageType: 'SOP-8',
    manufacturer: 'TI',
  },
  {
    componentId: 'c3d4e5f6a7b8412cb4d5e6f7a8b92345',
    model: 'AMS1117-3.3',
    type: '稳压器',
    packageType: 'SOT-223',
    manufacturer: 'AMS',
  },
]

const mockComponentDetailMap = {
  a7996aa05a6646c784769505d36316ae: {
    componentId: 'a7996aa05a6646c784769505d36316ae',
    model: 'STM32F103C8T6',
    type: 'MCU',
    packageType: 'LQFP48',
    manufacturer: 'STMicroelectronics',
    coreParams: {
      Flash: '64KB',
      引脚数: '48',
      工作电压: '2.0~3.6V',
      RAM: '20KB',
      主频: '72MHz',
      内核: 'ARM Cortex-M3',
    },
    datasheetUrl: 'https://www.st.com/resource/en/datasheet/stm32f103c8.pdf',
    imageUrl: null,
    updatedAt: '2026-05-06T14:35:48',
  },
  b2c3d4e5f6a7412ab3c4d5e6f7a81234: {
    componentId: 'b2c3d4e5f6a7412ab3c4d5e6f7a81234',
    model: 'LM358',
    type: '运放',
    packageType: 'SOP-8',
    manufacturer: 'TI',
    coreParams: {
      '供电电压': '3V~32V',
      '带宽': '1MHz',
      '静态电流': '0.7mA',
    },
    datasheetUrl: null,
    imageUrl: null,
    updatedAt: '2026-05-06T15:10:00',
  },
  c3d4e5f6a7b8412cb4d5e6f7a8b92345: {
    componentId: 'c3d4e5f6a7b8412cb4d5e6f7a8b92345',
    model: 'AMS1117-3.3',
    type: '稳压器',
    packageType: 'SOT-223',
    manufacturer: 'AMS',
    coreParams: {
      '输出电压': '3.3V',
      '输出电流': '1A',
      '压差': '1.3V',
    },
    datasheetUrl: null,
    imageUrl: null,
    updatedAt: '2026-05-06T15:25:00',
  },
}

export const searchComponentsApi = async ({ keyword, pageNum = 1, pageSize = 10 }) => {
  const result = await request.get('/components/search', {
    params: { keyword, pageNum, pageSize },
  })
  return result
}

export const getComponentDetailApi = async (componentId) => {
  const result = await request.get(`/components/${componentId}`)
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
    data: mockComponentDetailMap[componentId] || null,
  }
}
