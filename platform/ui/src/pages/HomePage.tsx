import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export function HomePage() {
  const [health, setHealth] = useState<{ status: string } | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/health')
      .then((res) => res.json())
      .then(setHealth)
      .catch((err) => setError(err.message))
  }, [])

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Welcome to Platform</h1>
        <p className="text-muted-foreground mt-2">
          A modern web application built with Flask, React, and PostgreSQL.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>API Status</CardTitle>
            <CardDescription>Backend health check</CardDescription>
          </CardHeader>
          <CardContent>
            {error ? (
              <p className="text-destructive">Error: {error}</p>
            ) : health ? (
              <p className="text-green-600 font-medium">
                Status: {health.status}
              </p>
            ) : (
              <p className="text-muted-foreground">Loading...</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>User Management</CardTitle>
            <CardDescription>Manage platform users</CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild>
              <a href="/users">View Users</a>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Documentation</CardTitle>
            <CardDescription>Learn about the platform</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Check the README for setup and development instructions.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
