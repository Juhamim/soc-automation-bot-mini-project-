import { Outlet, Link, useLocation } from "react-router";
import {
  Bot,
  LayoutDashboard,
  Bell,
  FileText,
  Shield,
  BookOpen,
  Settings as SettingsIcon,
  LogOut,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useWebSocket } from "../hooks/useWebSocket";
import { Toaster } from "sonner";

const navItems = [
  { path: "/", label: "Dashboard", icon: LayoutDashboard },
  { path: "/alerts", label: "Alerts", icon: Bell },
  { path: "/incident-reports", label: "Incident Reports", icon: FileText },
  { path: "/threat-intelligence", label: "Threat Intelligence", icon: Shield },
  { path: "/playbooks", label: "Playbooks", icon: BookOpen },
  { path: "/settings", label: "Settings", icon: SettingsIcon },
];

export function Layout() {
  const location = useLocation();
  const { user, logout } = useAuth();

  // Initialize the global WebSocket listener
  useWebSocket();

  return (
    <div className="relative flex h-screen min-h-screen overflow-hidden bg-slate-950 text-slate-100">
      {/* Ambient background */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(56,189,248,0.18),transparent_55%),radial-gradient(circle_at_bottom,_rgba(129,140,248,0.22),transparent_55%)]" />
      <div className="pointer-events-none absolute inset-0 opacity-30">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#020617_1px,transparent_1px)] bg-[size:40px_40px]" />
      </div>

      <div className="relative z-10 flex h-full w-full">
        {/* Sidebar */}
        <aside className="w-72 bg-slate-900/70 border-r border-slate-800/60 flex flex-col backdrop-blur-xl shadow-[0_0_35px_rgba(15,23,42,0.9)]">
          {/* Logo */}
          <div className="p-6 border-b border-slate-800/60">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-sky-500 via-indigo-500 to-purple-500 shadow-lg shadow-sky-500/40">
                  <div className="absolute inset-1 rounded-xl bg-slate-950/60 backdrop-blur-md" />
                  <Bot className="relative z-10 h-5 w-5 text-sky-100" />
                </div>
                <div className="flex flex-col">
                  <span className="text-sm font-semibold tracking-wide text-slate-100">
                    SOC Automation Bot
                  </span>
                  <span className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">
                    LIVE SOC CONSOLE
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4">
            <ul className="space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <li key={item.path}>
                    <Link
                      to={item.path}
                      className={`group relative flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                        isActive
                          ? "bg-gradient-to-r from-sky-500/80 via-indigo-500/80 to-purple-500/80 text-white shadow-lg shadow-sky-500/30"
                          : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/70"
                      }`}
                    >
                      <span
                        className={`h-1.5 w-1.5 rounded-full ${
                          isActive ? "bg-emerald-300" : "bg-slate-600 group-hover:bg-slate-300"
                        }`}
                      />
                      <Icon className="h-4 w-4" />
                      <span>{item.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>

          {/* User Profile */}
          <div className="border-t border-slate-800/60 p-4">
            <div className="flex items-center gap-3 px-2">
              <div className="relative flex h-10 w-10 items-center justify-center overflow-hidden rounded-full bg-slate-800/80 ring-1 ring-slate-700/70">
                <div className="absolute inset-0 bg-gradient-to-br from-sky-500/10 via-indigo-500/10 to-purple-500/10" />
                <span className="relative z-10 text-sm font-semibold text-slate-50">
                  {user?.username ? user.username.substring(0, 2).toUpperCase() : "AD"}
                </span>
              </div>
              <div className="flex-1 overflow-hidden">
                <div className="truncate text-sm font-medium text-slate-50">
                  {user?.username || "admin"}
                </div>
                <div className="truncate text-xs font-medium uppercase tracking-wide text-slate-500">
                  {user?.role || "SOC Analyst"}
                </div>
              </div>
              <button
                onClick={logout}
                className="group rounded-lg p-2 transition-colors hover:bg-slate-800/80"
                title="Logout"
              >
                <LogOut className="h-4 w-4 text-slate-400 transition-colors group-hover:text-red-400" />
              </button>
            </div>
          </div>
        </aside>

        {/* Main Content & Global Toast Container */}
        <main className="flex-1 overflow-auto">
          <Toaster theme="dark" position="top-right" richColors />
          <Outlet />
        </main>
      </div>
    </div>
  );
}
