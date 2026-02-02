import axios from 'axios'

const baseURL = import.meta.env.VITE_API_URL ?? '/api'

export const api = axios.create({
  baseURL,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})

function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null
  const t = localStorage.getItem('access_token')
  if (t) return t
  try {
    const raw = localStorage.getItem('medaudit-auth')
    if (raw) {
      const j = JSON.parse(raw) as { state?: { accessToken?: string } }
      if (j.state?.accessToken) return j.state.accessToken
    }
  } catch { /* ignore */ }
  return null
}

api.interceptors.request.use((config) => {
  const token = getStoredToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      if (typeof window !== 'undefined') localStorage.removeItem('access_token')
    }
    return Promise.reject(err)
  }
)

export type Job = {
  id: string
  patient_id: string
  status: string
  triggered_by: string | null
  export_type: string | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export type AuditReport = {
  id: string
  job_id: string
  patient_id: string
  status: string
  risk_level: string | null
  executive_summary: string | null
  findings: Array<{ category: string; description: string; responsible_doctor?: string; urgency?: string }> | null
  evidence: Array<{ kb_source?: string; ehr_snippet?: string; image_ref?: string }> | null
  corrective_actions: string[] | null
  next_audit_date: string | null
  created_at: string
}

export type EHRPatientSummary = { patient_id: string; patient_name: string | null; export_types: string[] }

export const authApi = {
  login: (username: string, password: string) =>
    api.post<{ access_token: string; token_type: string }>('/auth/login', { username, password }),
  logout: () => api.post('/auth/logout'),
  me: () => api.get<{ id: string; username: string }>('/auth/me'),
}

export const jobsApi = {
  list: (params?: { patient_id?: string; status?: string }) => api.get<Job[]>('/jobs', { params }),
  get: (id: string) => api.get<Job>(`/jobs/${id}`),
  create: (body: { patient_id: string; export_type?: string; triggered_by?: string }) =>
    api.post<Job>('/jobs', body),
}

export const auditReportsApi = {
  list: (params?: { job_id?: string; patient_id?: string }) =>
    api.get<AuditReport[]>('/audit-reports', { params }),
  get: (id: string) => api.get<AuditReport>(`/audit-reports/${id}`),
  getByJob: (jobId: string) => api.get<AuditReport | null>(`/audit-reports/by-job/${jobId}`),
}

export const ehrApi = {
  listPatients: () => api.get<EHRPatientSummary[]>('/ehr/patients'),
}
