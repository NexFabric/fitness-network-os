type EmptyStateProps = {
  title: string
  description?: string
  actionLabel?: string
  onAction?: () => void
}

export function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
}: EmptyStateProps) {
  return (
    <div className="px-4 py-12 text-center">
      <p className="font-medium text-slate-200">{title}</p>
      {description ? (
        <p className="mt-1 text-sm text-ink-muted">{description}</p>
      ) : null}
      {actionLabel && onAction ? (
        <button type="button" onClick={onAction} className="btn-primary mt-4">
          {actionLabel}
        </button>
      ) : null}
    </div>
  )
}
