import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { RefreshCw, Users, Zap } from 'lucide-react'
import { toast } from 'sonner'

import { PatientsTable } from './components/patients-table'
import { PatientStats } from './components/patient-stats'
import {
  listPatients,
  getPatientStats,
  syncPatients,
  updatePatientStatus,
  listPatientsDueForReview,
  createJobsBatch,
} from '@/lib/jobs-api'

export function PatientsPage() {
  const [isSyncing, setIsSyncing] = useState(false)
  const [activeTab, setActiveTab] = useState('all')

  const { data: patients = [], isLoading, refetch } = useQuery({
    queryKey: ['patients'],
    queryFn: () => listPatients(),
  })

  const { data: stats, refetch: refetchStats } = useQuery({
    queryKey: ['patient-stats'],
    queryFn: () => getPatientStats(),
  })

  const loadData = () => {
    refetch()
    refetchStats()
  }

  const handleSyncPatients = async () => {
    setIsSyncing(true)
    try {
      await syncPatients()
      toast.success('Patient list refreshed from EHR')
      setTimeout(loadData, 1000)
    } catch {
      toast.error('Failed to sync patients')
    } finally {
      setIsSyncing(false)
    }
  }

  const handleUpdateStatus = async () => {
    try {
      await updatePatientStatus()
      toast.success('Status is computed from latest reports')
      loadData()
    } catch {
      toast.error('Failed to refresh status')
    }
  }

  const handleBatchAudit = async () => {
    try {
      const duePatients = await listPatientsDueForReview()
      if (duePatients.length === 0) {
        toast.info('No patients due for review')
        return
      }
      const patientIds = duePatients.map(p => p.patient_id)
      await createJobsBatch({
        patient_ids: patientIds,
        audit_type: 'breast_cancer_screening',
        triggered_by: 'batch_audit',
      })
      toast.success(`Created audit jobs for ${duePatients.length} patients`)
      setTimeout(loadData, 1000)
    } catch {
      toast.error('Failed to create batch audit')
    }
  }

  const filteredPatients = patients.filter((patient) => {
    if (activeTab === 'all') return true
    if (activeTab === 'due') return patient.status === 'due_for_review' || patient.status === 'needs_attention'
    if (activeTab === 'never') return patient.status === 'never_audited'
    return patient.status === activeTab
  })

  return (
    <>
      <Header fixed>
        <Search />
        <div className="ms-auto flex items-center space-x-4">
          <ThemeSwitch />
          <ConfigDrawer />
          <ProfileDropdown />
        </div>
      </Header>

      <Main className="flex flex-1 flex-col gap-4 sm:gap-6">
        <div className="flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Patients</h2>
            <p className="text-muted-foreground">
              Monitor audit status, last/next review dates, and run batch audits for due patients.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleSyncPatients} disabled={isSyncing}>
              <RefreshCw className={`mr-2 h-4 w-4 ${isSyncing ? 'animate-spin' : ''}`} />
              Sync
            </Button>
            <Button variant="outline" size="sm" onClick={handleUpdateStatus}>
              <Users className="mr-2 h-4 w-4" />
              Refresh status
            </Button>
            <Button size="sm" onClick={handleBatchAudit}>
              <Zap className="mr-2 h-4 w-4" />
              Batch audit due
            </Button>
          </div>
        </div>

        {stats && <PatientStats stats={stats} isLoading={isLoading} />}

        <Card>
          <CardHeader>
            <CardTitle>Patient list</CardTitle>
            <p className="text-sm text-muted-foreground">
              Filter by status; last audit and next review come from the latest report.
            </p>
          </CardHeader>
          <CardContent>
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-5">
                <TabsTrigger value="all">All ({patients.length})</TabsTrigger>
                <TabsTrigger value="due">Due ({stats?.due_for_review_count ?? 0})</TabsTrigger>
                <TabsTrigger value="needs_attention">
                  Needs attention ({stats?.status_counts?.needs_attention ?? 0})
                </TabsTrigger>
                <TabsTrigger value="never_audited">
                  Never audited ({stats?.status_counts?.never_audited ?? 0})
                </TabsTrigger>
                <TabsTrigger value="compliant">
                  Compliant ({stats?.status_counts?.compliant ?? 0})
                </TabsTrigger>
              </TabsList>
              <TabsContent value={activeTab} className="mt-4">
                <PatientsTable patients={filteredPatients} isLoading={isLoading} />
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </Main>
    </>
  )
}