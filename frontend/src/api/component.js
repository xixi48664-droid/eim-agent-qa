const mockComponents = [
  {
    id: 1,
    name: '登录页校验',
    type: '页面',
    status: '已完成',
    owner: '前端组',
    updatedAt: '2026-05-04 10:00:00',
  },
  {
    id: 2,
    name: '首页布局',
    type: '布局',
    status: '进行中',
    owner: '前端组',
    updatedAt: '2026-05-04 10:20:00',
  },
  {
    id: 3,
    name: '接口写死适配层',
    type: '接口',
    status: '待开始',
    owner: '后端协作',
    updatedAt: '2026-05-04 10:30:00',
  },
]

export const getComponentListApi = async (params = {}) => {
  await new Promise((resolve) => setTimeout(resolve, 300))

  const keyword = (params.keyword || '').trim().toLowerCase()
  const status = params.status || ''

  const list = mockComponents.filter((item) => {
    const matchKeyword = !keyword || item.name.toLowerCase().includes(keyword)
    const matchStatus = !status || item.status === status
    return matchKeyword && matchStatus
  })

  return {
    code: 0,
    message: '获取成功',
    data: {
      list,
      total: list.length,
    },
  }
}
