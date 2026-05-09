/**
 * 元器件参数查询 API（严格按接口文档 V1.0）
 * 路由前缀：/api/v1/components
 */
import request from '../request'

// ============================================================
// Mock 数据
// ============================================================
const MOCK_MODE = true

const mockComponents = [
  { componentId: 301, model: 'STM32F103C8T6', type: 'MCU', packageType: 'LQFP48', manufacturer: 'STMicroelectronics' },
  { componentId: 302, model: 'STM32F103CBT6', type: 'MCU', packageType: 'LQFP48', manufacturer: 'STMicroelectronics' },
  { componentId: 303, model: 'ESP32-WROOM-32', type: 'WiFi模块', packageType: 'SMD', manufacturer: 'Espressif' },
  { componentId: 304, model: 'LM358N', type: '运算放大器', packageType: 'DIP-8', manufacturer: 'TI' },
  { componentId: 305, model: 'NE555', type: '定时器', packageType: 'DIP-8', manufacturer: 'TI' },
  { componentId: 306, model: 'ATmega328P', type: 'MCU', packageType: 'TQFP32', manufacturer: 'Microchip' },
  { componentId: 307, model: 'CH340G', type: 'USB转串口芯片', packageType: 'SOP-16', manufacturer: 'WCH' },
  { componentId: 308, model: 'AMS1117-3.3', type: 'LDO稳压器', packageType: 'SOT-223', manufacturer: 'AMS' },
]

const mockComponentDetails = {
  301: {
    componentId: 301,
    model: 'STM32F103C8T6',
    type: 'MCU',
    packageType: 'LQFP48',
    manufacturer: 'STMicroelectronics',
    coreParams: {
      core: 'ARM Cortex-M3',
      mainFreq: '72MHz',
      flash: '64KB',
      ram: '20KB',
      workVoltage: '2.0V-3.6V',
      pinCount: 48,
    },
    datasheetUrl: 'https://www.st.com/resource/en/datasheet/stm32f103c8.pdf',
    imageUrl: 'https://www.st.com/content/ccc/resource/graphic/registerszeichnung/group0/9c/67/0d/59/7d/59/4d/30/STM32F103C8T6.png/files/STM32F103C8T6.png/_jen_/STM32F103C8T6.png',
    updatedAt: '2026-04-20 10:20:00',
  },
}

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
 * GET /api/v1/components/search
 * 元器件搜索
 * keyword: 型号或关键词（必填）
 */
export const searchComponents = async ({
  keyword,
  pageNum = 1,
  pageSize = 10,
} = {}) => {
  if (MOCK_MODE) {
    await delay()
    if (!keyword) throwMockError(400, 'keyword 参数不能为空')
    const kw = keyword.toLowerCase()
    const filtered = mockComponents.filter(c =>
      c.model.toLowerCase().includes(kw) ||
      c.type.toLowerCase().includes(kw) ||
      c.manufacturer.toLowerCase().includes(kw),
    )
    if (filtered.length === 0) {
      throwMockError(404, '未查询到匹配的元器件')
    }
    const total = filtered.length
    const start = (pageNum - 1) * pageSize
    return {
      code: 200,
      message: '查询成功',
      data: { pageNum, pageSize, total, records: filtered.slice(start, start + pageSize) },
    }
  }
  return await request.get('/components/search', {
    params: { keyword, pageNum, pageSize },
  })
}

/**
 * GET /api/v1/components/{componentId}
 * 元器件参数详情
 */
export const getComponentDetail = async (componentId) => {
  if (MOCK_MODE) {
    await delay()
    const detail = mockComponentDetails[componentId]
    if (!detail) {
      const basic = mockComponents.find(c => c.componentId === componentId)
      if (!basic) throwMockError(404, '元器件不存在')
      return {
        code: 200,
        message: '查询成功',
        data: {
          componentId: basic.componentId,
          model: basic.model,
          type: basic.type,
          packageType: basic.packageType,
          manufacturer: basic.manufacturer,
          coreParams: {},
          datasheetUrl: '',
          imageUrl: '',
          updatedAt: '2026-04-20 10:20:00',
        },
      }
    }
    return { code: 200, message: '查询成功', data: detail }
  }
  return await request.get(`/components/${componentId}`)
}
