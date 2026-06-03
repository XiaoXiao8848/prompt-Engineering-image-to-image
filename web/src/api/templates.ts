import apiClient from "./client"
import type { ApiResponse, Template, TemplateVersion } from "@/types/api"

export const templatesApi = {
  list: async (params?: { page?: number; page_size?: number; scene_id?: number; template_type?: string }): Promise<{ items: Template[]; pagination: NonNullable<ApiResponse<unknown>["pagination"]> }> => {
    const res = await apiClient.get<ApiResponse<Template[]>>('/templates', { params })
    return { items: res.data.data, pagination: res.data.pagination! }
  },

  getByUuid: async (uuid: string): Promise<Template> => {
    const res = await apiClient.get<ApiResponse<Template>>(`/templates/${uuid}`)
    return res.data.data
  },

  render: async (uuid: string, variables: Record<string, unknown>): Promise<string> => {
    const res = await apiClient.post<ApiResponse<{ rendered: string }>>(`/templates/${uuid}/render`, { variables })
    return res.data.data.rendered
  },

  versions: async (uuid: string): Promise<TemplateVersion[]> => {
    const res = await apiClient.get<ApiResponse<TemplateVersion[]>>(`/templates/${uuid}/versions`)
    return res.data.data
  },
}
