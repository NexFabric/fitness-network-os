type StatusBadgeProps = {
  status?: string | null
  kind?: 'member' | 'invoice' | 'payment' | 'auto'
}

function resolveClass(status: string, kind: StatusBadgeProps['kind']): string {
  const s = status.toLowerCase()

  if (kind === 'invoice' || kind === 'auto') {
    if (s === 'paid' || s === 'succeeded' || s === 'completed' || s === 'active' || s === 'passed') {
      return 'badge-success'
    }
    if (s === 'pending' || s === 'open' || s === 'suspended' || s === 'lead' || s === 'conditional') {
      return 'badge-warn'
    }
    if (s === 'overdue' || s === 'failed' || s === 'canceled' || s === 'cancelled' || s === 'expired') {
      return 'badge-danger'
    }
  }

  if (s === 'active' || s === 'succeeded' || s === 'completed' || s === 'paid' || s === 'passed') {
    return 'badge-success'
  }
  if (s === 'suspended' || s === 'pending' || s === 'open' || s === 'lead' || s === 'conditional') {
    return 'badge-warn'
  }
  if (
    s === 'inactive' ||
    s === 'cancelled' ||
    s === 'canceled' ||
    s === 'void' ||
    s === 'failed' ||
    s === 'expired' ||
    s === 'overdue'
  ) {
    return s === 'failed' || s === 'overdue' || s === 'expired' ? 'badge-danger' : 'badge-neutral'
  }
  return 'badge-neutral'
}

export function StatusBadge({ status, kind = 'auto' }: StatusBadgeProps) {
  const safeStatus = status || 'ACTIVE'
  return (
    <span className={resolveClass(safeStatus, kind)}>
      <span className="sr-only">Durum: </span>
      {safeStatus}
    </span>
  )
}
