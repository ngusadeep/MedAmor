import React, { useState } from 'react'

type JobsContextType = {
  open: boolean
  setOpen: (v: boolean) => void
  onSuccess?: () => void
  setOnSuccess: (fn: (() => void) | undefined) => void
}

const JobsContext = React.createContext<JobsContextType | null>(null)

export function JobsProvider({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false)
  const [onSuccess, setOnSuccess] = useState<(() => void) | undefined>(
    undefined
  )

  return (
    <JobsContext.Provider
      value={{ open, setOpen, onSuccess, setOnSuccess }}
    >
      {children}
    </JobsContext.Provider>
  )
}

export function useJobs() {
  const ctx = React.useContext(JobsContext)
  if (!ctx) throw new Error('useJobs must be used within JobsProvider')
  return ctx
}
