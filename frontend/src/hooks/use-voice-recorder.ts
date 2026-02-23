import { useCallback, useRef, useState } from 'react'

export type ASRProvider = 'medasr' | 'medasr_local' | 'deepgram'
export type RecordingState = 'idle' | 'recording' | 'transcribing' | 'error'

interface UseVoiceRecorderOptions {
  onTranscript: (text: string) => void
  provider?: ASRProvider
}

export function useVoiceRecorder({
  onTranscript,
  provider = 'medasr',
}: UseVoiceRecorderOptions) {
  const [state, setState] = useState<RecordingState>('idle')
  const [error, setError] = useState<string | null>(null)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])

  const startRecording = useCallback(async () => {
    setError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

      // Prefer webm/opus (Chromium) then webm (Firefox); fall back to browser default
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm')
          ? 'audio/webm'
          : ''

      const recorder = new MediaRecorder(
        stream,
        mimeType ? { mimeType } : undefined
      )
      chunksRef.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop())
        const blob = new Blob(chunksRef.current, {
          type: recorder.mimeType || 'audio/webm',
        })
        setState('transcribing')
        try {
          const text = await _uploadForTranscription(
            blob,
            recorder.mimeType || 'audio/webm',
            provider
          )
          onTranscript(text)
          setState('idle')
        } catch (err) {
          setError(
            err instanceof Error ? err.message : 'Transcription failed'
          )
          setState('error')
        }
      }

      recorderRef.current = recorder
      recorder.start()
      setState('recording')
    } catch {
      setError('Microphone access denied. Please allow microphone permissions.')
      setState('error')
    }
  }, [onTranscript, provider])

  const stopRecording = useCallback(() => {
    recorderRef.current?.stop()
  }, [])

  const reset = useCallback(() => {
    setState('idle')
    setError(null)
  }, [])

  return { state, error, startRecording, stopRecording, reset }
}

async function _uploadForTranscription(
  blob: Blob,
  mimeType: string,
  provider: ASRProvider
): Promise<string> {
  const base =
    (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '') ??
    '/api'

  const form = new FormData()
  const ext = mimeType.includes('webm') ? 'webm' : 'mp4'
  form.append('audio', blob, `recording.${ext}`)
  form.append('provider', provider)

  const res = await fetch(`${base}/transcribe`, {
    method: 'POST',
    credentials: 'include',
    body: form,
  })

  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(
      (data as { detail?: string }).detail ?? 'Transcription failed'
    )
  }

  const data = (await res.json()) as { text: string }
  return data.text ?? ''
}
