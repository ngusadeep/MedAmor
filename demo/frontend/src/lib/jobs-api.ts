/**
 * Jobs and audit reports API for MedAudit dashboard.
 */

import { apiGet, apiPost } from './api'

export interface JobResponse {
  id: string
  patient_id: string
  audit_type: string
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
  audit_type?: string | null // default: breast_cancer_screening
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

export interface JobCreateBatch {
  patient_ids: string[]
  audit_type?: string | null
  export_type?: string | null
  triggered_by?: string | null
}

export function createJobsBatch(body: JobCreateBatch): Promise<JobResponse[]> {
  return apiPost<JobResponse[]>('/jobs/batch', body)
}

export interface EHRPatientSummary {
  patient_id: string
  patient_name: string | null
  export_types: string[]
}

export function listEHRPatients(): Promise<EHRPatientSummary[]> {
  return apiGet<EHRPatientSummary[]>('/ehr/patients')
}

export interface ReportAnnotationResponse {
  id: string
  audit_report_id: string
  finding_index: number
  note: string
  created_by_user_id: string | null
  created_at: string
}

export function listReportAnnotations(reportId: string): Promise<ReportAnnotationResponse[]> {
  return apiGet<ReportAnnotationResponse[]>(`/audit-reports/${reportId}/annotations`)
}

export function createReportAnnotation(
  reportId: string,
  body: { finding_index: number; note: string }
): Promise<ReportAnnotationResponse> {
  return apiPost<ReportAnnotationResponse>(`/audit-reports/${reportId}/annotations`, body)
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

/** Get audit report for a job (if completed). Returns null if none. */
export async function getAuditReportByJob(
  jobId: string
): Promise<AuditReportResponse | null> {
  const base = import.meta.env.VITE_API_URL?.replace(/\/$/, '') ?? '/api'
  const res = await fetch(`${base}/audit-reports/by-job/${jobId}`, {
    credentials: 'include',
  })
  if (res.status === 404) return null
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error((data as { detail?: string }).detail ?? 'Request failed')
  }
  return res.json() as Promise<AuditReportResponse | null>
}
