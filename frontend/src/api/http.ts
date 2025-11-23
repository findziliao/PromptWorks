const DEFAULT_BASE_URL = 'http://localhost:8000/api/v1'
const ACCESS_TOKEN_KEY = 'promptworks:access_token'

function normalizeBaseUrl(url: string | undefined): string {
  if (!url) return DEFAULT_BASE_URL
  return url.endsWith('/') ? url.slice(0, -1) : url
}

export const API_BASE_URL = normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL)

export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = window.localStorage.getItem(ACCESS_TOKEN_KEY)
    return raw && raw.trim() ? raw : null
  } catch (error) {
    console.warn('读取本地访问令牌失败', error)
    return null
  }
}

export function setAccessToken(token: string | null): void {
  if (typeof window === 'undefined') return
  try {
    if (token && token.trim()) {
      window.localStorage.setItem(ACCESS_TOKEN_KEY, token)
    } else {
      window.localStorage.removeItem(ACCESS_TOKEN_KEY)
    }
  } catch (error) {
    console.warn('写入本地访问令牌失败', error)
  }
}

type HttpMethod = 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE'

export interface HttpError extends Error {
  status?: number
  payload?: unknown
}

async function parseJsonSafely(response: Response): Promise<unknown> {
  const text = await response.text()
  if (!text) return null
  try {
    return JSON.parse(text)
  } catch (error) {
    console.warn('解析接口返回 JSON 失败', error)
    return text
  }
}

export async function request<T>(
  path: string,
  options: RequestInit & { method?: HttpMethod } = {}
): Promise<T> {
  const url = `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`
  const accessToken = getAccessToken()
  const baseHeaders: Record<string, string> = {
    'Content-Type': 'application/json'
  }
  const extraHeaders = (options.headers ?? {}) as Record<string, string>
  if (accessToken && !('Authorization' in extraHeaders)) {
    baseHeaders.Authorization = `Bearer ${accessToken}`
  }

  const merged: RequestInit = {
    ...options,
    headers: {
      ...baseHeaders,
      ...extraHeaders
    }
  }

  const response = await fetch(url, merged)

  if (!response.ok) {
    const error: HttpError = new Error('请求接口失败')
    error.status = response.status
    error.payload = await parseJsonSafely(response)
    throw error
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await parseJsonSafely(response)) as T
}
