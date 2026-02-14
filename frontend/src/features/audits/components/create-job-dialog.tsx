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
import { createJob } from '@/lib/jobs-api'
import { useJobs } from './jobs-provider'

export function CreateJobDialog() {
  const { open, setOpen, onSuccess } = useJobs()
  const [patientId, setPatientId] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    const id = patientId.trim()
    if (!id) {
      setError('Patient ID is required')
      return
    }
    setLoading(true)
    try {
      await createJob({ patient_id: id })
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
      <DialogContent className='sm:max-w-[425px]'>
        <DialogHeader>
          <DialogTitle>New audit job</DialogTitle>
          <DialogDescription>
            Enter a patient ID to run an EHR audit. The job will be queued and
            processed.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className='grid gap-4 py-4'>
            <div className='grid gap-2'>
              <Label htmlFor='patient_id'>Patient ID</Label>
              <Input
                id='patient_id'
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                placeholder='e.g. 51674'
                disabled={loading}
              />
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
              {loading ? 'Creating…' : 'Create job'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
