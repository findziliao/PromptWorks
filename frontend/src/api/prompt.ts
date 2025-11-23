import { request, type HttpError } from './http'
import type {
  Prompt,
  PromptCollaborator,
  PromptVersion,
  PromptImplementationRecord
} from '../types/prompt'

export interface PromptListParams {
  q?: string
  limit?: number
  offset?: number
}

export interface PromptCreatePayload {
  name: string
  description?: string | null
  author?: string | null
  class_id?: number
  class_name?: string
  class_description?: string | null
  version: string
  content: string
  tag_ids?: number[]
}

export interface PromptUpdatePayload {
  name?: string | null
  description?: string | null
  author?: string | null
  class_id?: number
  class_name?: string
  class_description?: string | null
  version?: string | null
  content?: string | null
  activate_version_id?: number | null
  tag_ids?: number[] | null
}

export interface PromptSharePayload {
  username: string
  role: 'viewer' | 'editor'
}

export interface PromptImplementationCreatePayload {
  content: string
}

export async function listPrompts(params: PromptListParams = {}): Promise<Prompt[]> {
  const searchParams = new URLSearchParams()
  if (params.q) searchParams.set('q', params.q)
  if (typeof params.limit === 'number') searchParams.set('limit', String(params.limit))
  if (typeof params.offset === 'number') searchParams.set('offset', String(params.offset))
  const query = searchParams.toString()
  const path = `/prompts${query ? `?${query}` : ''}`
  return request<Prompt[]>(path)
}

export async function getPrompt(promptId: number): Promise<Prompt> {
  return request<Prompt>(`/prompts/${promptId}`)
}

export async function createPrompt(payload: PromptCreatePayload): Promise<Prompt> {
  return request<Prompt>('/prompts/', {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export async function updatePrompt(
  promptId: number,
  payload: PromptUpdatePayload
): Promise<Prompt> {
  return request<Prompt>(`/prompts/${promptId}`, {
    method: 'PUT',
    body: JSON.stringify(payload)
  })
}

export async function deletePrompt(promptId: number): Promise<void> {
  await request<void>(`/prompts/${promptId}`, {
    method: 'DELETE'
  })
}

export async function createPromptVersion(
  promptId: number,
  version: string,
  content: string
): Promise<Prompt> {
  return updatePrompt(promptId, { version, content })
}

export async function switchPromptVersion(
  promptId: number,
  version: PromptVersion
): Promise<Prompt> {
  return updatePrompt(promptId, { activate_version_id: version.id })
}

export async function listPromptCollaborators(promptId: number): Promise<PromptCollaborator[]> {
  return request<PromptCollaborator[]>(`/prompts/${promptId}/collaborators`)
}

export async function sharePrompt(
  promptId: number,
  payload: PromptSharePayload
): Promise<PromptCollaborator> {
  return request<PromptCollaborator>(`/prompts/${promptId}/share`, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export async function revokePromptShare(promptId: number, userId: number): Promise<void> {
  await request<void>(`/prompts/${promptId}/share/${userId}`, {
    method: 'DELETE'
  })
}

export async function listPromptImplementations(
  promptId: number
): Promise<PromptImplementationRecord[]> {
  return request<PromptImplementationRecord[]>(`/prompts/${promptId}/implementations`)
}

export async function createPromptImplementation(
  promptId: number,
  payload: PromptImplementationCreatePayload
): Promise<PromptImplementationRecord> {
  return request<PromptImplementationRecord>(`/prompts/${promptId}/implementations`, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export type { HttpError }
