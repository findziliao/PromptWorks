export interface PromptTag {
  id: number
  name: string
  color: string
  created_at: string
  updated_at: string
}

export interface PromptClass {
  id: number
  name: string
  description: string | null
  created_at: string
  updated_at: string
}

export interface PromptVersion {
  id: number
  prompt_id: number
  version: string
  content: string
  created_at: string
  updated_at: string
}

export type PromptCollaboratorRole = 'viewer' | 'editor'

export interface PromptCollaborator {
  id: number
  user_id: number
  username: string
  role: PromptCollaboratorRole
  created_at: string
}

export interface PromptImplementationRecord {
  id: number
  prompt_id: number
  content: string
  created_at: string
}

export interface Prompt {
  id: number
  name: string
  description: string | null
  author: string | null
  owner_id: number | null
  prompt_class: PromptClass
  current_version: PromptVersion | null
  versions: PromptVersion[]
  tags: PromptTag[]
  created_at: string
  updated_at: string
  completed_at: string | null
}
