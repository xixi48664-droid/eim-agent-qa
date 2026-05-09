import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: '',
    userId: null,
    account: '',
    role: '',
    status: '',
    nickname: '',
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    isAdmin: (state) => state.role === 'admin',
  },
  actions: {
    setAuth({ token, userId, account, role, status, nickname }) {
      this.token = token
      this.userId = userId
      this.account = account || ''
      this.role = role || ''
      this.status = status || ''
      this.nickname = nickname || account || ''
    },
    setToken(token) {
      this.token = token
    },
    clearAuth() {
      this.token = ''
      this.userId = null
      this.account = ''
      this.role = ''
      this.status = ''
      this.nickname = ''
    },
  },
})
