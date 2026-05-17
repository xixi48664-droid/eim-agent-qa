import request from './request'

export const getProfileApi = () => {
  return request.get('/user/profile')
}

export const updateProfileApi = (data) => {
  return request.put('/user/profile', data)
}

export const changePasswordApi = ({ oldPassword, newPassword, confirmPassword }) => {
  return request.post('/user/change-password', { oldPassword, newPassword, confirmPassword })
}

export const getUserStatsApi = () => {
  return request.get('/user/stats')
}

export const getUserActivitiesApi = ({ pageNum = 1, pageSize = 10 } = {}) => {
  return request.get('/user/activities', { params: { pageNum, pageSize } })
}
