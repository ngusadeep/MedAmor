import { createFileRoute } from '@tanstack/react-router'
import { ReportDetailPage } from '@/features/audits/report-detail-page'

export const Route = createFileRoute(
  '/_authenticated/audits/reports/$reportId' as any
)({
  component: ReportDetailPage,
})
