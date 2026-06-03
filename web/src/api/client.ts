import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios"
import type { ApiResponse } from "@/types/api"

const apiClient = axios.create({
  baseURL: "/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
})

// Request interceptor: attach JWT token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem("access_token")
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor: unwrap data, handle errors
apiClient.interceptors.response.use(
  (response) => {
    const data = response.data as ApiResponse<unknown>
    if (data.code !== "SUCCESS") {
      return Promise.reject(new Error(data.message || "请求失败"))
    }
    return response
  },
  (error: AxiosError<ApiResponse<unknown>>) => {
    const message = error.response?.data?.message || error.message || "网络错误"
    return Promise.reject(new Error(message))
  }
)

export default apiClient
