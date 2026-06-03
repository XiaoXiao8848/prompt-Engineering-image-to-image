export interface ApiResponse<T> {
  code: string
  message: string
  data: T
  pagination?: PaginationInfo
}

export interface PaginationInfo {
  page: number
  page_size: number
  total: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

export interface User {
  id: number
  username: string
  email: string
  display_name: string | null
  avatar_url: string | null
  role: "admin" | "user" | "api"
  status: "active" | "inactive" | "banned"
  quota_daily: number
  quota_used_today: number
  created_at: string
  updated_at: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  display_name?: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface Product {
  id: number
  product_uuid: string
  product_id: string
  product_name: string
  brand: string | null
  material: string | null
  shape: string | null
  color: string | null
  size: string | null
  lock_tags: string
  selling_points: string[] | null
  reference_image: Record<string, unknown> | null
  material_keywords: string[] | null
  brand_tone: string | null
  status: string
  created_at: string
  updated_at: string
}

export interface ProductCreate {
  product_id: string
  product_name: string
  brand?: string
  material?: string
  shape?: string
  color?: string
  size?: string
  lock_tags: string
  selling_points?: string[]
  reference_image?: Record<string, unknown>
  material_keywords?: string[]
  brand_tone?: string
}

export interface Scene {
  id: number
  scene_uuid: string
  scene_id: string
  name: string
  description: string | null
  lighting: string | null
  background: string | null
  props: string[] | null
  atmosphere: string | null
  keywords: string[] | null
  category_id: number | null
  is_builtin: boolean
  is_public: boolean
  status: string
  created_at: string
}

export interface SceneCategory {
  id: number
  name: string
  description: string | null
  sort_order: number
  created_at: string
}

export interface Template {
  id: number
  template_uuid: string
  scene_id: number
  name: string
  template_type: "system" | "positive" | "negative" | "meta"
  content: string
  variables: string[] | null
  is_default: boolean
  status: string
  created_at: string
  updated_at: string
}

export interface TemplateVersion {
  id: number
  version: number
  content: string
  change_note: string | null
  created_at: string
}

export interface GeneratePromptRequest {
  product_uuid: string
  scene_id: string
  mode: "template" | "llm"
  use_cache?: boolean
  llm_model?: string
  llm_temperature?: number
}

export interface GeneratedPrompt {
  prompt: string
  negative_prompt: string
  parameters: Record<string, unknown>
  cache_hit: boolean
  scene_id: string
  scene_name: string
}

export interface BatchGenerateRequest {
  product_uuid: string
  scene_ids: string[]
  mode: "template" | "llm"
  use_cache?: boolean
  llm_model?: string
  llm_temperature?: number
  webhook_url?: string
}

export interface BatchGenerateResponse {
  job_uuid: string
  status: string
  total_tasks: number
}

export interface Job {
  job_uuid: string
  mode: string
  status: string
  total_tasks: number
  completed_tasks: number
  failed_tasks: number
  created_at: string
}

export interface JobDetail {
  job_uuid: string
  product_id: number
  mode: string
  scene_ids: string[]
  status: string
  total_tasks: number
  completed_tasks: number
  failed_tasks: number
  llm_model: string | null
  llm_temperature: number | null
  webhook_url: string | null
  started_at: string | null
  completed_at: string | null
  error_message: string | null
  created_at: string
}

export interface JobProgress {
  job_uuid: string
  status: string
  total_tasks: number
  completed_tasks: number
  failed_tasks: number
  progress_percent: number
  started_at: string | null
  completed_at: string | null
  error_message: string | null
}

export interface JobResult {
  result_uuid: string
  scene_id: number
  status: string
  prompt: string | null
  negative_prompt: string | null
  parameters: Record<string, unknown> | null
  cache_hit: boolean
  error_message: string | null
  completed_at: string | null
}
