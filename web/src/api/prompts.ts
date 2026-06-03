import apiClient from "./client"
import type { ApiResponse, GeneratePromptRequest, GeneratedPrompt, BatchGenerateRequest, BatchGenerateResponse } from "@/types/api"

export const promptsApi = {
  generate: async (data: GeneratePromptRequest): Promise<GeneratedPrompt> => {
    const res = await apiClient.post<ApiResponse<GeneratedPrompt>>("/prompts/generate", data)
    return res.data.data
  },

  generateBatch: async (data: BatchGenerateRequest): Promise<BatchGenerateResponse> => {
    const res = await apiClient.post<ApiResponse<BatchGenerateResponse>>("/prompts/generate/batch", data)
    return res.data.data
  },
}
