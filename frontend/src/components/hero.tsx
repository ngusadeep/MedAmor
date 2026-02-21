import { ArrowUpRight, Stethoscope } from 'lucide-react'
import { Link } from '@tanstack/react-router'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { BackgroundPattern } from '@/components/background-pattern'

export default function Hero() {
  return (
    <div className="flex min-h-[85vh] items-center justify-center px-6 pt-24">
      <BackgroundPattern />

      <div className="relative z-10 max-w-3xl text-center">
        <Badge
          asChild
          className="rounded-full border-border py-1"
          variant="secondary"
        >
          <Link to="/" className="flex items-center gap-1">
            <Stethoscope className="size-4" />
            Breast cancer screening compliance
            <ArrowUpRight className="ml-1 size-4" />
          </Link>
        </Badge>
        <h1 className="mt-6 font-semibold text-4xl tracking-tighter sm:text-5xl md:text-6xl md:leading-[1.2] lg:text-7xl">
          AI-assisted medical audits,{' '}
          <span className="text-primary">guideline-grounded</span>
        </h1>
        <p className="mt-6 text-foreground/80 md:text-lg">
          MedArmor compares patient EHR data against clinical guidelines,
          produces structured reports with findings and evidence, and keeps
          human review at the center with annotations and scheduled audits.
        </p>
        <div className="mt-12 flex items-center justify-center gap-4">
          <Button className="rounded-full text-base" size="lg" asChild>
            <Link to="/sign-up">
              Get started <ArrowUpRight className="ml-1 size-5" />
            </Link>
          </Button>
          <Button
            className="rounded-full text-base shadow-none"
            size="lg"
            variant="outline"
            asChild
          >
            <Link to="/sign-in">Sign in</Link>
          </Button>
        </div>
      </div>
    </div>
  )
}
