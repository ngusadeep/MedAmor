import { getRouteApi } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { listAuditReports } from '@/lib/jobs-api'
import { ReportsTable } from './components/reports-table'

const route = getRouteApi('/_authenticated/audits/reports/' as any)

export function AuditsReportsPage() {
  const search = route.useSearch()
  const navigate = route.useNavigate()

  const { data: reports = [] } = useQuery({
    queryKey: ['audit-reports'],
    queryFn: () => listAuditReports(),
  })

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
        <div>
          <h2 className='text-2xl font-bold tracking-tight'>Audit reports</h2>
          <p className='text-muted-foreground'>
            Completed audit reports: findings, evidence, and corrective
            actions.
          </p>
        </div>
        <ReportsTable
          data={reports}
          search={search}
          navigate={
            navigate as import('@/hooks/use-table-url-state').NavigateFn
          }
        />
      </Main>
    </>
  )
}
