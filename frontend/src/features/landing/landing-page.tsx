import { Link } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'
import { Sparkles } from 'lucide-react'
import Navbar from '@/components/navbar'
import Hero from '@/components/hero'
import Features from '@/components/features'
import Stats from '@/components/stats'
import FAQ from '@/components/faq'
import Team from '@/components/team'
import Footer from '@/components/footer'

const howItWorks = [
  {
    step: 1,
    title: 'Connect EHR',
    text: 'Point MedArmor at your EHR service or use our demo patient data.',
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

      <Features />

      <Stats />

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

      <FAQ />

      <Team />

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
