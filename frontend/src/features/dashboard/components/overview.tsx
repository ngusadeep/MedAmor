import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis } from 'recharts'

const MONTHS = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
]

interface OverviewProps {
  /** Reports (or jobs) to bucket by month for the chart */
  reportsByMonth?: { name: string; total: number }[]
}

function defaultData(): { name: string; total: number }[] {
  return MONTHS.map((name) => ({
    name,
    total: 0,
  }))
}

function buildDataFromReports(
  createdAts: string[]
): { name: string; total: number }[] {
  const counts: Record<string, number> = {}
  MONTHS.forEach((_, i) => {
    counts[i] = 0
  })
  const now = new Date()
  createdAts.forEach((iso) => {
    const d = new Date(iso)
    if (d.getFullYear() === now.getFullYear()) {
      const month = d.getMonth()
      counts[month] = (counts[month] ?? 0) + 1
    }
  })
  return MONTHS.map((name, i) => ({
    name,
    total: counts[i] ?? 0,
  }))
}

export function Overview({ reportsByMonth }: OverviewProps) {
  const data =
    reportsByMonth && reportsByMonth.length > 0
      ? reportsByMonth
      : defaultData()

  return (
    <ResponsiveContainer width='100%' height={350}>
      <BarChart data={data}>
        <XAxis
          dataKey='name'
          stroke='#888888'
          fontSize={12}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          direction='ltr'
          stroke='#888888'
          fontSize={12}
          tickLine={false}
          axisLine={false}
          tickFormatter={(value) => `${value}`}
        />
        <Bar
          dataKey='total'
          fill='currentColor'
          radius={[4, 4, 0, 0]}
          className='fill-primary'
        />
      </BarChart>
    </ResponsiveContainer>
  )
}

export { buildDataFromReports, MONTHS }
