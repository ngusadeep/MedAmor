"use client"

import { useEffect, useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { BaseLayout } from "@/components/layouts/base-layout"
import { Button } from "@/components/ui/button"
import { jobsApi, auditReportsApi } from "@/lib/api"
import { AuditDetail } from "../../components/audit-detail"
import { LoadingSpinner } from "@/components/ui/loading-spinner"

const POLL_INTERVAL_MS = 2000

export default function JobStatusPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const navigate = useNavigate()
  const [job, setJob] = useState<Awaited<ReturnType<typeof jobsApi.get>>["data"] | null>(null)
  const [report, setReport] = useState<Awaited<ReturnType<typeof auditReportsApi.getByJob>>["data"] | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!jobId) return
    let cancelled = false
    async function poll() {
      try {
        const [jobRes, reportRes] = await Promise.all([
          jobsApi.get(jobId),
          auditReportsApi.getByJob(jobId),
        ])
        if (cancelled) return
        setJob(jobRes.data)
        setReport(reportRes.data ?? null)
        if (jobRes.data.status === "completed" && reportRes.data) {
          return
        }
        if (jobRes.data.status === "failed") return
      } catch {
        if (!cancelled) setJob(null)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    poll()
    const id = setInterval(poll, POLL_INTERVAL_MS)
    return () => {
      cancelled = true
      clearInterval(id)
    }
  }, [jobId])

  if (loading && !job) {
    return (
      <BaseLayout title="Job status">
        <div className="flex items-center justify-center h-96">
          <LoadingSpinner />
        </div>
      </BaseLayout>
    )
  }

  if (!job) {
    return (
      <BaseLayout title="Not found">
        <div className="px-4 py-8 text-center">
          <p className="text-muted-foreground">Job not found.</p>
          <Button variant="link" onClick={() => navigate("/audits")}>Back to audits</Button>
        </div>
      </BaseLayout>
    )
  }

  const done = job.status === "completed" || job.status === "failed"

  return (
    <BaseLayout title="Audit job">
      <div className="@container/main px-4 lg:px-6 space-y-6">
        <Button variant="ghost" onClick={() => navigate("/audits")}>← Back to audits</Button>
        <div className="rounded-lg border p-4">
          <p className="font-medium">Job {job.id}</p>
          <p className="text-sm text-muted-foreground">
            Patient: {job.patient_id} · Status: {job.status}
          </p>
          {job.error_message && (
            <p className="text-sm text-destructive mt-2">{job.error_message}</p>
          )}
        </div>
        {!done && (
          <div className="flex items-center gap-2 text-muted-foreground">
            <LoadingSpinner className="h-4 w-4" />
            <span>Running audit…</span>
          </div>
        )}
        {report && (
          <>
            <Button onClick={() => navigate(`/audits/${report.id}`)}>View report</Button>
            <AuditDetail report={report} />
          </>
        )}
      </div>
    </BaseLayout>
  )
}
