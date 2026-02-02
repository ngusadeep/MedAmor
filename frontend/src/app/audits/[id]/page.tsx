"use client"

import { useEffect, useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { BaseLayout } from "@/components/layouts/base-layout"
import { Button } from "@/components/ui/button"
import { auditReportsApi } from "@/lib/api"
import { AuditDetail } from "../components/audit-detail"
import { LoadingSpinner } from "@/components/ui/loading-spinner"

export default function AuditDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [report, setReport] = useState<Awaited<ReturnType<typeof auditReportsApi.get>>["data"] | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    auditReportsApi
      .get(id)
      .then((r) => setReport(r.data))
      .catch(() => setReport(null))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return (
      <BaseLayout title="Audit report">
        <div className="flex items-center justify-center h-96">
          <LoadingSpinner />
        </div>
      </BaseLayout>
    )
  }

  if (!report) {
    return (
      <BaseLayout title="Not found">
        <div className="px-4 py-8 text-center">
          <p className="text-muted-foreground">Report not found.</p>
          <Button variant="link" onClick={() => navigate("/audits")}>Back to audits</Button>
        </div>
      </BaseLayout>
    )
  }

  return (
    <BaseLayout title="Audit report">
      <div className="@container/main px-4 lg:px-6 space-y-6">
        <Button variant="ghost" onClick={() => navigate("/audits")}>← Back to audits</Button>
        <AuditDetail report={report} />
      </div>
    </BaseLayout>
  )
}
