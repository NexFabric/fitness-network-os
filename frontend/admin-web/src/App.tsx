import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import RequireAuth from './components/RequireAuth'
import RequireRole from './components/RequireRole'
import Dashboard from './pages/Dashboard'
import Locations from './pages/Locations'
import Login from './pages/Login'
import Members from './pages/Members'
import Devices from './pages/Devices'
import Notifications from './pages/Notifications'
import Reports from './pages/Reports'
import Staff from './pages/Staff'
import Finance from './pages/Finance'
import { ReloadPrompt } from './components/ReloadPrompt'
import { AuthProvider } from './auth/AuthContext'
import {
  FEDERATION_ROLES,
  MEMBER_ROLES,
  OPS_ROLES,
  ROLES,
  TRAINER_ROLES,
} from './auth/roles'

import MemberPortal from './pages/MemberPortal'
import PortalHome from './pages/PortalHome'
import SuperAdminPortal from './pages/SuperAdminPortal'
import TrainerPortal from './pages/TrainerPortal'

/** Every portal route is auth-gated first, then role-gated. */
function Portal({
  allowed,
  children,
}: {
  allowed: typeof OPS_ROLES
  children: React.ReactNode
}) {
  return (
    <RequireAuth>
      <RequireRole allowed={allowed}>{children}</RequireRole>
    </RequireAuth>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ReloadPrompt />
        <Routes>
          <Route path="/login" element={<Login />} />

          {/* Gateway: needs a session, but no particular role — it shows the
              caller which portals its roles unlock. */}
          <Route
            path="/portal"
            element={
              <RequireAuth>
                <PortalHome />
              </RequireAuth>
            }
          />
          <Route path="/home" element={<Navigate to="/portal" replace />} />

          <Route
            path="/superadmin"
            element={
              <Portal allowed={FEDERATION_ROLES}>
                <SuperAdminPortal />
              </Portal>
            }
          />
          <Route path="/federation" element={<Navigate to="/superadmin" replace />} />

          <Route
            path="/trainer"
            element={
              <Portal allowed={[...TRAINER_ROLES, ROLES.GYM_OWNER, ROLES.GYM_ADMIN]}>
                <TrainerPortal />
              </Portal>
            }
          />

          <Route
            path="/member"
            element={
              <Portal allowed={MEMBER_ROLES}>
                <MemberPortal />
              </Portal>
            }
          />
          <Route path="/athlete" element={<Navigate to="/member" replace />} />

          <Route
            element={
              <Portal allowed={OPS_ROLES}>
                <Layout />
              </Portal>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="members" element={<Members />} />
            <Route path="locations" element={<Locations />} />
            <Route path="finance" element={<Finance />} />
            {/* devices:manage is held only by GYM_OWNER/GYM_ADMIN — the API is
                the boundary, this guard just keeps the page out of reach. */}
            <Route
              path="devices"
              element={
                <RequireRole allowed={[ROLES.GYM_OWNER, ROLES.GYM_ADMIN]}>
                  <Devices />
                </RequireRole>
              }
            />
            {/* notifications:* / reports:* / staff:* sit with the same two roles
                in permissions.yml; the API is still the boundary. */}
            <Route
              path="notifications"
              element={
                <RequireRole allowed={[ROLES.GYM_OWNER, ROLES.GYM_ADMIN]}>
                  <Notifications />
                </RequireRole>
              }
            />
            <Route
              path="reports"
              element={
                <RequireRole allowed={[ROLES.GYM_OWNER, ROLES.GYM_ADMIN]}>
                  <Reports />
                </RequireRole>
              }
            />
            <Route
              path="staff"
              element={
                <RequireRole allowed={[ROLES.GYM_OWNER, ROLES.GYM_ADMIN]}>
                  <Staff />
                </RequireRole>
              }
            />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
