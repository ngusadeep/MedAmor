import { Link } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'
import {
  ClipboardCheck,
  FileSearch,
  Shield,
  CalendarCheck,
  Stethoscope,
  Sparkles,
} from 'lucide-react'
import Navbar from '@/components/navbar'
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
      {/* Hero — replace this block with your shadcn hero component */}
      <section className="border-b bg-muted/40 pt-28">
        <div className="mx-auto max-w-6xl px-6 py-20 sm:py-28">
          <div className="flex flex-col items-center gap-8 text-center">
            <div className="flex items-center gap-2 rounded-full border bg-background px-4 py-1.5 text-sm text-muted-foreground">
              <Stethoscope className="h-4 w-4" />
              <span>Breast cancer screening compliance</span>
            </div>
            <h1 className="text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
              AI-assisted medical audits,{' '}
              <span className="text-primary">guideline-grounded</span>
            </h1>
            <p className="max-w-2xl text-lg text-muted-foreground">
              MedAudit compares patient EHR data against clinical guidelines,
              produces structured reports with findings and evidence, and keeps
              human review at the center with annotations and scheduled audits.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-4">
              <Button asChild size="lg">
                <Link to="/sign-in">Sign in</Link>
              </Button>
              <Button asChild variant="outline" size="lg">
                <Link to="/sign-up">Get started</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Features — replace with your shadcn block if needed */}
      <section id="features" className="border-b py-20">
        <div className="mx-auto max-w-6xl px-6">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              Built for compliance teams
            </h2>
            <p className="mt-4 max-w-2xl mx-auto text-muted-foreground">
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

      {/* How it works */}
      <section id="how-it-works" className="border-b bg-muted/30 py-20">
        <div className="mx-auto max-w-6xl px-6">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              How it works
            </h2>
            <p className="mt-4 max-w-2xl mx-auto text-muted-foreground">
              EHR → RAG (guidelines) → AI report. You review and annotate.
            </p>
          </div>
          <div className="grid gap-8 md:grid-cols-3">
            {howItWorks.map(({ step, title, text }) => (
              <div key={step} className="flex flex-col items-center text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary text-primary-foreground font-semibold">
                  {step}
                </div>
                <h3 className="mt-4 font-semibold">{title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA — replace with your shadcn CTA block if needed */}
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
