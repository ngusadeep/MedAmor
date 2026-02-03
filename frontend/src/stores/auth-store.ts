import { create } from 'zustand'

export interface AuthUser {
  id: string
  username: string
}

interface AuthState {
  auth: {
    user: AuthUser | null
    setUser: (user: AuthUser | null) => void
    accessToken: string
    setAccessToken: (token: string) => void
    reset: () => void
  }
}

export const useAuthStore = create<AuthState>()((set) => ({
  auth: {
    user: null,
    setUser: (user) =>
      set((state) => ({ ...state, auth: { ...state.auth, user } })),
    accessToken: '',
    setAccessToken: (token) =>
      set((state) => ({ ...state, auth: { ...state.auth, accessToken: token } })),
    reset: () =>
      set((state) => ({
        ...state,
        auth: { ...state.auth, user: null, accessToken: '' },
      })),
  },
}))
