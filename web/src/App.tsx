import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import AppLayout from '@/components/layout/AppLayout'
import LoginPage from '@/pages/LoginPage'
import RegisterPage from '@/pages/RegisterPage'
import DashboardPage from '@/pages/DashboardPage'
import ProductList from '@/pages/products/ProductList'
import SceneList from '@/pages/scenes/SceneList'
import TemplateList from '@/pages/templates/TemplateList'
import GenerateSingle from '@/pages/generate/GenerateSingle'
import GenerateBatch from '@/pages/generate/GenerateBatch'
import JobList from '@/pages/jobs/JobList'
import JobDetail from '@/pages/jobs/JobDetail'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <AppLayout>
                <Routes>
                  <Route path="/" element={<DashboardPage />} />
                  <Route path="/products" element={<ProductList />} />
                  <Route path="/scenes" element={<SceneList />} />
                  <Route path="/templates" element={<TemplateList />} />
                  <Route path="/generate" element={<GenerateSingle />} />
                  <Route path="/generate/batch" element={<GenerateBatch />} />
                  <Route path="/jobs" element={<JobList />} />
                  <Route path="/jobs/:jobUuid" element={<JobDetail />} />
                </Routes>
              </AppLayout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App
