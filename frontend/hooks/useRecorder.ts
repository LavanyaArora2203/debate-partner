'use client'

import { useCallback, useEffect, useRef, useState } from 'react'

export function useRecorder() {
  const [status, setStatus] = useState<'idle' | 'requesting' | 'recording' | 'stopped'>('idle')
  const [seconds, setSeconds] = useState(0)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const [error, setError] = useState<string | null>(null)

  const recorder = useRef<MediaRecorder | null>(null)
  const chunks = useRef<Blob[]>([])
  const timer = useRef<ReturnType<typeof setInterval> | null>(null)
  const stopTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const stop = useCallback(() => {
    if (recorder.current?.state === 'recording') recorder.current.stop()

    if (timer.current) {
      clearInterval(timer.current)
      timer.current = null
    }

    if (stopTimer.current) {
      clearTimeout(stopTimer.current)
      stopTimer.current = null
    }
  }, [])

  const start = useCallback(async () => {
    setError(null)
    setStatus('requesting')

    if (
      !navigator.mediaDevices?.getUserMedia ||
      typeof MediaRecorder === 'undefined'
    ) {
      setError(
        'Recording is not supported in this browser. You can type your speech instead.'
      )
      setStatus('idle')
      return
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

      chunks.current = []
      setSeconds(0)

      const next = new MediaRecorder(stream)
      recorder.current = next

      next.ondataavailable = (event) => {
        if (event.data.size) chunks.current.push(event.data)
      }

      next.onstop = () => {
        stream.getTracks().forEach((track) => track.stop())

        const blob = new Blob(chunks.current, {
          type: next.mimeType || 'audio/webm',
        })

        setAudioBlob(blob)
        setAudioUrl(URL.createObjectURL(blob))
        setStatus('stopped')
      }

      next.start()
      setStatus('recording')

      timer.current = setInterval(() => {
        setSeconds((value) => value + 1)
      }, 1000)

      stopTimer.current = setTimeout(stop, 180000)
    } catch {
      setError(
        'We could not access your microphone. Check your browser permission and try again.'
      )
      setStatus('idle')
    }
  }, [stop])

  const reset = useCallback(() => {
    stop()

    if (audioUrl) URL.revokeObjectURL(audioUrl)

    setAudioUrl(null)
    setAudioBlob(null)
    setSeconds(0)
    setError(null)
    setStatus('idle')
  }, [audioUrl, stop])

  useEffect(
    () => () => {
      stop()
      if (audioUrl) URL.revokeObjectURL(audioUrl)
    },
    [audioUrl, stop]
  )

  return { status, seconds, audioUrl, audioBlob, error, start, stop, reset }
}