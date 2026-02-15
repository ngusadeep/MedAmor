import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
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
  PatientStats as PatientStatisticsType
} from '@/lib/jobs-api'
import type { Patient } from './data/schema'

export function PatientsPage() {
  const [patients, setPatients] = useState<Patient[]>([])
  const [stats, setStats] = useState<PatientStatisticsType | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSyncing, setIsSyncing] = useState(false)
  const [activeTab, setActiveTab] = useState('all')

  const loadData = async () => {
    setIsLoading(true)
    try {
      const [patientsData, statsData] = await Promise.all([
        listPatients(),
        getPatientStats(),
      ])
      setPatients(patientsData)
      setStats(statsData)
    } catch (error) {
      toast.error('Failed to load patient data')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSyncPatients = async () => {
    setIsSyncing(true)
    try {
      await syncPatients()
      toast.success('Patient sync started in background')
      // Reload data after a short delay
      setTimeout(loadData, 2000)
    } catch (error) {
      toast.error('Failed to sync patients')
    } finally {
      setIsSyncing(false)
    }
  }

  const handleUpdateStatus = async () => {
    try {
      const result = await updatePatientStatus()
      toast.success(`Updated ${result.updated_patients} patient statuses`)
      loadData()
    } catch (error) {
      toast.error('Failed to update patient statuses')
    }
  }

  const handleBatchAudit = async () => {
    try {
      const duePatients = await listPatientsDueForReview()
      if (duePatients.length === 0) {
        toast.info('All patients are up to date')
        return
      }

      const patientIds = duePatients.map(p => p.patient_id)
      await createJobsBatch({
        patient_ids: patientIds,
        audit_type: 'breast_cancer_screening',
        triggered_by: 'batch_audit',
      })

      toast.success(`Created audit jobs for ${duePatients.length} patients`)

      // Reload data after a short delay
      setTimeout(loadData, 1000)
    } catch (error) {
      toast.error('Failed to create batch audit')
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const filteredPatients = patients.filter((patient) => {
    if (activeTab === 'all') return true
    if (activeTab === 'due') return patient.status === 'due_for_review' || patient.status === 'needs_attention'
    if (activeTab === 'never') return patient.status === 'never_audited'
    return patient.status === activeTab
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Patient Management</h1>
          <p className="text-muted-foreground">
            Monitor patient audit status and manage review schedules
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            onClick={handleSyncPatients}
            disabled={isSyncing}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${isSyncing ? 'animate-spin' : ''}`} />
            Sync Patients
          </Button>
          <Button variant="outline" onClick={handleUpdateStatus}>
            <Users className="mr-2 h-4 w-4" />
            Update Status
          </Button>
          <Button onClick={handleBatchAudit}>
            <Zap className="mr-2 h-4 w-4" />
            Batch Audit
          </Button>
        </div>
      </div>

      {/* Stats Dashboard */}
      {stats && <PatientStats stats={stats} isLoading={isLoading} />}

      {/* Patients Table */}
      <Card>
        <CardHeader>
          <CardTitle>Patients</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="all">All ({patients.length})</TabsTrigger>
              <TabsTrigger value="due">Due Review ({stats?.due_for_review_count || 0})</TabsTrigger>
              <TabsTrigger value="needs_attention">
                Needs Attention ({stats?.status_counts.needs_attention || 0})
              </TabsTrigger>
              <TabsTrigger value="never_audited">
                Never Audited ({stats?.status_counts.never_audited || 0})
              </TabsTrigger>
              <TabsTrigger value="compliant">
                Compliant ({stats?.status_counts.compliant || 0})
              </TabsTrigger>
            </TabsList>

            <TabsContent value={activeTab} className="mt-6">
              <PatientsTable patients={filteredPatients} isLoading={isLoading} />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}