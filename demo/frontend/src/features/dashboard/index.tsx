import { ClipboardList, FileCheck, FileText, TrendingUp } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { TopNav } from '@/components/layout/top-nav'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { Analytics } from './components/analytics'
import { Overview, buildDataFromReports } from './components/overview'
import { RecentActivity } from './components/recent-activity'
import { useDashboardStats } from './use-dashboard-stats'

export function Dashboard() {
  const { data: stats, isLoading, error } = useDashboardStats()

  const overviewData =
    stats && (stats.reports?.length ?? 0) > 0
      ? buildDataFromReports(stats.reports.map((r) => r.created_at))
      : undefined

  return (
    <>
      <Header>
        <TopNav links={topNav} />
        <div className='ms-auto flex items-center space-x-4'>
          <Search />
          <ThemeSwitch />
          <ConfigDrawer />
          <ProfileDropdown />
        </div>
      </Header>

      <Main>
        <div className='mb-2 flex items-center justify-between space-y-2'>
          <h1 className='text-2xl font-bold tracking-tight'>
            Breast Cancer Screening Audit
          </h1>
          <div className='flex items-center space-x-2'>
            <Button variant='outline' asChild>
              <a href='/audits/jobs'>New screening audit job</a>
            </Button>
          </div>
        </div>

        {error && (
          <div className='mb-4 rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-2 text-sm text-destructive'>
            {error.message}
          </div>
        )}

        <Tabs
          orientation='vertical'
          defaultValue='overview'
          className='space-y-4'
        >
          <div className='w-full overflow-x-auto pb-2'>
            <TabsList>
              <TabsTrigger value='overview'>Overview</TabsTrigger>
              <TabsTrigger value='analytics'>Analytics</TabsTrigger>
            </TabsList>
          </div>
          <TabsContent value='overview' className='space-y-4'>
            <div className='grid gap-4 sm:grid-cols-2 lg:grid-cols-4'>
              <Card>
                <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
                  <CardTitle className='text-sm font-medium'>
                    Total screening jobs
                  </CardTitle>
                  <ClipboardList className='h-4 w-4 text-muted-foreground' />
                </CardHeader>
                <CardContent>
                  <div className='text-2xl font-bold'>
                    {isLoading ? '—' : stats?.totalJobs ?? 0}
                  </div>
                  <p className='text-xs text-muted-foreground'>
                    Screening audit jobs (all statuses)
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
                  <CardTitle className='text-sm font-medium'>
                    Completed audits
                  </CardTitle>
                  <FileCheck className='h-4 w-4 text-muted-foreground' />
                </CardHeader>
                <CardContent>
                  <div className='text-2xl font-bold'>
                    {isLoading ? '—' : stats?.completedJobs ?? 0}
                  </div>
                  <p className='text-xs text-muted-foreground'>
                    Jobs finished successfully
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
                  <CardTitle className='text-sm font-medium'>
                    With findings
                  </CardTitle>
                  <FileText className='h-4 w-4 text-muted-foreground' />
                </CardHeader>
                <CardContent>
                  <div className='text-2xl font-bold'>
                    {isLoading ? '—' : stats?.withFindings ?? 0}
                  </div>
                  <p className='text-xs text-muted-foreground'>
                    Reports with FINDING_PRESENT
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
                  <CardTitle className='text-sm font-medium'>
                    Compliance rate
                  </CardTitle>
                  <TrendingUp className='h-4 w-4 text-muted-foreground' />
                </CardHeader>
                <CardContent>
                  <div className='text-2xl font-bold'>
                    {isLoading ? '—' : `${stats?.complianceRatePct ?? 0}%`}
                  </div>
                  <p className='text-xs text-muted-foreground'>
                    No findings (NO_FINDINGS)
                  </p>
                </CardContent>
              </Card>
            </div>
            <div className='grid grid-cols-1 gap-4 lg:grid-cols-7'>
              <Card className='col-span-1 lg:col-span-4'>
                <CardHeader>
                  <CardTitle>Audits this year</CardTitle>
                  <CardDescription>
                    Completed audit reports by month
                  </CardDescription>
                </CardHeader>
                <CardContent className='ps-2'>
                  <Overview reportsByMonth={overviewData} />
                </CardContent>
              </Card>
              <Card className='col-span-1 lg:col-span-3'>
                <CardHeader>
                  <CardTitle>Recent activity</CardTitle>
                  <CardDescription>
                    Latest jobs and reports
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <RecentActivity
                    recentJobs={stats?.recentJobs ?? []}
                    recentReports={stats?.recentReports ?? []}
                  />
                </CardContent>
              </Card>
            </div>
          </TabsContent>
          <TabsContent value='analytics' className='space-y-4'>
            <Analytics stats={stats} />
          </TabsContent>
        </Tabs>
      </Main>
    </>
  )
}

const topNav = [
  { title: 'Overview', href: '#', isActive: true, disabled: false },
  { title: 'Audit Jobs', href: '/audits/jobs', isActive: false, disabled: false },
  { title: 'Reports', href: '/audits/reports', isActive: false, disabled: false },
  { title: 'Settings', href: '/settings', isActive: false, disabled: false },
]
