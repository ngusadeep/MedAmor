import { Routes, Route } from 'react-router-dom'
import { HomePage } from './pages/HomePage'
import { UsersPage } from './pages/UsersPage'

function App() {
  return (
    <div className="min-h-screen bg-background">
      <nav className="border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <a href="/" className="text-xl font-bold">
              Platform
            </a>
            <div className="flex gap-4">
              <a href="/" className="text-muted-foreground hover:text-foreground">
                Home
              </a>
              <a href="/users" className="text-muted-foreground hover:text-foreground">
                Users
              </a>
            </div>
          </div>
        </div>
      </nav>
      <main className="container mx-auto px-4 py-8">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/users" element={<UsersPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
