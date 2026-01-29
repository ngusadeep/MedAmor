import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface User {
  id: number
  username: string
  email: string
  is_admin: boolean
}

interface DashboardPageProps {
  user: User
  onLogout: () => void
}

export function DashboardPage({ user, onLogout }: DashboardPageProps) {
  return (
    <div className="min-h-screen flex flex-col">
      <nav className="border-b border-border">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <span className="text-xl font-bold">MedArmor</span>
          <Button variant="outline" onClick={onLogout}>
            Sign Out
          </Button>
        </div>
      </nav>
      <main className="flex-1 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">
              Welcome, {user.username}
            </CardTitle>
            <CardDescription>
              You are signed in as {user.email}
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center text-muted-foreground">
            {user.is_admin && (
              <p className="text-sm">You have administrator privileges.</p>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
