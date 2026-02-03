import { useEffect } from 'react'
import { getRouteApi } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { listJobs } from '@/lib/jobs-api'
import { JobsTable } from './components/jobs-table'
import { JobsPrimaryButtons } from './components/jobs-primary-buttons'
import { CreateJobDialog } from './components/create-job-dialog'
import { JobsProvider, useJobs } from './components/jobs-provider'

const route = getRouteApi('/_authenticated/audits/jobs/')

function JobsPageInner() {
  const search = route.useSearch()
  const navigate = route.useNavigate()
  const { setOnSuccess } = useJobs()

  const { data: jobs = [], refetch } = useQuery({
    queryKey: ['jobs'],
    queryFn: () => listJobs(),
  })

  useEffect(() => {
    setOnSuccess(() => refetch())
  }, [refetch, setOnSuccess])

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
        <div className='flex flex-wrap items-end justify-between gap-2'>
          <div>
            <h2 className='text-2xl font-bold tracking-tight'>Audit jobs</h2>
            <p className='text-muted-foreground'>
              Create and monitor EHR audit jobs. Select a patient to run an
              audit.
            </p>
          </div>
          <JobsPrimaryButtons />
        </div>
        <JobsTable data={jobs} search={search} navigate={navigate} />
      </Main>

      <CreateJobDialog />
    </>
  )
}

export function AuditsJobsPage() {
  return (
    <JobsProvider>
      <JobsPageInner />
    </JobsProvider>
  )
}
