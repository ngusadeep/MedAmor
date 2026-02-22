import { useQuery, useQueryClient } from '@tanstack/react-query'
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
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { createJob, createJobsBatch, listEHRPatients } from '@/lib/jobs-api'
import { useJobs } from './jobs-provider'

const MODEL_OPTIONS = [
  { value: 'default', label: 'Default (from server)' },
  { value: 'medgemma_hf', label: 'MedGemma (Hugging Face)' },
  { value: 'medgemma_vertex', label: 'MedGemma (Vertex AI)' },
  { value: 'gemini', label: 'Gemini' },
  { value: 'openai', label: 'OpenAI' },
] as const

const EXTRACTION_MODE_OPTIONS = [
  { value: 'default', label: 'Default (from server)' },
  { value: 'one_pass', label: 'One pass' },
  { value: 'gemini_extract', label: 'Two pass (Gemini extract)' },
  { value: 'medgemma_extract', label: 'Two pass (MedGemma extract)' },
] as const

const SENSITIVITY_PRESETS = [
  { value: '0.2', label: 'Low', desc: 'Only high-confidence findings' },
  { value: '0.5', label: 'Medium', desc: 'Balanced (default)' },
  { value: '0.8', label: 'High', desc: 'Surface more findings' },
] as const

export function CreateJobDialog() {
  const queryClient = useQueryClient()
  const { open, setOpen, onSuccess } = useJobs()
  const [patientId, setPatientId] = useState('')
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [sensitivity, setSensitivity] = useState<string>('0.5')
  const [model, setModel] = useState<string>('default')
  const [extractionMode, setExtractionMode] = useState<string>('default')
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
        await createJobsBatch({
          patient_ids: batchIds,
          sensitivity: parseFloat(sensitivity),
          model: model === 'default' ? undefined : model,
          extraction_mode: extractionMode === 'default' ? undefined : extractionMode,
        })
        setSelectedIds(new Set())
        setPatientId('')
        setOpen(false)
        await queryClient.invalidateQueries({ queryKey: ['jobs'] })
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
      await createJob({
        patient_id: singleId,
        sensitivity: parseFloat(sensitivity),
        model: model || undefined,
        extraction_mode: extractionMode || undefined,
      })
      setPatientId('')
      setOpen(false)
      await queryClient.invalidateQueries({ queryKey: ['jobs'] })
      onSuccess?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create job')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => setOpen(v)}>
      <DialogContent className='sm:max-w-[520px]'>
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
              <Label>Sensitivity</Label>
              <RadioGroup
                value={sensitivity}
                onValueChange={setSensitivity}
                className='grid grid-cols-3 gap-2'
                aria-describedby='sensitivity-desc'
              >
                {SENSITIVITY_PRESETS.map((p) => (
                  <div
                    key={p.value}
                    className='flex items-center space-x-2 rounded border px-3 py-2 has-[[data-state=checked]]:border-primary has-[[data-state=checked]]:bg-primary/5'
                  >
                    <RadioGroupItem value={p.value} id={`sens-${p.value}`} />
                    <label
                      htmlFor={`sens-${p.value}`}
                      className='flex flex-col cursor-pointer text-sm'
                    >
                      <span className='font-medium'>{p.label}</span>
                      <span className='text-muted-foreground text-xs'>{p.desc}</span>
                    </label>
                  </div>
                ))}
              </RadioGroup>
              <p id='sensitivity-desc' className='text-muted-foreground text-xs'>
                Lower = fewer findings (only high-confidence). Higher = more findings.
              </p>
            </div>
            <div className='grid gap-2'>
              <Label htmlFor='model'>Model</Label>
              <Select value={model} onValueChange={setModel}>
                <SelectTrigger id='model' className='w-full'>
                  <SelectValue placeholder='Default (from server)' />
                </SelectTrigger>
                <SelectContent>
                  {MODEL_OPTIONS.map((o) => (
                    <SelectItem key={o.value} value={o.value}>
                      {o.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className='grid gap-2'>
              <Label htmlFor='extraction_mode'>Extraction mode</Label>
              <Select value={extractionMode} onValueChange={setExtractionMode}>
                <SelectTrigger id='extraction_mode' className='w-full'>
                  <SelectValue placeholder='Default (from server)' />
                </SelectTrigger>
                <SelectContent>
                  {EXTRACTION_MODE_OPTIONS.map((o) => (
                    <SelectItem key={o.value} value={o.value}>
                      {o.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className='text-muted-foreground text-xs'>
                One pass = single audit step. Two pass = extract EHR summary first, then audit.
              </p>
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
