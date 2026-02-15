import { ClipboardList, FileCheck, FileX } from 'lucide-react'
import type { JobResponse, AuditReportResponse } from '@/lib/jobs-api'
import { Badge } from '@/components/ui/badge'

interface RecentActivityProps {
  recentJobs: JobResponse[]
  recentReports: AuditReportResponse[]
}

function formatDate(iso: string) {
  const d = new Date(iso)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffMins = Math.floor(diffMs / 60_000)
  if (diffMins < 60) return `${diffMins}m ago`
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  return d.toLocaleDateString()
}

function statusVariant(
  status: string
): 'default' | 'secondary' | 'destructive' | 'outline' {
  if (status === 'completed') return 'default'
  if (status === 'NO_FINDINGS') return 'default'
  if (status === 'FINDING_PRESENT') return 'destructive'
  if (status === 'failed') return 'destructive'
  return 'secondary'
}

export function RecentActivity({
  recentJobs,
  recentReports,
}: RecentActivityProps) {
  const hasJobs = recentJobs.length > 0
  const hasReports = recentReports.length > 0

  return (
    <div className='space-y-6'>
      {hasJobs && (
        <div>
          <h4 className='mb-2 text-sm font-medium text-muted-foreground'>
            Recent jobs
          </h4>
          <ul className='space-y-3'>
            {recentJobs.map((job) => (
              <li
                key={job.id}
                className='flex items-center justify-between gap-2 rounded-lg border p-2'
              >
                <div className='flex min-w-0 items-center gap-2'>
                  <ClipboardList className='h-4 w-4 shrink-0 text-muted-foreground' />
                  <div className='min-w-0'>
                    <p className='truncate text-sm font-medium'>
                      Patient {job.patient_id}
                    </p>
                    <p className='text-xs text-muted-foreground'>
                      {formatDate(job.created_at)}
                    </p>
                  </div>
                </div>
                <Badge variant={statusVariant(job.status)}>{job.status}</Badge>
              </li>
            ))}
          </ul>
        </div>
      )}
      {hasReports && (
        <div>
          <h4 className='mb-2 text-sm font-medium text-muted-foreground'>
            Recent reports
          </h4>
          <ul className='space-y-3'>
            {recentReports.map((report) => (
              <li
                key={report.id}
                className='flex items-center justify-between gap-2 rounded-lg border p-2'
              >
                <div className='flex min-w-0 items-center gap-2'>
                  {report.status === 'NO_FINDINGS' ? (
                    <FileCheck className='h-4 w-4 shrink-0 text-green-600' />
                  ) : (
                    <FileX className='h-4 w-4 shrink-0 text-amber-600' />
                  )}
                  <div className='min-w-0'>
                    <p className='truncate text-sm font-medium'>
                      Patient {report.patient_id}
                    </p>
                    <p className='text-xs text-muted-foreground'>
                      {formatDate(report.created_at)}
                    </p>
                  </div>
                </div>
                <Badge variant={statusVariant(report.status)}>
                  {report.status === 'NO_FINDINGS' ? 'No findings' : 'Findings'}
                </Badge>
              </li>
            ))}
          </ul>
        </div>
      )}
      {!hasJobs && !hasReports && (
        <p className='text-sm text-muted-foreground'>
          No jobs or reports yet. Create an audit job to get started.
        </p>
      )}
    </div>
  )
}
