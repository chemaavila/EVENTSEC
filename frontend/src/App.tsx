import { useState } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import "./App.css";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import Topbar from "./components/layout/Topbar";
import Sidebar from "./components/layout/Sidebar";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import AlertsPage from "./pages/Alerts/AlertsPage";
import AlertDetailPage from "./pages/Alerts/AlertDetailPage";
import HandoverPage from "./pages/Handover/HandoverPage";
import ProfilePage from "./pages/Profile/ProfilePage";
import SiemPage from "./pages/SiemPage";
import EdrPage from "./pages/EdrPage";
import IocBiocPage from "./pages/IocBiocPage";
import AnalyticsRulesPage from "./pages/AnalyticsRulesPage";
import CorrelationRulesPage from "./pages/CorrelationRulesPage";
import AdvancedSearchPage from "./pages/AdvancedSearchPage";
import EventsExplorerPage from "./pages/EventsExplorerPage";
import UserManagementPage from "./pages/Admin/UserManagementPage";
import SandboxPage from "./pages/SandboxPage";
import EndpointsPage from "./pages/EndpointsPage";
import SoftwareInventoryPage from "./pages/SoftwareInventoryPage";
import WorkplansPage from "./pages/WorkplansPage";
import EmailProtectionPage from "./pages/EmailProtectionPage";
import ThreatIntelPage from "./pages/ThreatIntelPage";
import EmailSecurityDashboardPage from "./pages/EmailSecurity/EmailSecurityDashboardPage";
import EmailSecuritySettingsPage from "./pages/EmailSecurity/EmailSecuritySettingsPage";

function ProtectedRoute({ children }: { children: React.ReactElement }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div style={{ padding: "2rem", textAlign: "center" }}>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function AdminRoute({ children }: { children: React.ReactElement }) {
  const { user, loading } = useAuth();

  if (loading) {
    return <div style={{ padding: "2rem", textAlign: "center" }}>Loading...</div>;
  }

  if (!user || user.role !== "admin") {
    return <Navigate to="/" replace />;
  }

  return children;
}

function AppContent() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const location = useLocation();
  const { isAuthenticated, loading } = useAuth();
  const isLoginPage = location.pathname === "/login";
  const showChrome = isAuthenticated && !isLoginPage;

  const handleToggleSidebar = () => {
    setIsSidebarOpen((prev) => !prev);
  };

  const handleCloseSidebar = () => {
    setIsSidebarOpen(false);
  };

  return (
    <div className="app-root">
      {showChrome && <Topbar onToggleSidebar={handleToggleSidebar} />}
      <div className="app-body">
        {showChrome && isSidebarOpen && (
          <div
            className="sidebar-backdrop"
            onClick={handleCloseSidebar}
            aria-hidden="true"
          />
        )}
        {showChrome && (
          <Sidebar
            isOpen={isSidebarOpen}
            onToggle={handleToggleSidebar}
            onNavigate={handleCloseSidebar}
          />
        )}
        <main className={!isAuthenticated ? "app-main-fullscreen" : "app-main"}>
          <Routes>
            <Route
              path="/login"
              element={
                isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />
              }
            />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/siem"
              element={
                <ProtectedRoute>
                  <SiemPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/edr"
              element={
                <ProtectedRoute>
                  <EdrPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/ioc-bioc"
              element={
                <ProtectedRoute>
                  <IocBiocPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/sandbox"
              element={
                <ProtectedRoute>
                  <SandboxPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/alerts"
              element={
                <ProtectedRoute>
                  <AlertsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/endpoints"
              element={
                <ProtectedRoute>
                  <EndpointsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/software-inventory"
              element={
                <ProtectedRoute>
                  <SoftwareInventoryPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/alerts/:alertId"
              element={
                <ProtectedRoute>
                  <AlertDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/analytics-rules"
              element={
                <ProtectedRoute>
                  <AnalyticsRulesPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/correlation-rules"
              element={
                <ProtectedRoute>
                  <CorrelationRulesPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/events"
              element={
                <ProtectedRoute>
                  <EventsExplorerPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/advanced-search"
              element={
                <ProtectedRoute>
                  <AdvancedSearchPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/handover"
              element={
                <ProtectedRoute>
                  <HandoverPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/workplans"
              element={
                <ProtectedRoute>
                  <WorkplansPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/email-protection"
              element={
                <ProtectedRoute>
                  <EmailProtectionPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/email-security"
              element={
                <ProtectedRoute>
                  <EmailSecurityDashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/email-security/settings"
              element={
                <ProtectedRoute>
                  <EmailSecuritySettingsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/threat-intel"
              element={
                <ProtectedRoute>
                  <ThreatIntelPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <ProfilePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/users"
              element={
                <AdminRoute>
                  <UserManagementPage />
                </AdminRoute>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
