const stats = [
  {
    value: 'RAG + AI',
    label: 'Guideline-grounded',
    description: 'Clinical KB (e.g. BI-RADS) retrieved per audit; AI outputs structured findings and evidence.',
  },
  {
    value: '1',
    label: 'Report schema',
    description: 'Same format for MedGemma, Gemini, or OpenAI: status, findings, evidence, corrective actions.',
  },
  {
    value: '24/7',
    label: 'Scheduled audits',
    description: 'Daily Celery Beat job creates audits for patients due for review; human sign-off in the loop.',
  },
  {
    value: 'EHR',
    label: 'Your data',
    description: 'Point at your EHR service or use the demo patient data; FHIR-style list and bundle APIs.',
  },
]

const Stats = () => {
  return (
    <section className="border-b px-6 py-20">
      <div className="mx-auto w-full max-w-6xl">
        <h2 className="font-semibold text-4xl tracking-tight md:text-5xl">
          Built for compliance at scale
        </h2>
        <p className="mt-4 max-w-2xl text-lg text-muted-foreground">
          One pipeline from EHR to report. RAG over your guidelines, pluggable
          AI, and human review where it matters.
        </p>
        <div className="mt-16 grid gap-10 gap-y-16 sm:mt-24 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map(({ value, label, description }) => (
            <div key={label}>
              <span className="font-semibold text-5xl tracking-tight md:text-6xl">
                {value}
              </span>
              <p className="mt-6 font-medium text-xl">{label}</p>
              <p className="mt-2 text-muted-foreground">{description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

export default Stats
