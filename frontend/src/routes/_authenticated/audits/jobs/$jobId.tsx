import { createFileRoute } from '@tanstack/react-router'
import { JobDetailPage } from '@/features/audits/job-detail-page'

export const Route = createFileRoute(
  '/_authenticated/audits/jobs/$jobId' as any
)({
  component: JobDetailPage,
})
