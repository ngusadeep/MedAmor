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
  sensitivity?: number | null
  model?: string | null
  extraction_mode?: string | null
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
  sensitivity?: number | null // 0.0–1.0; Low=0.2, Medium=0.5, High=0.8
  model?: string | null // medgemma_hf | medgemma_vertex | gemini | openai
  extraction_mode?: string | null // one_pass | gemini_extract | medgemma_extract
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
  sensitivity?: number | null
  model?: string | null
  extraction_mode?: string | null
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

// Patient management API
export interface PatientResponse {
  id: string
  patient_id: string
  patient_name: string | null
  status: string
  last_audit_date: string | null
  next_audit_date: string | null
  risk_level: string | null
  created_at: string
  updated_at: string
}

export interface PatientStats {
  total_patients: number
  status_counts: Record<string, number>
  due_for_review_count: number
}

export function listPatients(params?: {
  status?: string
}): Promise<PatientResponse[]> {
  const search = new URLSearchParams()
  if (params?.status) search.set('status', params.status)
  const qs = search.toString()
  return apiGet<PatientResponse[]>(`/patients${qs ? `?${qs}` : ''}`)
}

export function getPatientStats(): Promise<PatientStats> {
  return apiGet<PatientStats>('/patients/stats')
}

export function syncPatients(): Promise<{ message: string }> {
  return apiPost<{ message: string }>('/patients/sync', {})
}

export function updatePatientStatus(): Promise<{ updated_patients: number }> {
  return apiPost<{ updated_patients: number }>('/patients/update-status', {})
}

export function listPatientsDueForReview(): Promise<PatientResponse[]> {
  return apiGet<PatientResponse[]>('/patients/due-for-review')
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
