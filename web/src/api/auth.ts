import apiClient from "./client"
import type { ApiResponse, LoginRequest, RegisterRequest, TokenResponse, User } from "@/types/api"

export const authApi = {
  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const res = await apiClient.post<ApiResponse<TokenResponse>>("/auth/login", data)
    return res.data.data
  },

  register: async (data: RegisterRequest): Promise<User> => {
    const res = await apiClient.post<ApiResponse<User>>("/auth/register", data)
    return res.data.data
  },

  refresh: async (refreshToken: string): Promise<TokenResponse> => {
    const res = await apiClient.post<ApiResponse<TokenResponse>>("/auth/refresh", {
      refresh_token: refreshToken,
    })
    return res.data.data
  },

  getMe: async (): Promise<User> => {
    const res = await apiClient.get<ApiResponse<User>>("/auth/me")
    return res.data.data
  },
}
