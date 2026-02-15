import { createFileRoute, redirect } from '@tanstack/react-router'
import { AuthenticatedLayout } from '@/components/layout/authenticated-layout'
import { useAuthStore } from '@/stores/auth-store'
import { me } from '@/lib/auth-api'

export const Route = createFileRoute('/_authenticated')({
  beforeLoad: async ({ location }) => {
    const user = await me()
    if (!user) {
      throw redirect({
        to: '/sign-in',
        search: { redirect: location.href },
        replace: true,
      })
    }
    useAuthStore.getState().auth.setUser({ id: user.id, username: user.username })
    useAuthStore.getState().auth.setAccessToken('ok')
  },
  component: AuthenticatedLayout,
})
