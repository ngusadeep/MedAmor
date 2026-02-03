import z from 'zod'
import { createFileRoute } from '@tanstack/react-router'
import { AuditsJobsPage } from '@/features/audits/index-jobs'

const jobsSearchSchema = z.object({
  page: z.number().optional().catch(1),
  pageSize: z.number().optional().catch(10),
  patient_id: z.string().optional().catch(''),
  status: z.array(z.string()).optional().catch([]),
})

export const Route = createFileRoute('/_authenticated/audits/jobs/' as any)({
  validateSearch: jobsSearchSchema,
  component: AuditsJobsPage,
})
