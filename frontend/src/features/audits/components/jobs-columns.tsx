import { type ColumnDef } from '@tanstack/react-table'
import { Link } from '@tanstack/react-router'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { DataTableColumnHeader } from '@/components/data-table'
import { Eye } from 'lucide-react'
import type { Job } from '../data/schema'

const statusVariant = (
  status: string
): 'default' | 'secondary' | 'destructive' | 'outline' => {
  if (status === 'completed') return 'default'
  if (status === 'failed') return 'destructive'
  return 'secondary'
}

export const jobsColumns: ColumnDef<Job>[] = [
  {
    accessorKey: 'id',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Job ID' />
    ),
    cell: ({ row }) => (
      <span className='font-mono text-xs'>
        {String(row.getValue('id')).slice(0, 8)}…
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
    accessorKey: 'audit_type',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Audit type' />
    ),
    cell: ({ row }) => {
      const v = row.getValue('audit_type') as string
      return (
        <span className='text-muted-foreground text-xs'>
          {v === 'breast_cancer_screening' ? 'Breast cancer screening' : v}
        </span>
      )
    },
    enableSorting: true,
  },
  {
    accessorKey: 'sensitivity',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Sensitivity' />
    ),
    cell: ({ row }) => {
      const val = row.getValue('sensitivity') as number | null | undefined
      if (val == null) return <span className='text-muted-foreground text-xs'>—</span>
      const preset =
        val <= 0.3 ? 'Low' : val <= 0.6 ? 'Medium' : val <= 1 ? 'High' : String(val)
      return (
        <span className='text-muted-foreground text-xs'>
          {preset} ({val})
        </span>
      )
    },
    enableSorting: true,
  },
  {
    accessorKey: 'status',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Status' />
    ),
    cell: ({ row }) => {
      const status = (row.getValue('status') as string) ?? ''
      const normalized = status.toLowerCase()
      const label =
        normalized === 'in_progress'
          ? 'In progress'
          : normalized === 'pending'
            ? 'Pending'
            : normalized === 'completed'
              ? 'Completed'
              : normalized === 'failed' || normalized === 'fail'
                ? 'Failed'
                : status || 'Unknown'
      const variantStatus = normalized === 'fail' ? 'failed' : normalized
      return (
        <Badge variant={statusVariant(variantStatus)} className='capitalize'>
          {label}
        </Badge>
      )
    },
    filterFn: (row, id, value) => value.includes(row.getValue(id)),
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
      const job = row.original
      return (
        <Button variant='ghost' size='sm' asChild>
          <Link
            to={'/audits/jobs/$jobId' as any}
            params={{ jobId: job.id } as any}
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
