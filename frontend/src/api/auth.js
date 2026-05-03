export const loginApi = async ({ username, password }) => {
  await new Promise((resolve) => setTimeout(resolve, 300))

  const validUsers = {
    admin: {
      password: '123456',
      token: 'mock-admin-token',
      userInfo: {
        id: 1,
        username: 'admin',
        nickname: '管理员',
        role: 'admin',
      },
    },
    user: {
      password: '123456',
      token: 'mock-user-token',
      userInfo: {
        id: 2,
        username: 'user',
        nickname: '普通用户',
        role: 'user',
      },
    },
  }

  const account = validUsers[username]

  if (!account || account.password !== password) {
    throw new Error('账号或密码错误')
  }

  return {
    code: 0,
    message: '登录成功',
    data: {
      token: account.token,
      userInfo: account.userInfo,
    },
  }
}
