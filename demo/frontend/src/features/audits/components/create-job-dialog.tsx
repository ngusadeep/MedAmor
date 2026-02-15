import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { createJob, createJobsBatch, listEHRPatients } from '@/lib/jobs-api'
import { useJobs } from './jobs-provider'

export function CreateJobDialog() {
  const { open, setOpen, onSuccess } = useJobs()
  const [patientId, setPatientId] = useState('')
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const { data: patients = [] } = useQuery({
    queryKey: ['ehr-patients'],
    queryFn: () => listEHRPatients(),
    enabled: open,
  })

  const togglePatient = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    const singleId = patientId.trim()
    const batchIds = Array.from(selectedIds).filter(Boolean)
    if (batchIds.length > 0) {
      setLoading(true)
      try {
        await createJobsBatch({ patient_ids: batchIds })
        setSelectedIds(new Set())
        setPatientId('')
        setOpen(false)
        onSuccess?.()
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to create jobs')
      } finally {
        setLoading(false)
      }
      return
    }
    if (!singleId) {
      setError('Enter a patient ID or select one or more patients from the list')
      return
    }
    setLoading(true)
    try {
      await createJob({ patient_id: singleId })
      setPatientId('')
      setOpen(false)
      onSuccess?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create job')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => setOpen(v)}>
      <DialogContent className='sm:max-w-[500px]'>
        <DialogHeader>
          <DialogTitle>New breast cancer screening audit</DialogTitle>
          <DialogDescription>
            Enter a patient ID or select one or more patients to run audits. Jobs will be queued.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className='grid gap-4 py-4'>
            <div className='grid gap-2'>
              <Label htmlFor='patient_id'>Patient ID (single)</Label>
              <Input
                id='patient_id'
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                placeholder='e.g. 2f9df1ec-139f-b7ef-1e20-e0b5a1c3d39f'
                disabled={loading}
              />
            </div>
            <div className='grid gap-2'>
              <Label>Or select patients (batch)</Label>
              <div className='max-h-48 overflow-y-auto rounded border p-2 space-y-2'>
                {patients.length === 0 && (
                  <p className='text-muted-foreground text-sm'>No patients loaded. Enter ID above.</p>
                )}
                {patients.slice(0, 100).map((p) => (
                  <div key={p.patient_id} className='flex items-center gap-2'>
                    <Checkbox
                      id={`pat-${p.patient_id}`}
                      checked={selectedIds.has(p.patient_id)}
                      onCheckedChange={() => togglePatient(p.patient_id)}
                    />
                    <label
                      htmlFor={`pat-${p.patient_id}`}
                      className='text-sm cursor-pointer font-mono'
                    >
                      {p.patient_id}
                      {p.patient_name ? ` (${p.patient_name})` : ''}
                    </label>
                  </div>
                ))}
                {patients.length > 100 && (
                  <p className='text-muted-foreground text-xs'>Showing first 100. Use ID for others.</p>
                )}
              </div>
            </div>
            {error && (
              <p className='text-sm text-destructive' role='alert'>
                {error}
              </p>
            )}
          </div>
          <DialogFooter>
            <Button
              type='button'
              variant='outline'
              onClick={() => setOpen(false)}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button type='submit' disabled={loading}>
              {loading ? 'Creating…' : selectedIds.size > 0 ? `Create ${selectedIds.size} jobs` : 'Create job'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
