import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Users, AlertTriangle, Calendar, Clock } from 'lucide-react'
import type { PatientStatistics } from '../data/schema'

interface PatientStatsProps {
  stats: PatientStatistics
  isLoading?: boolean
}

export function PatientStats({ stats, isLoading }: PatientStatsProps) {
  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Loading...</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-8 bg-muted animate-pulse rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  const statCards = [
    {
      title: 'Total Patients',
      value: stats.total_patients,
      icon: Users,
      description: 'All active patients',
      color: 'text-blue-600',
    },
    {
      title: 'Due for Review',
      value: stats.due_for_review_count,
      icon: Calendar,
      description: 'Need immediate attention',
      color: 'text-orange-600',
    },
    {
      title: 'Needs Attention',
      value: stats.status_counts.needs_attention || 0,
      icon: AlertTriangle,
      description: 'High-risk findings',
      color: 'text-red-600',
    },
    {
      title: 'Never Audited',
      value: stats.status_counts.never_audited || 0,
      icon: Clock,
      description: 'First-time audits needed',
      color: 'text-gray-600',
    },
  ]

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat) => {
          const Icon = stat.icon
          return (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
                <Icon className={`h-4 w-4 ${stat.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className="text-xs text-muted-foreground">{stat.description}</p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Status Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Patient Status Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {Object.entries(stats.status_counts).map(([status, count]) => {
              const statusLabels = {
                never_audited: 'Never Audited',
                due_for_review: 'Due for Review',
                recently_audited: 'Recently Audited',
                compliant: 'Compliant',
                needs_attention: 'Needs Attention',
              }

              const statusColors = {
                never_audited: 'bg-gray-100 text-gray-800',
                due_for_review: 'bg-blue-100 text-blue-800',
                recently_audited: 'bg-green-100 text-green-800',
                compliant: 'bg-green-100 text-green-800',
                needs_attention: 'bg-red-100 text-red-800',
              }

              return (
                <div key={status} className="flex items-center justify-between p-3 rounded-lg border">
                  <div className="flex items-center space-x-2">
                    <Badge
                      variant="secondary"
                      className={statusColors[status as keyof typeof statusColors]}
                    >
                      {statusLabels[status as keyof typeof statusLabels]}
                    </Badge>
                  </div>
                  <div className="text-2xl font-bold">{count}</div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}