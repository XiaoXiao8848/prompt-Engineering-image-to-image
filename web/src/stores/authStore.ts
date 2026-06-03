import { create } from "zustand"
import type { User } from "@/types/api"

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  accessToken: string | null
  refreshToken: string | null
  setAuth: (tokens: { access_token: string; refresh_token: string }, user: User) => void
  clearAuth: () => void
  setUser: (user: User) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  accessToken: localStorage.getItem("access_token"),
  refreshToken: localStorage.getItem("refresh_token"),

  setAuth: (tokens, user) => {
    localStorage.setItem("access_token", tokens.access_token)
    localStorage.setItem("refresh_token", tokens.refresh_token)
    set({
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
      user,
      isAuthenticated: true,
    })
  },

  clearAuth: () => {
    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")
    set({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
    })
  },

  setUser: (user) => set({ user }),
}))
