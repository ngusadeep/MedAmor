"use client"

import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { useAuthStore } from "@/stores/auth-store"
import { BaseLayout } from "@/components/layouts/base-layout"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { auditReportsApi, ehrApi, jobsApi, type AuditReport, type EHRPatientSummary } from "@/lib/api"
import { LoadingSpinner } from "@/components/ui/loading-spinner"

export default function AuditsPage() {
  const navigate = useNavigate()
  const accessToken = useAuthStore((s) => s.accessToken)
  const [reports, setReports] = useState<AuditReport[]>([])
  const [patients, setPatients] = useState<EHRPatientSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [triggerOpen, setTriggerOpen] = useState(false)
  const [selectedPatientId, setSelectedPatientId] = useState<string>("")
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!accessToken) {
      navigate("/auth/sign-in", { replace: true })
      return
    }
  }, [accessToken, navigate])

  useEffect(() => {
    if (!accessToken) return
    let cancelled = false
    async function load() {
      try {
        const [reportsRes, patientsRes] = await Promise.all([
          auditReportsApi.list(),
          ehrApi.listPatients(),
        ])
        if (!cancelled) {
          setReports(reportsRes.data)
          setPatients(patientsRes.data)
        }
      } catch (e) {
        if (!cancelled) setReports([])
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [accessToken])

  const handleTriggerAudit = async () => {
    if (!selectedPatientId) return
    setSubmitting(true)
    try {
      const { data: job } = await jobsApi.create({
        patient_id: selectedPatientId,
        export_type: "full",
        triggered_by: "ui",
      })
      setTriggerOpen(false)
      setSelectedPatientId("")
      navigate(`/audits/job/${job.id}`)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <BaseLayout title="Audits" description="Historical audit reports">
        <div className="flex items-center justify-center h-96">
          <LoadingSpinner />
        </div>
      </BaseLayout>
    )
  }

  return (
    <BaseLayout title="Audits" description="Historical audit reports and trigger new audits">
      <div className="@container/main px-4 lg:px-6 space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-semibold">Audit reports</h2>
          <Dialog open={triggerOpen} onOpenChange={setTriggerOpen}>
            <DialogTrigger asChild>
              <Button>Trigger audit</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Trigger audit</DialogTitle>
                <DialogDescription>Select a patient to run an AI audit. The job will run in the background.</DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label>Patient</Label>
                  <Select value={selectedPatientId} onValueChange={setSelectedPatientId}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select patient" />
                    </SelectTrigger>
                    <SelectContent>
                      {patients.map((p) => (
                        <SelectItem key={p.patient_id} value={p.patient_id}>
                          {p.patient_name ?? p.patient_id}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setTriggerOpen(false)}>Cancel</Button>
                <Button onClick={handleTriggerAudit} disabled={!selectedPatientId || submitting}>
                  {submitting ? "Submitting…" : "Submit"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Patient</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Risk</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="w-[80px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {reports.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                    No audit reports yet. Trigger an audit to get started.
                  </TableCell>
                </TableRow>
              ) : (
                reports.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell>{r.patient_id}</TableCell>
                    <TableCell>{r.status}</TableCell>
                    <TableCell>{r.risk_level ?? "—"}</TableCell>
                    <TableCell>{new Date(r.created_at).toLocaleString()}</TableCell>
                    <TableCell>
                      <Button variant="ghost" size="sm" onClick={() => navigate(`/audits/${r.id}`)}>
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>
    </BaseLayout>
  )
}
