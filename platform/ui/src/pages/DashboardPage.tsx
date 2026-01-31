import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'

interface User {
  id: number
  username: string
  email: string
  is_admin: boolean
}

interface Report {
  id: number
  patient_id: string
  date_of_finding: string
  status: 'OPEN' | 'INVESTIGATING' | 'CLOSED'
  finding_type: 'IMAGING' | 'HANDOFF'
  created_at: string
  updated_at: string
}

interface DashboardPageProps {
  user: User
  onLogout: () => void
}

function getStatusBadgeVariant(status: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (status) {
    case 'OPEN':
      return 'destructive'
    case 'INVESTIGATING':
      return 'default'
    case 'CLOSED':
      return 'secondary'
    default:
      return 'outline'
  }
}

function getTypeBadgeVariant(type: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (type) {
    case 'IMAGING':
      return 'outline'
    case 'HANDOFF':
      return 'secondary'
    default:
      return 'outline'
  }
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString()
}

export function DashboardPage({ user, onLogout }: DashboardPageProps) {
  const [reports, setReports] = useState<Report[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/reports')
      .then((res) => {
        if (!res.ok) throw new Error('Failed to fetch reports')
        return res.json()
      })
      .then((data) => {
        setReports(data)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  return (
    <div className="min-h-screen flex flex-col">
      <nav className="border-b border-border">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <span className="text-xl font-bold">MedArmor</span>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">
              Welcome, {user.username}
            </span>
            <Button variant="outline" onClick={onLogout}>
              Sign Out
            </Button>
          </div>
        </div>
      </nav>
      <main className="flex-1 container mx-auto px-4 py-8">
        <Card>
          <CardHeader>
            <CardTitle>Findings</CardTitle>
            <CardDescription>
              All findings in the system
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-muted-foreground">Loading reports...</p>
            ) : error ? (
              <p className="text-destructive">Error: {error}</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Patient ID</TableHead>
                    <TableHead>Date of Finding</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Type</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {reports.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center text-muted-foreground">
                        No findings found.
                      </TableCell>
                    </TableRow>
                  ) : (
                    reports.map((report) => (
                      <TableRow key={report.id}>
                        <TableCell>{report.id}</TableCell>
                        <TableCell className="font-medium">{report.patient_id}</TableCell>
                        <TableCell>{formatDate(report.date_of_finding)}</TableCell>
                        <TableCell>
                          <Badge variant={getStatusBadgeVariant(report.status)}>
                            {report.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={getTypeBadgeVariant(report.finding_type)}>
                            {report.finding_type}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
