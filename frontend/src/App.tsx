import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './lib/auth/AuthContext'
import { ProtectedRoute } from './app/guards/ProtectedRoute'
import { AdminRoute } from './app/guards/AdminRoute'
import { SuporteRoute } from './app/guards/SuporteRoute'
import { RoleRoute } from './app/guards/RoleRoute'
import { RoleName } from './lib/auth/permissions'
import { Layout } from './app/layout/Layout'
import LoginPage from './app/routes/LoginPage'
import DashboardPage from './app/routes/DashboardPage'
import UsuariosPage from './app/routes/UsuariosPage'
import ClientesPage from './app/routes/ClientesPage'
import ClienteDetailPage from './app/routes/ClienteDetailPage'
import FormulariosPage from './app/routes/FormulariosPage'
import FormTemplateEditPage from './app/routes/FormTemplateEditPage'
import FormPageEditPage from './app/routes/FormPageEditPage'
import LookupListsPage from './app/routes/LookupListsPage'
import ReportKickoffPage from './app/routes/ReportKickoffPage'
import ReportListPage from './app/routes/ReportListPage'
import ReportWizardPage from './app/routes/ReportWizardPage'
import ManutTiposPage from './app/routes/ManutTiposPage'
import ManutEquipamentosPage from './app/routes/ManutEquipamentosPage'
import ConfiguracoesPage from './app/routes/ConfiguracoesPage'
import NotFoundPage from './app/routes/NotFoundPage'

function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Rota pública */}
        <Route path="/login" element={<LoginPage />} />

        {/* Rotas protegidas */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          
          {/* Dashboard - Todos os perfis */}
          <Route
            path="dashboard"
            element={
              <RoleRoute allowedRoles={[RoleName.TECNICO, RoleName.SUPORTE, RoleName.ADMINISTRADOR]}>
                <DashboardPage />
              </RoleRoute>
            }
          />

          {/* Novo relatório — somente Técnico (#244; RoleRoute valida canCreateReport) */}
          <Route
            path="novo-relatorio"
            element={
              <RoleRoute allowedRoles={[RoleName.TECNICO]}>
                <ReportKickoffPage />
              </RoleRoute>
            }
          />
          <Route
            path="relatorios"
            element={
              <RoleRoute allowedRoles={[RoleName.TECNICO, RoleName.SUPORTE, RoleName.ADMINISTRADOR]}>
                <ReportListPage />
              </RoleRoute>
            }
          />
          <Route
            path="relatorios/:id/preencher"
            element={
              <RoleRoute allowedRoles={[RoleName.TECNICO, RoleName.SUPORTE, RoleName.ADMINISTRADOR]}>
                <ReportWizardPage />
              </RoleRoute>
            }
          />

          {/* Clientes - Suporte e Administrador */}
          <Route
            path="clientes"
            element={
              <SuporteRoute>
                <ClientesPage />
              </SuporteRoute>
            }
          />
          <Route
            path="clientes/:clienteId"
            element={
              <SuporteRoute>
                <ClienteDetailPage />
              </SuporteRoute>
            }
          />

          {/* Rotas de usuários - Apenas Administrador */}
          <Route
            path="usuarios"
            element={
              <AdminRoute>
                <UsuariosPage />
              </AdminRoute>
            }
          />

          {/* Rotas admin */}
          <Route
            path="formularios"
            element={
              <AdminRoute>
                <FormulariosPage />
              </AdminRoute>
            }
          />
          <Route
            path="formularios/:id"
            element={
              <AdminRoute>
                <FormTemplateEditPage />
              </AdminRoute>
            }
          />
          <Route
            path="formularios/:id/pages/:pageId"
            element={
              <AdminRoute>
                <FormPageEditPage />
              </AdminRoute>
            }
          />
          <Route
            path="listas"
            element={
              <AdminRoute>
                <LookupListsPage />
              </AdminRoute>
            }
          />
          <Route
            path="configuracoes"
            element={
              <AdminRoute>
                <ConfiguracoesPage />
              </AdminRoute>
            }
          />

          {/* Cadastros NR13 - Suporte e Administrador */}
          <Route
            path="equipamentos"
            element={
              <SuporteRoute>
                <ManutEquipamentosPage />
              </SuporteRoute>
            }
          />
          <Route
            path="tipos"
            element={
              <SuporteRoute>
                <ManutTiposPage />
              </SuporteRoute>
            }
          />

          {/* Redirects legados /nr13/* */}
          <Route path="nr13/clientes" element={<Navigate to="/clientes" replace />} />
          <Route path="nr13/equipamentos" element={<Navigate to="/equipamentos" replace />} />
          <Route path="nr13/tipos" element={<Navigate to="/tipos" replace />} />
        </Route>

        {/* 404 */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </AuthProvider>
  )
}

export default App
