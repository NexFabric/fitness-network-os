import type { ReactNode } from 'react'

type AlertProps = {
  variant?: 'error' | 'success' | 'info'
  children: ReactNode
  onRetry?: () => void
}

export function Alert({ variant = 'error', children, onRetry }: AlertProps) {
  const cls =
    variant === 'success'
      ? 'alert-success'
      : variant === 'info'
        ? 'rounded-control border border-slate-700 bg-slate-900/60 px-4 py-3 text-sm text-slate-300'
        : 'alert-error'

  return (
    <div className={cls} role={variant === 'error' ? 'alert' : 'status'}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>{children}</div>
        {onRetry ? (
          <button type="button" onClick={onRetry} className="btn-secondary shrink-0">
            Yeniden dene
          </button>
        ) : null}
      </div>
    </div>
  )
}
