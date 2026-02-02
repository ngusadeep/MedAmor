"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { AuditReport } from "@/lib/api"

export function AuditDetail({ report }: { report: AuditReport }) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Audit report</CardTitle>
            <div className="flex gap-2">
              <Badge variant={report.status === "FINDING_PRESENT" ? "destructive" : "secondary"}>
                {report.status}
              </Badge>
              {report.risk_level && (
                <Badge variant="outline">{report.risk_level}</Badge>
              )}
            </div>
          </div>
          <p className="text-sm text-muted-foreground">
            Patient: {report.patient_id} · {new Date(report.created_at).toLocaleString()}
          </p>
        </CardHeader>
        <CardContent>
          {report.executive_summary && (
            <div className="mb-4">
              <h3 className="text-sm font-medium mb-1">Executive summary</h3>
              <p className="text-sm text-muted-foreground">{report.executive_summary}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {report.findings && report.findings.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Findings</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3">
              {report.findings.map((f, i) => (
                <li key={i} className="border-l-2 border-muted pl-3">
                  <p className="font-medium">{f.category}</p>
                  <p className="text-sm text-muted-foreground">{f.description}</p>
                  {(f.responsible_doctor || f.urgency) && (
                    <p className="text-xs mt-1">
                      {f.responsible_doctor && `Responsible: ${f.responsible_doctor}`}
                      {f.urgency && ` · Urgency: ${f.urgency}`}
                    </p>
                  )}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {report.evidence && report.evidence.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Evidence</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              {report.evidence.map((e, i) => (
                <li key={i} className="text-muted-foreground">
                  {e.kb_source && <span className="text-muted-foreground">KB: {e.kb_source}</span>}
                  {e.ehr_snippet && (
                    <p className="mt-1 bg-muted/50 p-2 rounded text-xs font-mono truncate max-w-full">
                      {e.ehr_snippet}
                    </p>
                  )}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {report.corrective_actions && report.corrective_actions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Corrective actions</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc list-inside space-y-1 text-sm">
              {report.corrective_actions.map((a, i) => (
                <li key={i}>{a}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
