import { Suspense, lazy, useEffect, useState, type ComponentType } from "react";
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
import InventoryPage from "./pages/Inventory/InventoryPage";
import AssetInventoryDetailPage from "./pages/Inventory/AssetInventoryDetailPage";
import VulnerabilitiesPage from "./pages/VulnerabilitiesPage";
import WorkplansPage from "./pages/WorkplansPage";
import WorkplanDetailPage from "./pages/WorkplanDetailPage";
import EmailProtectionPage from "./pages/EmailProtectionPage";
import ThreatIntelPage from "./pages/ThreatIntelPage";
import RuleLibraryPage from "./pages/RuleLibraryPage";
import NetworkSecurityOverviewPage from "./pages/NetworkSecurity/NetworkSecurityOverviewPage";
import NetworkSecurityEventsPage from "./pages/NetworkSecurity/NetworkSecurityEventsPage";
import NetworkSecurityDetectionsPage from "./pages/NetworkSecurity/NetworkSecurityDetectionsPage";
import NetworkSecuritySensorsPage from "./pages/NetworkSecurity/NetworkSecuritySensorsPage";
import NetworkSecurityActionsPage from "./pages/NetworkSecurity/NetworkSecurityActionsPage";
import EmailSecurityDashboardPage from "./pages/EmailSecurity/EmailSecurityDashboardPage";
import EmailSecuritySettingsPage from "./pages/EmailSecurity/EmailSecuritySettingsPage";
import EmailThreatIntelPage from "./pages/EmailSecurity/EmailThreatIntelPage";
import PasswordGuardPage from "./pages/PasswordGuard/PasswordGuardPage";
import IntelligenceDashboardPage from "./pages/Intelligence/IntelligenceDashboardPage";
import IntelligenceSearchPage from "./pages/Intelligence/IntelligenceSearchPage";
import IntelligenceEntityPage from "./pages/Intelligence/IntelligenceEntityPage";
import IntelligenceGraphPage from "./pages/Intelligence/IntelligenceGraphPage";
import IntelligenceAttackPage from "./pages/Intelligence/IntelligenceAttackPage";
import IntelligenceIndicatorsPage from "./pages/Intelligence/IntelligenceIndicatorsPage";
import IntelligenceReportsPage from "./pages/Intelligence/IntelligenceReportsPage";
import IntelligenceCasesPage from "./pages/Intelligence/IntelligenceCasesPage";
import IntelligencePlaybooksPage from "./pages/Intelligence/IntelligencePlaybooksPage";
import IntelligenceConnectorsPage from "./pages/Intelligence/IntelligenceConnectorsPage";
import IncidentsPage from "./pages/Incidents/IncidentsPage";
import IncidentDetailPage from "./pages/Incidents/IncidentDetailPage";
import { ConfirmProvider } from "./components/common/ConfirmDialog";
import { DebugPanel } from "./components/common/DebugPanel";
import { ErrorBoundary } from "./components/common/ErrorBoundary";
import { LoadingState } from "./components/common/LoadingState";
import { ToastProvider } from "./components/common/ToastProvider";
import { isOtUiEnabled } from "./lib/featureFlags";

const OTOverviewPage = lazy(() => import("./pages/OT/OverviewPage"));
const OTAssetsPage = lazy(() => import("./pages/OT/AssetsPage"));
const OTCommunicationsPage = lazy(() => import("./pages/OT/CommunicationsPage"));
const OTDetectionsPage = lazy(() => import("./pages/OT/DetectionsPage"));
const OTSensorsPage = lazy(() => import("./pages/OT/SensorsPage"));
const OTPcapPage = lazy(() => import("./pages/OT/PcapPage"));

function ProtectedRoute({ children }: { children: React.ReactElement }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <LoadingState message="Loading session…" />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function AdminRoute({ children }: { children: React.ReactElement }) {
  const { user, loading } = useAuth();

  if (loading) {
    return <LoadingState message="Loading session…" />;
  }

  if (!user || user.role !== "admin") {
    return <Navigate to="/" replace />;
  }

  return children;
}

function AppContent() {
  const [theme, setTheme] = useState<"dark" | "light">(() => {
    if (typeof window === "undefined") {
      return "dark";
    }
    const stored = window.localStorage.getItem("eventsec-theme");
    return stored === "light" ? "light" : "dark";
  });
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const location = useLocation();
  const { isAuthenticated, loading } = useAuth();
  const otUiEnabled = isOtUiEnabled();
  const isLoginPage = location.pathname === "/login";
  const isIntelligenceRoute = location.pathname.startsWith("/intelligence");
  const isIntelligenceFullChrome =
    location.pathname.startsWith("/intelligence/dashboard") ||
    location.pathname.startsWith("/intelligence/search");
  const showChrome =
    isAuthenticated && !isLoginPage && (!isIntelligenceRoute || isIntelligenceFullChrome);
  const mainClassName =
    !isAuthenticated || isLoginPage || (isIntelligenceRoute && !isIntelligenceFullChrome)
      ? "app-main-fullscreen"
      : "app-main";

  const handleToggleSidebar = () => {
    setIsSidebarOpen((prev) => !prev);
  };

  const handleCloseSidebar = () => {
    setIsSidebarOpen(false);
  };

  const handleToggleTheme = () => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  };

  useEffect(() => {
    const root = document.documentElement;
    root.setAttribute("data-theme", theme);
    root.style.colorScheme = theme;
    window.localStorage.setItem("eventsec-theme", theme);
  }, [theme]);

  const renderOtRoute = (Component: ComponentType) => (
    <ProtectedRoute>
      <Suspense fallback={<LoadingState message="Loading OT module…" />}>
        <Component />
      </Suspense>
    </ProtectedRoute>
  );

  return (
    <div className="app-root">
      {showChrome && (
        <Topbar
          onToggleSidebar={handleToggleSidebar}
          theme={theme}
          onToggleTheme={handleToggleTheme}
        />
      )}
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
        <main className={mainClassName}>
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
              path="/inventory"
              element={
                <ProtectedRoute>
                  <InventoryPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/inventory/assets/:assetId"
              element={
                <ProtectedRoute>
                  <AssetInventoryDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/vulnerabilities"
              element={
                <ProtectedRoute>
                  <VulnerabilitiesPage />
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
              path="/detections/rules"
              element={
                <ProtectedRoute>
                  <RuleLibraryPage />
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
              path="/network-security/overview"
              element={
                <ProtectedRoute>
                  <NetworkSecurityOverviewPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/network-security/events"
              element={
                <ProtectedRoute>
                  <NetworkSecurityEventsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/network-security/detections"
              element={
                <ProtectedRoute>
                  <NetworkSecurityDetectionsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/network-security/sensors"
              element={
                <ProtectedRoute>
                  <NetworkSecuritySensorsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/network-security/actions"
              element={
                <ProtectedRoute>
                  <NetworkSecurityActionsPage />
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
              path="/incidents"
              element={
                <ProtectedRoute>
                  <IncidentsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/incidents/:incidentId"
              element={
                <ProtectedRoute>
                  <IncidentDetailPage />
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
              path="/workplans/:workplanId"
              element={
                <ProtectedRoute>
                  <WorkplanDetailPage />
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
              path="/email-security/threat-intel"
              element={
                <ProtectedRoute>
                  <EmailThreatIntelPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/passwordguard"
              element={
                <ProtectedRoute>
                  <PasswordGuardPage />
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
              path="/intelligence/dashboard"
              element={
                <ProtectedRoute>
                  <IntelligenceDashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/intelligence/search"
              element={
                <ProtectedRoute>
                  <IntelligenceSearchPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/intelligence/entity/:id"
              element={
                <ProtectedRoute>
                  <IntelligenceEntityPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/intelligence/graph"
              element={
                <ProtectedRoute>
                  <IntelligenceGraphPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/intelligence/attack"
              element={
                <ProtectedRoute>
                  <IntelligenceAttackPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/intelligence/indicators"
              element={
                <ProtectedRoute>
                  <IntelligenceIndicatorsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/intelligence/reports"
              element={
                <ProtectedRoute>
                  <IntelligenceReportsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/intelligence/cases"
              element={
                <ProtectedRoute>
                  <IntelligenceCasesPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/intelligence/playbooks"
              element={
                <ProtectedRoute>
                  <IntelligencePlaybooksPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/intelligence/connectors"
              element={
                <ProtectedRoute>
                  <IntelligenceConnectorsPage />
                </ProtectedRoute>
              }
            />
            {otUiEnabled && (
              <>
                <Route path="/ot/overview" element={renderOtRoute(OTOverviewPage)} />
                <Route path="/ot/assets" element={renderOtRoute(OTAssetsPage)} />
                <Route path="/ot/communications" element={renderOtRoute(OTCommunicationsPage)} />
                <Route path="/ot/detections" element={renderOtRoute(OTDetectionsPage)} />
                <Route path="/ot/sensors" element={renderOtRoute(OTSensorsPage)} />
                <Route path="/ot/pcap" element={renderOtRoute(OTPcapPage)} />
              </>
            )}
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
        <DebugPanel />
      </div>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <ConfirmProvider>
          <ErrorBoundary>
            <AppContent />
          </ErrorBoundary>
        </ConfirmProvider>
      </ToastProvider>
    </AuthProvider>
  );
}

export default App;
