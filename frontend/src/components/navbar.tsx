import { Link } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'
import { Logo } from '@/components/logo'
import { NavMenu } from '@/components/nav-menu'
import { NavigationSheet } from '@/components/navigation-sheet'

const Navbar = () => {
  return (
    <nav className="fixed inset-x-4 top-6 z-50 mx-auto h-16 max-w-6xl rounded-full border bg-background/95 shadow-sm backdrop-blur">
      <div className="mx-auto flex h-full items-center justify-between px-4">
        <Logo />

        {/* Desktop Menu */}
        <NavMenu className="hidden md:block" />

        <div className="flex items-center gap-3">
          <Button
            className="hidden rounded-full sm:inline-flex"
            variant="outline"
            asChild
          >
            <Link to="/sign-in">Sign In</Link>
          </Button>
          <Button className="rounded-full" asChild>
            <Link to="/sign-up">Get Started</Link>
          </Button>

          {/* Mobile Menu */}
          <div className="md:hidden">
            <NavigationSheet />
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navbar
