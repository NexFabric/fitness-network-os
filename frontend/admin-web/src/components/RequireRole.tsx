import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { homeRouteFor, type RoleName } from '../auth/roles'

type RequireRoleProps = {
  allowed: RoleName[]
  children: ReactNode
}

/**
 * Role gate for a portal route. Must sit inside <RequireAuth>, which has
 * already guaranteed a confirmed session.
 *
 * A denied user is sent to its own portal rather than shown a 403 page — the
 * common case is someone typing the wrong URL, not an attack.
 */
export default function RequireRole({ allowed, children }: RequireRoleProps) {
  const { session, hasRole } = useAuth()

  if (!session) {
    return <Navigate to="/login" replace />
  }

  if (!hasRole(allowed)) {
    return (
      <Navigate
        to={homeRouteFor(session.roles, session.is_superuser)}
        replace
      />
    )
  }

  return <>{children}</>
}
