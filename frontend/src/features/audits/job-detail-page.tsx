import { useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import { ArrowLeft } from 'lucide-react'
import { getRouteApi } from '@tanstack/react-router'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  getJob,
  getAuditReportByJob,
  type AuditReportResponse,
} from '@/lib/jobs-api'

const route = getRouteApi('/_authenticated/audits/jobs/$jobId')

export function JobDetailPage() {
  const { jobId } = route.useParams()
  const { data: job, isLoading, error } = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => getJob(jobId),
  })
  const { data: report } = useQuery({
    queryKey: ['audit-report-by-job', jobId],
    queryFn: () => getAuditReportByJob(jobId),
    enabled: !!job?.id && job?.status === 'completed',
  })

  if (isLoading) {
    return (
      <>
        <Header fixed>
          <Search />
          <div className='ms-auto flex items-center space-x-4'>
            <ThemeSwitch />
            <ConfigDrawer />
            <ProfileDropdown />
          </div>
        </Header>
        <Main>
          <p className='text-muted-foreground'>Loading job…</p>
        </Main>
      </>
    )
  }
  if (error || !job) {
    return (
      <>
        <Header fixed>
          <Search />
          <div className='ms-auto flex items-center space-x-4'>
            <ThemeSwitch />
            <ConfigDrawer />
            <ProfileDropdown />
          </div>
        </Header>
        <Main>
          <p className='text-destructive'>Job not found or failed to load.</p>
          <Button variant='link' asChild>
            <Link to='/audits/jobs'>Back to jobs</Link>
          </Button>
        </Main>
      </>
    )
  }

  const statusVariant =
    job.status === 'completed'
      ? 'default'
      : job.status === 'failed'
        ? 'destructive'
        : 'secondary'

  return (
    <>
      <Header fixed>
        <Search />
        <div className='ms-auto flex items-center space-x-4'>
          <ThemeSwitch />
          <ConfigDrawer />
          <ProfileDropdown />
        </div>
      </Header>

      <Main className='flex flex-1 flex-col gap-4 sm:gap-6'>
        <div className='flex flex-wrap items-center gap-2'>
          <Button variant='ghost' size='sm' asChild>
            <Link to='/audits/jobs' className='gap-1'>
              <ArrowLeft className='h-4 w-4' />
              Back to jobs
            </Link>
          </Button>
        </div>

        <div className='space-y-4'>
          <h2 className='text-2xl font-bold tracking-tight'>Job details</h2>
          <Card>
            <CardHeader>
              <CardTitle className='font-mono text-sm'>
                Job {String(job.id).slice(0, 8)}…
              </CardTitle>
              <CardDescription>
                Patient {job.patient_id} · Created{' '}
                {new Date(job.created_at).toLocaleString()}
              </CardDescription>
            </CardHeader>
            <CardContent className='space-y-2'>
              <div className='flex items-center gap-2'>
                <span className='text-muted-foreground'>Status:</span>
                <Badge variant={statusVariant}>{job.status}</Badge>
              </div>
              {job.error_message && (
                <p className='text-sm text-destructive'>{job.error_message}</p>
              )}
            </CardContent>
          </Card>

          {report && (
            <Card>
              <CardHeader>
                <CardTitle>Audit report</CardTitle>
                <CardDescription>
                  Status: {report.status} · Risk: {report.risk_level ?? '—'}
                </CardDescription>
              </CardHeader>
              <CardContent className='space-y-4'>
                {report.executive_summary && (
                  <div>
                    <h4 className='mb-1 text-sm font-medium'>
                      Executive summary
                    </h4>
                    <p className='text-sm text-muted-foreground'>
                      {report.executive_summary}
                    </p>
                  </div>
                )}
                {report.findings && report.findings.length > 0 && (
                  <div>
                    <h4 className='mb-1 text-sm font-medium'>Findings</h4>
                    <ul className='list-inside list-disc space-y-1 text-sm text-muted-foreground'>
                      {(report.findings as { description?: string }[]).map(
                        (f, i) => (
                          <li key={i}>{f.description ?? JSON.stringify(f)}</li>
                        )
                      )}
                    </ul>
                  </div>
                )}
                {report.corrective_actions &&
                  report.corrective_actions.length > 0 && (
                    <div>
                      <h4 className='mb-1 text-sm font-medium'>
                        Corrective actions
                      </h4>
                      <ul className='list-inside list-disc space-y-1 text-sm text-muted-foreground'>
                        {report.corrective_actions.map((a, i) => (
                          <li key={i}>{a}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                <Button variant='outline' size='sm' asChild>
                  <Link
                    to='/audits/reports/$reportId'
                    params={{ reportId: report.id }}
                  >
                    View full report
                  </Link>
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </Main>
    </>
  )
}
