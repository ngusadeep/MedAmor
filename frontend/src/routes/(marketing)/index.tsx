import { createFileRoute, redirect } from '@tanstack/react-router'
import { LandingPage } from '@/features/landing/landing-page'
import { me } from '@/lib/auth-api'

export const Route = createFileRoute('/(marketing)/')({
  beforeLoad: async () => {
    try {
      const user = await me()
      if (user) {
        throw redirect({ to: '/dashboard', replace: true })
      }
    } catch (err) {
      // Re-throw redirects so the router handles them
      if (err && typeof err === 'object' && 'to' in err) throw err
      // Network/API error: show landing page
    }
  },
  component: LandingPage,
})