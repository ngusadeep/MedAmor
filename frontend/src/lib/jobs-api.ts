/**
 * Jobs and audit reports API for MedAudit dashboard.
 */

import { apiGet, apiPost } from './api'

export interface JobResponse {
  id: string
  patient_id: string
  status: string
  triggered_by: string | null
  export_type: string | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface AuditReportResponse {
  id: string
  job_id: string
  patient_id: string
  status: string
  risk_level: string | null
  executive_summary: string | null
  findings: unknown[] | null
  evidence: unknown[] | null
  corrective_actions: string[] | null
  next_audit_date: string | null
  created_at: string
}

export interface JobCreate {
  patient_id: string
  export_type?: string | null
  triggered_by?: string | null
}

export function listJobs(params?: {
  patient_id?: string
  status?: string
}): Promise<JobResponse[]> {
  const search = new URLSearchParams()
  if (params?.patient_id) search.set('patient_id', params.patient_id)
  if (params?.status) search.set('status', params.status)
  const qs = search.toString()
  return apiGet<JobResponse[]>(`/jobs${qs ? `?${qs}` : ''}`)
}

export function getJob(jobId: string): Promise<JobResponse> {
  return apiGet<JobResponse>(`/jobs/${jobId}`)
}

export function createJob(body: JobCreate): Promise<JobResponse> {
  return apiPost<JobResponse>('/jobs', body)
}

export function listAuditReports(params?: {
  job_id?: string
  patient_id?: string
}): Promise<AuditReportResponse[]> {
  const search = new URLSearchParams()
  if (params?.job_id) search.set('job_id', params.job_id)
  if (params?.patient_id) search.set('patient_id', params.patient_id)
  const qs = search.toString()
  return apiGet<AuditReportResponse[]>(`/audit-reports${qs ? `?${qs}` : ''}`)
}

export function getAuditReport(reportId: string): Promise<AuditReportResponse> {
  return apiGet<AuditReportResponse>(`/audit-reports/${reportId}`)
}
