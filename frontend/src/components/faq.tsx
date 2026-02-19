import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'

const faq = [
  {
    question: 'What does MedAudit do?',
    answer:
      'MedAudit runs AI-assisted compliance audits for breast cancer screening. It compares patient EHR data against clinical guidelines (e.g. BI-RADS), uses RAG to ground answers in your Medical KB, and produces structured reports with findings, evidence, and corrective actions. You review and annotate before sign-off.',
  },
  {
    question: 'How do I run an audit?',
    answer:
      'Sign in, go to Audit Jobs, and create a job with one patient ID or select multiple patients for a batch. The system enqueues a task that fetches EHR data, retrieves guidelines via RAG, and calls the configured AI (MedGemma, Gemini, or OpenAI) to generate the report. You can view job status and open the report when it completes.',
  },
  {
    question: 'Where does the patient data come from?',
    answer:
      'Patient list and per-patient bundles come from an EHR service you configure (EHR_SERVICE_URL). The demo includes a local EHR service that serves sample data from the repo. You can also point the backend at your own FHIR-compatible or custom API.',
  },
  {
    question: 'What AI models can I use?',
    answer:
      'You can use MedGemma (local or container), Google Gemini, or OpenAI. Set AUDIT_AI_PROVIDER and the corresponding API keys in .env. All providers output the same report schema (status, findings, evidence, corrective actions, next_audit_date).',
  },
  {
    question: 'What are scheduled audits?',
    answer:
      'Celery Beat runs daily and creates audit jobs for patients who are due for review (no report yet or next_audit_date ≤ today). Those jobs run the same pipeline as manual jobs. You can see due-for-review counts on the Patients page and in the dashboard.',
  },
]

const FAQ = () => {
  return (
    <section id="faq" className="border-b bg-muted/20 px-6 py-20">
      <div className="mx-auto flex max-w-6xl flex-col items-start gap-6 md:flex-row md:gap-12">
        <h2 className="shrink-0 font-semibold text-4xl tracking-tight lg:text-5xl">
          Frequently Asked <br /> Questions
        </h2>
        <Accordion className="w-full max-w-xl" defaultValue="question-0" type="single">
          {faq.map(({ question, answer }, index) => (
            <AccordionItem key={question} value={`question-${index}`}>
              <AccordionTrigger className="text-left text-lg">
                {question}
              </AccordionTrigger>
              <AccordionContent className="text-base text-muted-foreground">
                {answer}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </section>
  )
}

export default FAQ
