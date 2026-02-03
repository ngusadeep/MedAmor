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
import { getAuditReport } from '@/lib/jobs-api'

const route = getRouteApi(
  '/_authenticated/audits/reports/$reportId' as any
)

export function ReportDetailPage() {
  const { reportId } = route.useParams()
  const { data: report, isLoading, error } = useQuery({
    queryKey: ['audit-report', reportId],
    queryFn: () => getAuditReport(reportId),
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
          <p className='text-muted-foreground'>Loading report…</p>
        </Main>
      </>
    )
  }
  if (error || !report) {
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
          <p className='text-destructive'>
            Report not found or failed to load.
          </p>
          <Button variant='link' asChild>
            <Link to={'/audits/reports' as any}>Back to reports</Link>
          </Button>
        </Main>
      </>
    )
  }

  const findings = (report.findings ?? []) as {
    category?: string
    description?: string
    responsible_doctor?: string
    urgency?: string
  }[]
  const evidence = (report.evidence ?? []) as {
    kb_source?: string
    ehr_snippet?: string
    image_ref?: string
  }[]

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
            <Link to={'/audits/reports' as '/'} className='gap-1'>
              <ArrowLeft className='h-4 w-4' />
              Back to reports
            </Link>
          </Button>
        </div>

        <div className='space-y-4'>
          <h2 className='text-2xl font-bold tracking-tight'>
            Audit report
          </h2>
          <Card>
            <CardHeader>
              <CardTitle className='font-mono text-sm'>
                Report {String(report.id).slice(0, 8)}…
              </CardTitle>
              <CardDescription>
                Job {String(report.job_id).slice(0, 8)}… · Patient{' '}
                {report.patient_id} ·{' '}
                {new Date(report.created_at).toLocaleString()}
              </CardDescription>
            </CardHeader>
            <CardContent className='flex flex-wrap gap-2'>
              <Badge
                variant={
                  report.status === 'NO_FINDINGS' ? 'default' : 'destructive'
                }
              >
                {report.status === 'NO_FINDINGS'
                  ? 'No findings'
                  : 'Findings present'}
              </Badge>
              {report.risk_level && (
                <Badge variant='outline'>{report.risk_level}</Badge>
              )}
            </CardContent>
          </Card>

          {report.executive_summary && (
            <Card>
              <CardHeader>
                <CardTitle>Executive summary</CardTitle>
              </CardHeader>
              <CardContent>
                <p className='text-muted-foreground'>
                  {report.executive_summary}
                </p>
              </CardContent>
            </Card>
          )}

          {findings.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Findings</CardTitle>
                <CardDescription>
                  {findings.length} finding(s)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className='space-y-3'>
                  {findings.map((f, i) => (
                    <li
                      key={i}
                      className='rounded-lg border p-3 text-sm'
                    >
                      {f.category && (
                        <span className='font-medium text-muted-foreground'>
                          {f.category}
                        </span>
                      )}
                      <p className='mt-1'>{f.description}</p>
                      {f.responsible_doctor && (
                        <p className='mt-1 text-muted-foreground'>
                          Responsible: {f.responsible_doctor}
                        </p>
                      )}
                      {f.urgency && (
                        <Badge variant='outline' className='mt-1'>
                          {f.urgency}
                        </Badge>
                      )}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {evidence.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Evidence</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className='space-y-2 text-sm text-muted-foreground'>
                  {evidence.map((e, i) => (
                    <li key={i} className='rounded border p-2'>
                      {e.kb_source && <div>KB: {e.kb_source}</div>}
                      {e.ehr_snippet && (
                        <div className='mt-1 truncate'>{e.ehr_snippet}</div>
                      )}
                      {e.image_ref && <div>Ref: {e.image_ref}</div>}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {report.corrective_actions &&
            report.corrective_actions.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Corrective actions</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className='list-inside list-disc space-y-1 text-sm text-muted-foreground'>
                    {report.corrective_actions.map((a, i) => (
                      <li key={i}>{a}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}

          {report.next_audit_date && (
            <Card>
              <CardHeader>
                <CardTitle>Next audit date</CardTitle>
              </CardHeader>
              <CardContent>
                <p className='text-muted-foreground'>
                  {new Date(report.next_audit_date).toLocaleDateString()}
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </Main>
    </>
  )
}
