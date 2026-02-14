import { ClipboardList } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useJobs } from './jobs-provider'

export function JobsPrimaryButtons() {
  const { setOpen } = useJobs()
  return (
    <Button className='gap-1' onClick={() => setOpen(true)}>
      <ClipboardList className='h-4 w-4' />
      New audit job
    </Button>
  )
}
