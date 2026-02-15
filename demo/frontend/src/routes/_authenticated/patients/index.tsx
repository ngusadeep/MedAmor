import { createFileRoute } from '@tanstack/react-router'
import { PatientsPage } from '@/features/patients'

export const Route = createFileRoute('/_authenticated/patients/' as any)({
  component: PatientsPage,
})