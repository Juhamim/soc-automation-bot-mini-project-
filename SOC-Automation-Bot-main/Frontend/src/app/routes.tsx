import { createBrowserRouter, Navigate, Outlet } from "react-router";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { Alerts } from "./pages/Alerts";
import { IncidentReports } from "./pages/IncidentReports";
import { ThreatIntelligence } from "./pages/ThreatIntelligence";
import { Playbooks } from "./pages/Playbooks";
import { Settings } from "./pages/Settings";
import Login from "./pages/Login";
import { AuthProvider, useAuth } from "./context/AuthContext";

const ProtectedRoute = () => {
  const { user, isLoading } = useAuth();
  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-blue-500 text-xl">Loading...</div>
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  return <Outlet />;
};

const AuthWrapper = () => (
  <AuthProvider>
    <Outlet />
  </AuthProvider>
);

export const router = createBrowserRouter([
  {
    element: <AuthWrapper />,
    children: [
      { path: "/login", element: <Login /> },
      {
        path: "/",
        element: <ProtectedRoute />,
        children: [
          {
            element: <Layout />,
            children: [
              { index: true, Component: Dashboard },
              { path: "alerts", Component: Alerts },
              { path: "incident-reports", Component: IncidentReports },
              { path: "threat-intelligence", Component: ThreatIntelligence },
              { path: "playbooks", Component: Playbooks },
              { path: "settings", Component: Settings },
            ],
          }
        ],
      },
    ],
  },
]);
