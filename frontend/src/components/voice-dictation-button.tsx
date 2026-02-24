import { Loader2, Mic, MicOff, RotateCcw, Settings2 } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { type ASRProvider, useVoiceRecorder } from '@/hooks/use-voice-recorder'
import { Button } from '@/components/ui/button'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { cn } from '@/lib/utils'

interface VoiceDictationButtonProps {
  onTranscript: (text: string) => void
  provider: ASRProvider
  onProviderChange: (provider: ASRProvider) => void
  disabled?: boolean
  className?: string
}

const PROVIDER_LABELS: Record<ASRProvider, string> = {
  medasr_local: 'MedASR (Local)',
  medasr: 'MedASR (API)',
  deepgram: 'Deepgram',
}

function useDurationCounter(active: boolean) {
  const [seconds, setSeconds] = useState(0)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (active) {
      setSeconds(0)
      intervalRef.current = setInterval(() => setSeconds((s) => s + 1), 1000)
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current)
      setSeconds(0)
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [active])

  return seconds
}

function formatDuration(s: number) {
  const m = Math.floor(s / 60)
  const sec = s % 60
  return `${m}:${String(sec).padStart(2, '0')}`
}

export function VoiceDictationButton({
  onTranscript,
  provider,
  onProviderChange,
  disabled,
  className,
}: VoiceDictationButtonProps) {
  const { state, error, startRecording, stopRecording, reset } = useVoiceRecorder(
    { onTranscript, provider }
  )
  const [settingsOpen, setSettingsOpen] = useState(false)

  const isRecording = state === 'recording'
  const isTranscribing = state === 'transcribing'
  const hasError = state === 'error'
  const busy = isRecording || isTranscribing
  const duration = useDurationCounter(isRecording)

  function handleMicClick() {
    if (hasError) { reset(); return }
    if (isRecording) stopRecording()
    else startRecording()
  }

  return (
    <div className={cn('flex items-center gap-1', className)}>
      {/* Recording state pill */}
      {isRecording && (
        <span className='flex items-center gap-1.5 rounded-full bg-destructive/10 border border-destructive/30 px-2.5 py-1 text-xs font-semibold text-destructive'>
          <span className='h-1.5 w-1.5 rounded-full bg-destructive animate-pulse' />
          {formatDuration(duration)}
        </span>
      )}

      {isTranscribing && (
        <span className='flex items-center gap-1.5 rounded-full bg-muted px-2.5 py-1 text-xs text-muted-foreground'>
          <Loader2 className='h-3 w-3 animate-spin' />
          Transcribing…
        </span>
      )}

      {hasError && (
        <span
          className='max-w-[180px] truncate rounded-full bg-destructive/10 px-2.5 py-1 text-xs text-destructive cursor-pointer'
          title={error ?? undefined}
          onClick={reset}
        >
          {error ?? 'Error'} · tap to retry
        </span>
      )}

      {/* Mic button */}
      <Button
        type='button'
        variant={isRecording ? 'destructive' : 'outline'}
        size='icon'
        className={cn(
          'h-9 w-9 shrink-0 rounded-full transition-all',
          isRecording && 'ring-2 ring-destructive ring-offset-2 shadow-md',
        )}
        disabled={isTranscribing || disabled}
        onClick={handleMicClick}
        aria-label={
          isRecording
            ? `Stop recording (${formatDuration(duration)})`
            : isTranscribing
              ? 'Transcribing…'
              : `Dictate with ${PROVIDER_LABELS[provider]}`
        }
      >
        {isTranscribing ? (
          <Loader2 className='h-4 w-4 animate-spin' />
        ) : hasError ? (
          <RotateCcw className='h-4 w-4' />
        ) : isRecording ? (
          <MicOff className='h-4 w-4' />
        ) : (
          <Mic className='h-4 w-4' />
        )}
      </Button>

      {/* Provider badge + popover trigger — always visible so users know what's active */}
      <Popover open={settingsOpen} onOpenChange={setSettingsOpen}>
        <PopoverTrigger asChild>
          <button
            type='button'
            disabled={busy || disabled}
            aria-label='Switch transcription provider'
            className={cn(
              'flex items-center gap-1 rounded-full border px-2.5 py-1 text-[11px] font-medium transition-colors',
              'border-border bg-muted/60 text-muted-foreground hover:border-primary/60 hover:bg-accent hover:text-accent-foreground',
              'disabled:cursor-not-allowed disabled:opacity-50',
            )}
          >
            <Settings2 className='h-3 w-3 shrink-0' />
            {PROVIDER_LABELS[provider]}
          </button>
        </PopoverTrigger>
        <PopoverContent align='end' className='w-48 p-1.5'>
          <p className='px-2 py-1 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground'>
            Transcription provider
          </p>
          {(['medasr_local', 'medasr', 'deepgram'] as ASRProvider[]).map((p) => (
            <button
              key={p}
              type='button'
              className={cn(
                'flex w-full items-center gap-2 rounded px-2 py-1.5 text-xs text-left transition-colors hover:bg-accent',
                provider === p && 'bg-accent font-semibold text-accent-foreground',
              )}
              onClick={() => { onProviderChange(p); setSettingsOpen(false) }}
            >
              <span
                className={cn(
                  'h-1.5 w-1.5 shrink-0 rounded-full',
                  provider === p ? 'bg-primary' : 'bg-muted-foreground/30',
                )}
              />
              {PROVIDER_LABELS[p]}
              {p === 'medasr_local' && (
                <span className='ml-auto text-[10px] text-muted-foreground'>default</span>
              )}
            </button>
          ))}
        </PopoverContent>
      </Popover>
    </div>
  )
}
