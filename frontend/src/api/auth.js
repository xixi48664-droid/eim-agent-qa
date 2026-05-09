import request from './request'

export const loginApi = (data) => {
  return request.post('/api/v1/auth/login', data)
}
