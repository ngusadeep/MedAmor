import { ColumnDef } from '@tanstack/react-table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  MoreHorizontal,
  Calendar,
  AlertTriangle,
  CheckCircle,
  Clock,
  FileText,
  History,
} from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import type { Patient } from '../data/schema'
import { riskLevels } from '../data/schema'

function getStatusBadge(status: string) {
  const statusConfig = {
    never_audited: { variant: 'secondary' as const, icon: Clock, label: 'Never Audited' },
    due_for_review: { variant: 'default' as const, icon: Calendar, label: 'Due for Review' },
    recently_audited: { variant: 'outline' as const, icon: CheckCircle, label: 'Recently Audited' },
    compliant: { variant: 'secondary' as const, icon: CheckCircle, label: 'Compliant' },
    needs_attention: { variant: 'destructive' as const, icon: AlertTriangle, label: 'Needs Attention' }
  }

  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.never_audited
  const Icon = config.icon

  return (
    <Badge variant={config.variant} className="flex items-center gap-1">
      <Icon className="h-3 w-3" />
      {config.label}
    </Badge>
  )
}

function getRiskBadge(riskLevel: string | null) {
  if (!riskLevel) return null

  const variants = {
    low: 'secondary' as const,
    medium: 'default' as const,
    high: 'destructive' as const
  }

  return (
    <Badge variant={variants[riskLevel as keyof typeof variants] || 'outline'}>
      {riskLevels[riskLevel as keyof typeof riskLevels] || riskLevel}
    </Badge>
  )
}

export function getPatientsColumns(
  onViewPatient: (patient: Patient, tab?: 'timeline' | 'audit-history') => void
): ColumnDef<Patient>[] {
  return [
  {
    accessorKey: 'patient_id',
    header: 'Patient ID',
    cell: ({ row }) => (
      <div className="font-mono text-sm">{row.original.patient_id}</div>
    ),
  },
  {
    accessorKey: 'patient_name',
    header: 'Patient Name',
    cell: ({ row }) => (
      <div className="font-medium">
        {row.original.patient_name || 'Unknown'}
      </div>
    ),
  },
  {
    accessorKey: 'status',
    header: 'Status',
    cell: ({ row }) => getStatusBadge(row.original.status),
  },
  {
    accessorKey: 'risk_level',
    header: 'Risk Level',
    cell: ({ row }) => getRiskBadge(row.original.risk_level),
  },
  {
    accessorKey: 'last_audit_date',
    header: 'Last Audit',
    cell: ({ row }) => (
      <div className="text-sm text-muted-foreground">
        {row.original.last_audit_date
          ? new Date(row.original.last_audit_date).toLocaleDateString()
          : 'Never'
        }
      </div>
    ),
  },
  {
    accessorKey: 'next_audit_date',
    header: 'Next Review',
    cell: ({ row }) => (
      <div className="text-sm text-muted-foreground">
        {row.original.next_audit_date
          ? new Date(row.original.next_audit_date).toLocaleDateString()
          : 'Not scheduled'
        }
      </div>
    ),
  },
  {
    id: 'actions',
    header: '',
    cell: ({ row }) => {
      const patient = row.original
      return (
        <div onClick={(e) => e.stopPropagation()}>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="h-8 w-8 p-0">
              <span className="sr-only">Open menu</span>
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => onViewPatient(patient, 'timeline')}>
              <FileText className="mr-2 h-4 w-4" />
              View Timeline
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => onViewPatient(patient, 'audit-history')}
            >
              <History className="mr-2 h-4 w-4" />
              Audit History
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
        </div>
      )
    },
  },
]
}