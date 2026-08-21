import { useCallback, useEffect, useRef, useState } from 'react'
import jsQR from 'jsqr'

/** Minimal BarcodeDetector shape (Chromium); not in all TS lib targets. */
type BarcodeDetectorLike = {
  detect: (source: ImageBitmapSource) => Promise<Array<{ rawValue?: string }>>
}

type BarcodeDetectorCtor = new (options?: {
  formats?: string[]
}) => BarcodeDetectorLike

function getBarcodeDetector(): BarcodeDetectorCtor | null {
  if (typeof window === 'undefined') return null
  const ctor = (
    window as unknown as { BarcodeDetector?: BarcodeDetectorCtor }
  ).BarcodeDetector
  return ctor ?? null
}

export type CameraQrScannerProps = {
  /** Called once per successful decode (camera stops after first hit). */
  onDecode: (token: string) => void
  /** Optional: parent can force-stop via remount or calling stop from outside. */
  active: boolean
  onStop?: () => void
}

/**
 * Camera QR capture via getUserMedia.
 * Prefers BarcodeDetector when available; falls back to jsQR on canvas frames.
 * facingMode: environment (back camera) preferred for door scanners.
 */
export function CameraQrScanner({
  onDecode,
  active,
  onStop,
}: CameraQrScannerProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const rafRef = useRef<number | null>(null)
  const detectorRef = useRef<BarcodeDetectorLike | null>(null)
  const decodedRef = useRef(false)
  const onDecodeRef = useRef(onDecode)
  onDecodeRef.current = onDecode

  const [cameraError, setCameraError] = useState<string | null>(null)
  const [starting, setStarting] = useState(false)

  const stopTracks = useCallback(() => {
    if (rafRef.current != null) {
      cancelAnimationFrame(rafRef.current)
      rafRef.current = null
    }
    const stream = streamRef.current
    if (stream) {
      for (const track of stream.getTracks()) {
        track.stop()
      }
      streamRef.current = null
    }
    const video = videoRef.current
    if (video) {
      video.srcObject = null
    }
  }, [])

  const handleStop = useCallback(() => {
    stopTracks()
    setStarting(false)
    setCameraError(null)
    onStop?.()
  }, [stopTracks, onStop])

  useEffect(() => {
    if (!active) {
      stopTracks()
      decodedRef.current = false
      return
    }

    let cancelled = false
    decodedRef.current = false

    async function start() {
      if (!navigator.mediaDevices?.getUserMedia) {
        setCameraError(
          'Camera API not available in this browser. Paste the QR token instead.',
        )
        setStarting(false)
        return
      }

      setStarting(true)
      setCameraError(null)

      try {
        const BD = getBarcodeDetector()
        if (BD) {
          try {
            detectorRef.current = new BD({ formats: ['qr_code'] })
          } catch {
            detectorRef.current = null
          }
        }

        const stream = await navigator.mediaDevices.getUserMedia({
          audio: false,
          video: {
            facingMode: { ideal: 'environment' },
            width: { ideal: 1280 },
            height: { ideal: 720 },
          },
        })

        if (cancelled) {
          for (const track of stream.getTracks()) track.stop()
          return
        }

        streamRef.current = stream
        const video = videoRef.current
        if (!video) {
          for (const track of stream.getTracks()) track.stop()
          setCameraError('Video element unavailable.')
          setStarting(false)
          return
        }

        video.srcObject = stream
        await video.play()
        setStarting(false)

        const canvas = canvasRef.current
        const ctx = canvas?.getContext('2d', { willReadFrequently: true })

        const tick = async () => {
          if (cancelled || decodedRef.current) return
          const v = videoRef.current
          if (!v || v.readyState < 2) {
            rafRef.current = requestAnimationFrame(() => {
              void tick()
            })
            return
          }

          try {
            // Prefer native BarcodeDetector
            const detector = detectorRef.current
            if (detector) {
              const codes = await detector.detect(v)
              const value = codes[0]?.rawValue?.trim()
              if (value) {
                decodedRef.current = true
                stopTracks()
                onDecodeRef.current(value)
                return
              }
            } else if (canvas && ctx) {
              const w = v.videoWidth
              const h = v.videoHeight
              if (w > 0 && h > 0) {
                canvas.width = w
                canvas.height = h
                ctx.drawImage(v, 0, 0, w, h)
                const imageData = ctx.getImageData(0, 0, w, h)
                const code = jsQR(imageData.data, w, h, {
                  inversionAttempts: 'dontInvert',
                })
                const value = code?.data?.trim()
                if (value) {
                  decodedRef.current = true
                  stopTracks()
                  onDecodeRef.current(value)
                  return
                }
              }
            }
          } catch {
            // Frame decode errors are transient; keep scanning.
          }

          rafRef.current = requestAnimationFrame(() => {
            void tick()
          })
        }

        rafRef.current = requestAnimationFrame(() => {
          void tick()
        })
      } catch (err) {
        if (cancelled) return
        setStarting(false)
        const name = err instanceof DOMException ? err.name : ''
        if (name === 'NotAllowedError' || name === 'PermissionDeniedError') {
          setCameraError(
            'Camera permission denied. Enable camera access or paste the QR token below.',
          )
        } else if (
          name === 'NotFoundError' ||
          name === 'DevicesNotFoundError'
        ) {
          setCameraError(
            'No camera found on this device. Paste the QR token below.',
          )
        } else if (name === 'NotReadableError' || name === 'TrackStartError') {
          setCameraError(
            'Camera is in use by another app. Close it or paste the QR token.',
          )
        } else {
          const msg =
            err instanceof Error ? err.message : 'Could not start camera'
          setCameraError(`${msg}. Paste the QR token as a fallback.`)
        }
      }
    }

    void start()

    return () => {
      cancelled = true
      stopTracks()
    }
  }, [active, stopTracks])

  if (!active) return null

  return (
    <div className="overflow-hidden rounded-xl border border-teal-800/40 bg-black shadow-lg shadow-black/40">
      <div className="relative aspect-[4/3] w-full bg-slate-950">
        <video
          ref={videoRef}
          className="h-full w-full object-cover"
          playsInline
          muted
          autoPlay
          aria-label="Camera preview for QR scanning"
        />
        {/* Hidden canvas for jsQR frame sampling */}
        <canvas ref={canvasRef} className="hidden" aria-hidden />
        {/* Viewfinder guide */}
        <div
          className="pointer-events-none absolute inset-0 flex items-center justify-center"
          aria-hidden
        >
          <div className="h-48 w-48 rounded-xl border-2 border-emerald-400/90 shadow-[0_0_0_9999px_rgba(0,0,0,0.4)]" />
        </div>
        {starting && !cameraError && (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-950/70 text-sm text-slate-300">
            Starting camera…
          </div>
        )}
      </div>
      {cameraError && (
        <div
          className="border-t border-red-900 bg-red-950/80 px-3 py-2 text-sm text-red-200"
          role="alert"
        >
          {cameraError}
        </div>
      )}
      <div className="flex items-center justify-between gap-2 border-t border-slate-800 bg-slate-900/95 px-3 py-2.5">
        <p className="text-xs text-slate-400">
          Arka kamerayı üyenin QR koduna doğrultun
        </p>
        <button
          type="button"
          onClick={handleStop}
          className="inline-flex shrink-0 items-center justify-center min-h-[44px] min-w-[44px] rounded-lg border border-slate-600 px-3.5 py-2 text-sm font-medium text-slate-200 hover:bg-slate-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/60"
        >
          Kamerayı durdur
        </button>
      </div>
    </div>
  )
}
