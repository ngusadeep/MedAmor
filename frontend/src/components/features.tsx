import {
  FileSearch,
  ClipboardCheck,
  Shield,
  CalendarCheck,
  Users,
  MessageSquare,
} from 'lucide-react'

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
  {
    icon: Users,
    title: 'Due-for-review list',
    description:
      'See which patients are due for audit and create jobs in one click or run batch audits.',
  },
  {
    icon: MessageSquare,
    title: 'Human-in-the-loop',
    description:
      'Add annotations per finding on reports. Review and override before sign-off.',
  },
]

const Features = () => {
  return (
    <section id="features" className="border-b py-20">
      <div className="flex items-center justify-center py-6">
        <div className="w-full max-w-5xl px-6">
          <h2 className="text-center font-semibold text-4xl tracking-tight sm:text-5xl">
            Built for compliance teams
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-center text-muted-foreground">
            From single-patient checks to batch and scheduled audits, with one
            pipeline and one report schema.
          </p>
          <div className="mx-auto mt-10 grid gap-6 sm:mt-16 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => {
              const Icon = feature.icon
              return (
                <div
                  className="flex flex-col rounded-xl border bg-card px-5 py-6 text-card-foreground shadow-sm"
                  key={feature.title}
                >
                  <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-full bg-muted">
                    <Icon className="size-5 text-primary" />
                  </div>
                  <span className="font-semibold text-lg">{feature.title}</span>
                  <p className="mt-1 text-[15px] text-foreground/80">
                    {feature.description}
                  </p>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </section>
  )
}

export default Features
