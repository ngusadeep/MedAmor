import { createFileRoute } from '@tanstack/react-router'
import { LandingPage } from '@/features/landing/landing-page'

// Route id matches file path; route tree will include this when generated
export const Route = createFileRoute('/(marketing)/landing')({
  component: LandingPage,
})
