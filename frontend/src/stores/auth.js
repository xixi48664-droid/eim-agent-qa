import { defineStore } from 'pinia'

const AUTH_TOKEN_KEY = 'eim_token'              //存储token的key
const AUTH_USERINFO_KEY = 'eim_user_info'       //存储用户信息的key

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
    token: getSavedToken(),
    userInfo: getSavedUserInfo(),
  }),
  getters: {
    isLoggedIn: (state) => Boolean(state.token),
  },
  actions: {
    setToken(token) {
      this.token = token
      localStorage.setItem(AUTH_TOKEN_KEY, token)
    },
    setUserInfo(userInfo) {
      this.userInfo = userInfo
      localStorage.setItem(AUTH_USERINFO_KEY, JSON.stringify(userInfo))
    },
    hydrateAuth() {
      this.token = getSavedToken()
      this.userInfo = getSavedUserInfo()
    },
    clearAuth() {
      this.token = ''
      this.userInfo = null
      localStorage.removeItem(AUTH_TOKEN_KEY)
      localStorage.removeItem(AUTH_USERINFO_KEY)
    },
  },
})
