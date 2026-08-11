import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { getTenantId } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { Alert, LoadingSkeleton } from './ui'

/**
 * Gate on a session the server confirmed, not on a localStorage string.
 *
 * The previous version returned true whenever a tenant id existed in
 * localStorage, so anyone could type one in devtools and render the console
 * shell. Now the gate waits for GET /me/session.
 */
export default function RequireAuth({ children }: { children: ReactNode }) {
  const location = useLocation()
  const { session, loading, error } = useAuth()

  // No tenant id at all — never authenticated, skip the spinner.
  if (!getTenantId() && !session) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }

  if (loading) {
    return (
      <div className="p-8">
        <LoadingSkeleton rows={5} />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <Alert variant="error">{error}</Alert>
      </div>
    )
  }

  if (!session) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }

  return <>{children}</>
}
