import { Link } from '@tanstack/react-router'
import { Github, Twitter, Linkedin, Mail } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'

const footerSections = [
  {
    title: 'Product',
    links: [
      { title: 'Overview', to: '/' },
      { title: 'Features', to: '/', hash: '#features' },
      { title: 'Audits & reports', to: '/sign-in' },
      { title: 'Patients', to: '/sign-in' },
    ],
  },
  {
    title: 'Resources',
    links: [
      { title: 'Sign in', to: '/sign-in' },
      { title: 'Get started', to: '/sign-up' },
      { title: 'Workflow', to: '/', hash: '#how-it-works' },
    ],
  },
]

const Footer = () => {
  return (
    <footer className="border-t">
      <div className="mx-auto max-w-6xl">
        <div className="grid grid-cols-2 gap-x-8 gap-y-10 px-6 py-12 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-7 xl:px-0">
          <div className="col-span-full xl:col-span-2">
            <Link to="/" className="font-semibold text-xl text-foreground">
              MedAudit
            </Link>
            <p className="mt-4 text-muted-foreground">
              AI-assisted breast cancer screening compliance audits.
              Guideline-grounded reports and human-in-the-loop review.
            </p>
          </div>

          {footerSections.map(({ title, links }) => (
            <div key={title}>
              <h6 className="font-medium">{title}</h6>
              <ul className="mt-6 space-y-4">
                {links.map((link) => (
                  <li key={link.title}>
                    <Link
                      to={link.to}
                      {...(link.hash && { hash: link.hash })}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      {link.title}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}

          <div className="col-span-2">
            <h6 className="font-medium">Stay up to date</h6>
            <form
              className="mt-6 flex items-center gap-2"
              onSubmit={(e) => e.preventDefault()}
            >
              <Input
                className="max-w-64 grow"
                placeholder="Enter your email"
                type="email"
              />
              <Button type="submit">Subscribe</Button>
            </form>
          </div>
        </div>
        <Separator />
        <div className="flex flex-col-reverse items-center justify-between gap-x-2 gap-y-5 px-6 py-8 sm:flex-row xl:px-0">
          <span className="text-muted-foreground">
            &copy; {new Date().getFullYear()}{' '}
            <Link to="/">MedAudit</Link>. All rights reserved.
          </span>
          <div className="flex items-center gap-5 text-muted-foreground">
            <a href="#" target="_blank" rel="noreferrer" aria-label="Twitter">
              <Twitter className="h-5 w-5" />
            </a>
            <a href="#" target="_blank" rel="noreferrer" aria-label="LinkedIn">
              <Linkedin className="h-5 w-5" />
            </a>
            <a href="#" target="_blank" rel="noreferrer" aria-label="GitHub">
              <Github className="h-5 w-5" />
            </a>
            <a href="mailto:contact@medaudit.example" aria-label="Contact">
              <Mail className="h-5 w-5" />
            </a>
          </div>
        </div>
      </div>
    </footer>
  )
}

export default Footer
