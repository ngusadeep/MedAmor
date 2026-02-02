import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authApi } from '@/lib/api'

type AuthState = {
  accessToken: string | null
  user: { id: string; username: string } | null
  setToken: (token: string) => void
  setUser: (user: { id: string; username: string } | null) => void
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  loadUser: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      user: null,
      setToken: (token) => {
        if (typeof window !== 'undefined') localStorage.setItem('access_token', token)
        set({ accessToken: token })
      },
      setUser: (user) => set({ user }),
      login: async (username, password) => {
        const { data } = await authApi.login(username, password)
        get().setToken(data.access_token)
        await get().loadUser()
      },
      logout: async () => {
        try { await authApi.logout() } catch { /* ignore */ }
        if (typeof window !== 'undefined') localStorage.removeItem('access_token')
        set({ accessToken: null, user: null })
      },
      loadUser: async () => {
        try {
          const { data } = await authApi.me()
          set({ user: { id: data.id, username: data.username } })
        } catch {
          set({ user: null })
        }
      },
    }),
    { name: 'medaudit-auth', partialize: (s) => ({ accessToken: s.accessToken, user: s.user }) }
  )
)
