import apiClient from "./client"
import type { ApiResponse, Scene, SceneCategory } from "@/types/api"

export const scenesApi = {
  list: async (params?: { page?: number; page_size?: number; keyword?: string; category_id?: number }): Promise<{ items: Scene[]; pagination: NonNullable<ApiResponse<unknown>["pagination"]> }> => {
    const res = await apiClient.get<ApiResponse<Scene[]>>("/scenes", { params })
    return { items: res.data.data, pagination: res.data.pagination! }
  },

  categories: async (): Promise<SceneCategory[]> => {
    const res = await apiClient.get<ApiResponse<SceneCategory[]>>("/scenes/categories")
    return res.data.data
  },

  getByUuid: async (uuid: string): Promise<Scene> => {
    const res = await apiClient.get<ApiResponse<Scene>>(`/scenes/${uuid}`)
    return res.data.data
  },
}
