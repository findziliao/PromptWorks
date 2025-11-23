import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { User } from '../types/user'
import { getAccessToken, setAccessToken } from '../api/http'
import { getMe, login as loginApi, signup as signupApi } from '../api/authApi'

const currentUser = ref<User | null>(null)
const loadingUser = ref(false)
const authToken = ref<string | null>(getAccessToken())

const isAuthenticated = computed(() => currentUser.value != null)

async function internalLoadUser(): Promise<void> {
  const token = authToken.value || getAccessToken()
  if (!token) {
    currentUser.value = null
    return
  }

  loadingUser.value = true
  try {
    const user = await getMe()
    currentUser.value = user
  } catch (error) {
    console.warn('[auth] load current user failed', error)
    await logout()
  } finally {
    loadingUser.value = false
  }
}

export function useAuth() {
  async function login(payload: { username: string; password: string }): Promise<void> {
    try {
      const token = await loginApi(payload)
      authToken.value = token.access_token
      setAccessToken(token.access_token)
      await internalLoadUser()
      ElMessage.success('登录成功')
    } catch (error) {
      console.warn('[auth] login failed', error)
      let message = '登录失败，请检查用户名和密码'
      if (error instanceof Error && error.message) {
        message = error.message
      } else if (error && typeof error === 'object' && 'payload' in error) {
        const payload = (error as { payload?: unknown }).payload
        if (payload && typeof payload === 'object' && 'detail' in payload) {
          const detail = (payload as Record<string, unknown>).detail
          if (typeof detail === 'string' && detail.trim()) {
            message = detail
          }
        }
      }
      ElMessage.error(message)
      throw error
    }
  }

  async function signup(payload: { username: string; password: string }): Promise<void> {
    try {
      await signupApi(payload)
      ElMessage.success('注册成功，请使用新账号登录')
    } catch (error) {
      console.warn('[auth] signup failed', error)
      let message = '注册失败，请稍后重试'
      if (error && typeof error === 'object' && 'payload' in error) {
        const payload = (error as { payload?: unknown }).payload
        if (payload && typeof payload === 'object' && 'detail' in payload) {
          const detail = (payload as Record<string, unknown>).detail
          if (typeof detail === 'string' && detail.trim()) {
            message = detail
          }
        }
      }
      ElMessage.error(message)
      throw error
    }
  }

  async function logout(): Promise<void> {
    authToken.value = null
    setAccessToken(null)
    currentUser.value = null
  }

  async function loadUser(): Promise<void> {
    await internalLoadUser()
  }

  return {
    currentUser,
    authToken,
    loadingUser,
    isAuthenticated,
    login,
    signup,
    logout,
    loadUser
  }
}
