import apiClient from "./client"
import type { ApiResponse, Job, JobDetail, JobProgress, JobResult } from "@/types/api"

export const jobsApi = {
  list: async (params?: { page?: number; page_size?: number; status?: string }): Promise<{ items: Job[]; pagination: NonNullable<ApiResponse<unknown>["pagination"]> }> => {
    const res = await apiClient.get<ApiResponse<Job[]>>("/jobs", { params })
    return { items: res.data.data, pagination: res.data.pagination! }
  },

  getDetail: async (jobUuid: string): Promise<JobDetail> => {
    const res = await apiClient.get<ApiResponse<JobDetail>>(`/jobs/${jobUuid}`)
    return res.data.data
  },

  getProgress: async (jobUuid: string): Promise<JobProgress> => {
    const res = await apiClient.get<ApiResponse<JobProgress>>(`/jobs/${jobUuid}/progress`)
    return res.data.data
  },

  getResults: async (jobUuid: string): Promise<JobResult[]> => {
    const res = await apiClient.get<ApiResponse<JobResult[]>>(`/jobs/${jobUuid}/results`)
    return res.data.data
  },
}
