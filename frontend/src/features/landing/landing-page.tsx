import { Link } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'
import {
  ClipboardCheck,
  FileSearch,
  Shield,
  CalendarCheck,
  Sparkles,
} from 'lucide-react'
import Navbar from '@/components/navbar'
import Hero from '@/components/hero'
import Footer from '@/components/footer'

const features = [
  {
    icon: FileSearch,
    title: 'EHR-driven audits',
    description:
      'Compare patient timelines against clinical guidelines. Pull data from your EHR or our demo service.',
  },
  {
    icon: ClipboardCheck,
    title: 'Structured reports',
    description:
      'Get findings, evidence, corrective actions, and next audit dates—ready for review and annotations.',
  },
  {
    icon: Shield,
    title: 'Guideline-grounded AI',
    description:
      'RAG over your Medical KB (e.g. BI-RADS, SOPs). AI answers are grounded in retrievable guidelines.',
  },
  {
    icon: CalendarCheck,
    title: 'Scheduled reviews',
    description:
      'Daily jobs for patients due for review. Never miss a follow-up; human sign-off stays in the loop.',
  },
]

const howItWorks = [
  {
    step: 1,
    title: 'Connect EHR',
    text: 'Point MedAudit at your EHR service or use our demo patient data.',
  },
  {
    step: 2,
    title: 'Run audits',
    text: 'Create a job per patient or batch. Our worker runs EHR + RAG + AI and writes the report.',
  },
  {
    step: 3,
    title: 'Review & annotate',
    text: 'Open reports, add annotations per finding, and track next audit dates.',
  },
]

export function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <Hero />

      <section id="features" className="border-b py-20">
        <div className="mx-auto max-w-6xl px-6">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              Built for compliance teams
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-muted-foreground">
              From single-patient checks to batch and scheduled audits, with one
              pipeline and one report schema.
            </p>
          </div>
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {features.map(({ icon: Icon, title, description }) => (
              <div
                key={title}
                className="rounded-lg border bg-card p-6 text-card-foreground shadow-sm"
              >
                <Icon className="mb-4 h-10 w-10 text-primary" />
                <h3 className="font-semibold">{title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  {description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="how-it-works" className="border-b bg-muted/30 py-20">
        <div className="mx-auto max-w-6xl px-6">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              How it works
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-muted-foreground">
              EHR → RAG (guidelines) → AI report. You review and annotate.
            </p>
          </div>
          <div className="grid gap-8 md:grid-cols-3">
            {howItWorks.map(({ step, title, text }) => (
              <div key={step} className="flex flex-col items-center text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary font-semibold text-primary-foreground">
                  {step}
                </div>
                <h3 className="mt-4 font-semibold">{title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-20">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <Sparkles className="mx-auto h-12 w-12 text-primary" />
          <h2 className="mt-6 text-3xl font-bold tracking-tight sm:text-4xl">
            Ready to run your first audit?
          </h2>
          <p className="mt-4 text-muted-foreground">
            Sign up, create a job with a patient ID from the list, and view the
            report when it completes.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-4">
            <Button asChild size="lg">
              <Link to="/sign-up">Create account</Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link to="/sign-in">Sign in</Link>
            </Button>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}
