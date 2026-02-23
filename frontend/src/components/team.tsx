const teamMembers = [
  {
    name: 'Charles Law',
    title: 'Team Lead · EHR server',
    bio: 'EHR integrations, patient list and bundle API. 7.5 years deploying AI in large hospital systems.',
  },
  {
    name: 'Dr. Greg Russell',
    title: 'AI research · Demo · Compliance',
    bio: 'Clinical researcher and expert; AI research, demo, and compliance & governance.',
  },
  {
    name: 'Samwel Ngusa',
    title: 'Frontend',
    bio: 'Dashboard, jobs, reports, and annotations UI. AI researcher & software engineer.',
  },
  {
    name: 'Nazmus Sakib Ahmed',
    title: 'AI orchestration & Backend',
    bio: 'Pipeline, RAG, API, and workers. AI engineering.',
  },
]

function Avatar({ name }: { name: string }) {
  const initials = name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
  return (
    <div
      className="flex h-20 w-20 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xl font-semibold text-primary"
      aria-hidden
    >
      {initials}
    </div>
  )
}

const Team = () => {
  return (
    <section className="border-b bg-muted/20">
      <div className="mx-auto flex max-w-6xl flex-col justify-center px-6 py-12 sm:py-20">
        <span className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Our team
        </span>
        <h2 className="mt-4 font-semibold text-3xl tracking-tight md:text-4xl">
          The people behind MedArmor
        </h2>
        <p className="mt-3 max-w-2xl text-base text-muted-foreground sm:text-lg">
          AI research, clinical expertise, EHR systems, and full-stack engineering.
        </p>
        <div className="mt-14 grid w-full grid-cols-1 gap-8 sm:mt-20 sm:grid-cols-2 lg:grid-cols-4">
          {teamMembers.map((member) => (
            <div key={member.name}>
              <Avatar name={member.name} />
              <h3 className="mt-4 font-semibold text-lg">{member.name}</h3>
              <p className="text-sm text-muted-foreground">{member.title}</p>
              <p className="mt-3 text-sm">{member.bio}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

export default Team
