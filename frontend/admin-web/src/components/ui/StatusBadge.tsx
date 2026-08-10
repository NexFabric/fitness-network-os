type StatusBadgeProps = {
  status: string
  kind?: 'member' | 'invoice' | 'payment' | 'auto'
}

function resolveClass(status: string, kind: StatusBadgeProps['kind']): string {
  const s = status.toLowerCase()

  if (kind === 'invoice' || kind === 'auto') {
    if (s === 'paid' || s === 'succeeded' || s === 'completed' || s === 'active') {
      return 'badge-success'
    }
    if (s === 'pending' || s === 'open' || s === 'suspended' || s === 'lead') {
      return 'badge-warn'
    }
    if (s === 'overdue' || s === 'failed' || s === 'canceled' || s === 'cancelled') {
      return 'badge-danger'
    }
  }

  if (s === 'active' || s === 'succeeded' || s === 'completed' || s === 'paid') {
    return 'badge-success'
  }
  if (s === 'suspended' || s === 'pending' || s === 'open' || s === 'lead') {
    return 'badge-warn'
  }
  if (
    s === 'inactive' ||
    s === 'cancelled' ||
    s === 'canceled' ||
    s === 'void' ||
    s === 'failed' ||
    s === 'overdue'
  ) {
    return s === 'failed' || s === 'overdue' ? 'badge-danger' : 'badge-neutral'
  }
  return 'badge-neutral'
}

export function StatusBadge({ status, kind = 'auto' }: StatusBadgeProps) {
  return (
    <span className={resolveClass(status, kind)}>
      <span className="sr-only">Durum: </span>
      {status}
    </span>
  )
}
