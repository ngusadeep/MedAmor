import { createFileRoute } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

// Route id; routeTree.gen.ts will include this after dev/build
export const Route = createFileRoute('/_authenticated/audits/reports/' as any)({
  component: AuditsReportsPage,
})

function AuditsReportsPage() {
  return (
    <div className='space-y-4'>
      <h1 className='text-2xl font-bold tracking-tight'>Audit Reports</h1>
      <Card>
        <CardHeader>
          <CardTitle>Reports</CardTitle>
        </CardHeader>
        <CardContent>
          <p className='text-muted-foreground'>
            View completed audit reports: findings, evidence, and corrective
            actions.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
