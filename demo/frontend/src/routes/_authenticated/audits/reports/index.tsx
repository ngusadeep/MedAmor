import z from 'zod'
import { createFileRoute } from '@tanstack/react-router'
import { AuditsReportsPage } from '@/features/audits/index-reports'

const reportsSearchSchema = z.object({
  page: z.number().optional().catch(1),
  pageSize: z.number().optional().catch(10),
  patient_id: z.string().optional().catch(''),
  status: z.array(z.string()).optional().catch([]),
})

export const Route = createFileRoute(
  '/_authenticated/audits/reports/' as any
)({
  validateSearch: reportsSearchSchema,
  component: AuditsReportsPage,
})
