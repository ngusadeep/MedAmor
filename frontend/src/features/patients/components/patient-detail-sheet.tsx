import { useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import { FileText, History } from 'lucide-react'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { getPatientBundle, listAuditReports } from '@/lib/jobs-api'
import type { Patient } from '../data/schema'

interface PatientDetailSheetProps {
  patient: Patient | null
  open: boolean
  onOpenChange: (open: boolean) => void
  defaultTab?: 'timeline' | 'audit-history'
}

export function PatientDetailSheet({
  patient,
  open,
  onOpenChange,
  defaultTab = 'timeline',
}: PatientDetailSheetProps) {
  const patientId = patient?.patient_id ?? ''

  const { data: bundle, isLoading: timelineLoading } = useQuery({
    queryKey: ['patient-bundle', patientId],
    queryFn: () => getPatientBundle(patientId),
    enabled: open && !!patientId,
  })

  const { data: reports = [], isLoading: historyLoading } = useQuery({
    queryKey: ['audit-reports', 'patient', patientId],
    queryFn: () => listAuditReports({ patient_id: patientId }),
    enabled: open && !!patientId,
  })

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side='right'
        className='w-full sm:max-w-xl flex flex-col'
      >
        <SheetHeader>
          <SheetTitle>
            {patient?.patient_name || patient?.patient_id || 'Patient'}
          </SheetTitle>
          <SheetDescription>
            {patient?.patient_id && (
              <span className='font-mono text-xs'>{patient.patient_id}</span>
            )}
          </SheetDescription>
        </SheetHeader>

        <Tabs defaultValue={defaultTab} className='flex-1 flex flex-col min-h-0'>
          <TabsList className='grid w-full grid-cols-2'>
            <TabsTrigger value='timeline' className='gap-2'>
              <FileText className='h-4 w-4' />
              Timeline
            </TabsTrigger>
            <TabsTrigger value='audit-history' className='gap-2'>
              <History className='h-4 w-4' />
              Audit History
            </TabsTrigger>
          </TabsList>

          <TabsContent value='timeline' className='flex-1 mt-4 min-h-0'>
            {timelineLoading ? (
              <div className='space-y-2'>
                <Skeleton className='h-4 w-full' />
                <Skeleton className='h-4 w-5/6' />
                <Skeleton className='h-4 w-4/5' />
              </div>
            ) : bundle ? (
              <ScrollArea className='h-[60vh] rounded-md border p-4'>
                <pre className='text-xs font-mono whitespace-pre-wrap break-words'>
                  {bundle.ehr_text || 'No timeline data available.'}
                </pre>
              </ScrollArea>
            ) : (
              <p className='text-sm text-muted-foreground'>
                No timeline data found for this patient.
              </p>
            )}
          </TabsContent>

          <TabsContent value='audit-history' className='flex-1 mt-4 min-h-0'>
            {historyLoading ? (
              <div className='space-y-2'>
                <Skeleton className='h-12 w-full' />
                <Skeleton className='h-12 w-full' />
              </div>
            ) : reports.length > 0 ? (
              <ScrollArea className='h-[60vh]'>
                <div className='space-y-2 pr-4'>
                  {reports
                    .sort(
                      (a, b) =>
                        new Date(b.created_at).getTime() -
                        new Date(a.created_at).getTime()
                    )
                    .map((r) => (
                      <Link
                        key={r.id}
                        to='/audits/reports/$reportId'
                        params={{ reportId: r.id }}
                        className='block rounded-lg border p-3 hover:bg-muted/50 transition-colors'
                        onClick={() => onOpenChange(false)}
                      >
                        <div className='flex items-center justify-between gap-2'>
                          <span className='text-sm font-medium'>
                            {new Date(r.created_at).toLocaleString()}
                          </span>
                          <Badge
                            variant={
                              r.status === 'FINDING_PRESENT'
                                ? 'destructive'
                                : 'secondary'
                            }
                          >
                            {r.status}
                          </Badge>
                        </div>
                        {r.risk_level && (
                          <p className='text-xs text-muted-foreground mt-1'>
                            Risk: {r.risk_level}
                          </p>
                        )}
                        {r.executive_summary && (
                          <p className='text-xs mt-1 line-clamp-2'>
                            {r.executive_summary}
                          </p>
                        )}
                      </Link>
                    ))}
                </div>
              </ScrollArea>
            ) : (
              <p className='text-sm text-muted-foreground'>
                No audit history for this patient.
              </p>
            )}
          </TabsContent>
        </Tabs>
      </SheetContent>
    </Sheet>
  )
}
