import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import type { DashboardStats } from '../use-dashboard-stats'
import { AnalyticsChart } from './analytics-chart'

interface AnalyticsProps {
  stats?: DashboardStats | null
}

export function Analytics({ stats }: AnalyticsProps) {
  const jobStatusItems = stats
    ? [
        { name: 'Completed', value: stats.completedJobs },
        { name: 'Pending / Running', value: stats.pendingOrRunning },
        { name: 'Failed', value: stats.failedJobs },
      ].filter((i) => i.value > 0)
    : []

  const findingItems = stats
    ? [
        { name: 'No findings', value: stats.noFindings },
        { name: 'With findings', value: stats.withFindings },
      ].filter((i) => i.value > 0)
    : []

  return (
    <div className='space-y-4'>
      <Card>
        <CardHeader>
          <CardTitle>Audit jobs over time</CardTitle>
          <CardDescription>
            Weekly view (sample). Use Overview for monthly audits.
          </CardDescription>
        </CardHeader>
        <CardContent className='px-6'>
          <AnalyticsChart />
        </CardContent>
      </Card>
      <div className='grid gap-4 sm:grid-cols-2 lg:grid-cols-4'>
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>Total jobs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>{stats?.totalJobs ?? '—'}</div>
            <p className='text-xs text-muted-foreground'>All audit jobs</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>Completed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>
              {stats?.completedJobs ?? '—'}
            </div>
            <p className='text-xs text-muted-foreground'>Successful audits</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>With findings</CardTitle>
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>
              {stats?.withFindings ?? '—'}
            </div>
            <p className='text-xs text-muted-foreground'>FINDING_PRESENT</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>Compliance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>
              {stats != null ? `${stats.complianceRatePct}%` : '—'}
            </div>
            <p className='text-xs text-muted-foreground'>No findings rate</p>
          </CardContent>
        </Card>
      </div>
      <div className='grid grid-cols-1 gap-4 lg:grid-cols-2'>
        <Card>
          <CardHeader>
            <CardTitle>Job status</CardTitle>
            <CardDescription>Breakdown by status</CardDescription>
          </CardHeader>
          <CardContent>
            {jobStatusItems.length > 0 ? (
              <SimpleBarList
                items={jobStatusItems}
                barClass='bg-primary'
                valueFormatter={(n) => `${n}`}
              />
            ) : (
              <p className='text-sm text-muted-foreground'>
                No job data yet.
              </p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Findings</CardTitle>
            <CardDescription>Reports with vs without findings</CardDescription>
          </CardHeader>
          <CardContent>
            {findingItems.length > 0 ? (
              <SimpleBarList
                items={findingItems}
                barClass='bg-muted-foreground'
                valueFormatter={(n) => `${n}`}
              />
            ) : (
              <p className='text-sm text-muted-foreground'>
                No report data yet.
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function SimpleBarList({
  items,
  valueFormatter,
  barClass,
}: {
  items: { name: string; value: number }[]
  valueFormatter: (n: number) => string
  barClass: string
}) {
  const max = Math.max(...items.map((i) => i.value), 1)
  return (
    <ul className='space-y-3'>
      {items.map((i) => {
        const width = `${Math.round((i.value / max) * 100)}%`
        return (
          <li key={i.name} className='flex items-center justify-between gap-3'>
            <div className='min-w-0 flex-1'>
              <div className='mb-1 truncate text-xs text-muted-foreground'>
                {i.name}
              </div>
              <div className='h-2.5 w-full rounded-full bg-muted'>
                <div
                  className={`h-2.5 rounded-full ${barClass}`}
                  style={{ width }}
                />
              </div>
            </div>
            <div className='ps-2 text-xs font-medium tabular-nums'>
              {valueFormatter(i.value)}
            </div>
          </li>
        )
      })}
    </ul>
  )
}
