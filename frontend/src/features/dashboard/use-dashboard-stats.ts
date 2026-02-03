import { useQuery } from '@tanstack/react-query'
import {
  listJobs,
  listAuditReports,
  type JobResponse,
  type AuditReportResponse,
} from '@/lib/jobs-api'

export interface DashboardStats {
  totalJobs: number
  completedJobs: number
  pendingOrRunning: number
  failedJobs: number
  totalReports: number
  withFindings: number
  noFindings: number
  complianceRatePct: number
  recentJobs: JobResponse[]
  recentReports: AuditReportResponse[]
  reports: AuditReportResponse[]
}

export function useDashboardStats(): {
  data: DashboardStats | undefined
  isLoading: boolean
  error: Error | null
} {
  const jobsQuery = useQuery({
    queryKey: ['dashboard', 'jobs'],
    queryFn: () => listJobs(),
    staleTime: 30_000,
  })
  const reportsQuery = useQuery({
    queryKey: ['dashboard', 'audit-reports'],
    queryFn: () => listAuditReports(),
    staleTime: 30_000,
  })

  const jobs = jobsQuery.data ?? []
  const reports = reportsQuery.data ?? []

  const completedJobs = jobs.filter((j) => j.status === 'completed').length
  const pendingOrRunning = jobs.filter(
    (j) => j.status === 'pending' || j.status === 'running'
  ).length
  const failedJobs = jobs.filter((j) => j.status === 'failed').length
  const withFindings = reports.filter((r) => r.status === 'FINDING_PRESENT').length
  const noFindings = reports.filter((r) => r.status === 'NO_FINDINGS').length
  const totalWithResult = withFindings + noFindings
  const complianceRatePct =
    totalWithResult > 0 ? Math.round((noFindings / totalWithResult) * 100) : 0

  const recentJobs = [...jobs].sort(
    (a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  ).slice(0, 5)
  const recentReports = [...reports]
    .sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )
    .slice(0, 5)

  const data: DashboardStats = {
    totalJobs: jobs.length,
    completedJobs,
    pendingOrRunning,
    failedJobs,
    totalReports: reports.length,
    withFindings,
    noFindings,
    complianceRatePct,
    recentJobs,
    recentReports,
    reports,
  }

  return {
    data,
    isLoading: jobsQuery.isLoading || reportsQuery.isLoading,
    error: jobsQuery.error ?? reportsQuery.error ?? null,
  }
}
