import { createFileRoute } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

// Route id; routeTree.gen.ts will include this after dev/build
export const Route = createFileRoute('/_authenticated/audits/jobs/' as any)({
  component: AuditsJobsPage,
})

function AuditsJobsPage() {
  return (
    <div className='space-y-4'>
      <h1 className='text-2xl font-bold tracking-tight'>Audit Jobs</h1>
      <Card>
        <CardHeader>
          <CardTitle>Jobs</CardTitle>
        </CardHeader>
        <CardContent>
          <p className='text-muted-foreground'>
            List and manage audit jobs. Create a job for a patient to run an EHR
            audit.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
