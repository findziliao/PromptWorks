import { request } from './http'
import type { User } from '../types/user'

export interface UserListParams {
  q?: string
  limit?: number
  offset?: number
}

export interface UserAdminUpdatePayload {
  password?: string
  is_active?: boolean
  is_superuser?: boolean
}

export async function listUsers(params: UserListParams = {}): Promise<User[]> {
  const searchParams = new URLSearchParams()
  if (params.q) searchParams.set('q', params.q)
  if (typeof params.limit === 'number') searchParams.set('limit', String(params.limit))
  if (typeof params.offset === 'number') searchParams.set('offset', String(params.offset))
  const query = searchParams.toString()
  const path = `/users${query ? `?${query}` : ''}`
  return request<User[]>(path)
}

export async function getUser(userId: number): Promise<User> {
  return request<User>(`/users/${userId}`)
}

export async function updateUser(
  userId: number,
  payload: UserAdminUpdatePayload
): Promise<User> {
  return request<User>(`/users/${userId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload)
  })
}
