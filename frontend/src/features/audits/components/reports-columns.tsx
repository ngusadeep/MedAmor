import { type ColumnDef } from '@tanstack/react-table'
import { Link } from '@tanstack/react-router'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { DataTableColumnHeader } from '@/components/data-table'
import { Eye } from 'lucide-react'
import type { AuditReport } from '../data/schema'

const statusVariant = (
  status: string
): 'default' | 'secondary' | 'destructive' | 'outline' => {
  if (status === 'NO_FINDINGS') return 'default'
  if (status === 'FINDING_PRESENT') return 'destructive'
  return 'secondary'
}

export const reportsColumns: ColumnDef<AuditReport>[] = [
  {
    accessorKey: 'id',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Report ID' />
    ),
    cell: ({ row }) => (
      <span className='font-mono text-xs'>
        {String(row.getValue('id')).slice(0, 8)}…
      </span>
    ),
    enableSorting: true,
  },
  {
    accessorKey: 'job_id',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Job ID' />
    ),
    cell: ({ row }) => (
      <span className='font-mono text-xs'>
        {String(row.getValue('job_id')).slice(0, 8)}…
      </span>
    ),
    enableSorting: true,
  },
  {
    accessorKey: 'patient_id',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Patient ID' />
    ),
    cell: ({ row }) => (
      <span className='font-medium'>{row.getValue('patient_id')}</span>
    ),
    enableSorting: true,
  },
  {
    accessorKey: 'status',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Status' />
    ),
    cell: ({ row }) => {
      const status = row.getValue('status') as string
      const label =
        status === 'NO_FINDINGS' ? 'No findings' : 'Findings present'
      return (
        <Badge variant={statusVariant(status)}>{label}</Badge>
      )
    },
    filterFn: (row, id, value) => value.includes(row.getValue(id)),
  },
  {
    accessorKey: 'risk_level',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Risk' />
    ),
    cell: ({ row }) => (
      <span className='text-muted-foreground'>
        {row.getValue('risk_level') ?? '—'}
      </span>
    ),
  },
  {
    accessorKey: 'created_at',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Created' />
    ),
    cell: ({ row }) => {
      const val = row.getValue('created_at') as string
      return (
        <span className='text-muted-foreground'>
          {new Date(val).toLocaleString()}
        </span>
      )
    },
    enableSorting: true,
  },
  {
    id: 'actions',
    cell: ({ row }) => {
      const report = row.original
      return (
        <Button variant='ghost' size='sm' asChild>
          <Link
            to='/audits/reports/$reportId'
            params={{ reportId: report.id }}
            className='gap-1'
          >
            <Eye className='h-4 w-4' />
            View
          </Link>
        </Button>
      )
    },
  },
]
