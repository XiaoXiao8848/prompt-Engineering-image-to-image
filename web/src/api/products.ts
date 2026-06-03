import apiClient from "./client"
import type { ApiResponse, Product, ProductCreate } from "@/types/api"

export const productsApi = {
  list: async (params?: { page?: number; page_size?: number; keyword?: string }): Promise<{ items: Product[]; pagination: NonNullable<ApiResponse<unknown>["pagination"]> }> => {
    const res = await apiClient.get<ApiResponse<Product[]>>('/products', { params })
    return { items: res.data.data, pagination: res.data.pagination! }
  },

  create: async (data: ProductCreate): Promise<Product> => {
    const res = await apiClient.post<ApiResponse<Product>>("/products", data)
    return res.data.data
  },

  update: async (uuid: string, data: Partial<ProductCreate>): Promise<Product> => {
    const res = await apiClient.put<ApiResponse<Product>>(`/products/${uuid}`, data)
    return res.data.data
  },

  delete: async (uuid: string): Promise<void> => {
    await apiClient.delete(`/products/${uuid}`)
  },

  getByUuid: async (uuid: string): Promise<Product> => {
    const res = await apiClient.get<ApiResponse<Product>>(`/products/${uuid}`)
    return res.data.data
  },
}
