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
    accessorKey: 'status',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Status' />
    ),
    cell: ({ row }) => {
      const status = row.getValue('status') as string
      return (
        <Badge variant={statusVariant(status)} className='capitalize'>
          {status}
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
            to='/audits/jobs/$jobId'
            params={{ jobId: job.id }}
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
