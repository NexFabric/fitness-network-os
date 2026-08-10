import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import RequireAuth from './components/RequireAuth'
import Dashboard from './pages/Dashboard'
import Locations from './pages/Locations'
import Login from './pages/Login'
import Members from './pages/Members'
import Finance from './pages/Finance'
import { ReloadPrompt } from './components/ReloadPrompt'

export default function App() {
  return (
    <BrowserRouter>
      <ReloadPrompt />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          element={
            <RequireAuth>
              <Layout />
            </RequireAuth>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="members" element={<Members />} />
          <Route path="locations" element={<Locations />} />
          <Route path="finance" element={<Finance />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
