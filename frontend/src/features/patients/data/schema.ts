import type { PatientResponse, PatientStats } from '@/lib/jobs-api'

export type Patient = PatientResponse
export type PatientStatistics = PatientStats

export const patientStatuses = {
  never_audited: 'Never Audited',
  due_for_review: 'Due for Review',
  recently_audited: 'Recently Audited',
  compliant: 'Compliant',
  needs_attention: 'Needs Attention'
} as const

export const riskLevels = {
  low: 'Low',
  medium: 'Medium',
  high: 'High'
} as const