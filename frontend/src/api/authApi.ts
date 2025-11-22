import { request } from './http'
import type { AuthToken, User } from '../types/user'

export interface SignupPayload {
  username: string
  password: string
}

export async function signup(payload: SignupPayload): Promise<User> {
  return request<User>('/auth/signup', {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export interface LoginPayload {
  username: string
  password: string
}

export async function login(payload: LoginPayload): Promise<AuthToken> {
  const body = new URLSearchParams()
  body.set('username', payload.username)
  body.set('password', payload.password)

  return request<AuthToken>('/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body
  })
}

export async function getMe(): Promise<User> {
  return request<User>('/auth/me')
}
