import { defineStore } from 'pinia'

const AUTH_TOKEN_KEY = 'eim_token'
const AUTH_USERINFO_KEY = 'eim_user_info'

const getSavedToken = () => localStorage.getItem(AUTH_TOKEN_KEY) || ''

const getSavedUserInfo = () => {
  const raw = localStorage.getItem(AUTH_USERINFO_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

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
      localStorage.setItem(AUTH_TOKEN_KEY, token)
      localStorage.setItem(AUTH_USERINFO_KEY, JSON.stringify({ userId, account, role, status, nickname }))
    },
    setToken(token) {
      this.token = token
      localStorage.setItem(AUTH_TOKEN_KEY, token)
    },
    setUserInfo(userInfo) {
      Object.assign(this, userInfo)
      if (userInfo.nickname !== undefined) this.nickname = userInfo.nickname || userInfo.account || ''
      localStorage.setItem(AUTH_USERINFO_KEY, JSON.stringify(userInfo))
    },
    hydrateAuth() {
      this.token = getSavedToken()
      const info = getSavedUserInfo()
      if (info) {
        this.userId = info.userId ?? null
        this.account = info.account ?? ''
        this.role = info.role ?? ''
        this.status = info.status ?? ''
        this.nickname = info.nickname ?? info.account ?? ''
      }
    },
    clearAuth() {
      this.token = ''
      this.userId = null
      this.account = ''
      this.role = ''
      this.status = ''
      this.nickname = ''
      localStorage.removeItem(AUTH_TOKEN_KEY)
      localStorage.removeItem(AUTH_USERINFO_KEY)
    },
  },
})
