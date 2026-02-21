import { Loader2, Mic, MicOff, RotateCcw } from 'lucide-react'
import {
  type ASRProvider,
  type RecordingState,
  useVoiceRecorder,
} from '@/hooks/use-voice-recorder'
import { Button } from '@/components/ui/button'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'

interface VoiceDictationButtonProps {
  /** Called with the final transcript text. Append or replace the note as needed. */
  onTranscript: (text: string) => void
  provider: ASRProvider
  onProviderChange: (provider: ASRProvider) => void
  disabled?: boolean
  className?: string
}

const PROVIDER_LABELS: Record<ASRProvider, string> = {
  medasr: 'MedASR (API)',
  medasr_local: 'MedASR (Local)',
  deepgram: 'Deepgram',
}

function tooltipLabel(state: RecordingState, error: string | null, provider: ASRProvider) {
  if (state === 'transcribing') return 'Transcribing…'
  if (state === 'error') return `Error: ${error ?? 'unknown'} — click to reset`
  if (state === 'recording') return 'Stop recording'
  return `Dictate note (${PROVIDER_LABELS[provider]})`
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

  const isRecording = state === 'recording'
  const isTranscribing = state === 'transcribing'
  const hasError = state === 'error'
  const busy = isRecording || isTranscribing

  function handleClick() {
    if (hasError) { reset(); return }
    if (isRecording) stopRecording()
    else startRecording()
  }

  return (
    <div className={cn('flex items-center gap-1.5', className)}>
      {/* Provider selector */}
      <select
        className='h-9 rounded-md border border-input bg-transparent px-2 text-xs shadow-sm transition-colors focus:outline-none focus:ring-1 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50'
        value={provider}
        onChange={(e) => onProviderChange(e.target.value as ASRProvider)}
        disabled={busy || disabled}
        aria-label='ASR provider'
      >
        <option value='medasr'>MedASR (API)</option>
        <option value='medasr_local'>MedASR (Local)</option>
        <option value='deepgram'>Deepgram</option>
      </select>

      {/* Mic / stop / reset button */}
      <TooltipProvider delayDuration={300}>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              type='button'
              variant={isRecording ? 'destructive' : 'outline'}
              size='icon'
              className={cn('h-9 w-9 shrink-0', isRecording && 'animate-pulse')}
              disabled={isTranscribing || disabled}
              onClick={handleClick}
              aria-label={tooltipLabel(state, error, provider)}
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
          </TooltipTrigger>
          <TooltipContent side='top'>
            {tooltipLabel(state, error, provider)}
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      {/* Inline status */}
      {isRecording && (
        <span className='text-xs font-medium text-destructive animate-pulse'>
          Recording…
        </span>
      )}
      {isTranscribing && (
        <span className='text-xs text-muted-foreground'>Transcribing…</span>
      )}
      {hasError && (
        <span className='text-xs text-destructive' title={error ?? undefined}>
          Failed — click to retry
        </span>
      )}
    </div>
  )
}
