import { useState, useEffect } from "react";
import { Info, Flame, AlertTriangle, Clock, ChevronLeft, ChevronRight, ArrowUp, ArrowDown } from "lucide-react";
import { PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { fetchMetrics, fetchAlerts, fetchThreatIntel } from "../../api/client";

import { useMemo } from "react";


export function Dashboard() {
  const [activeTab, setActiveTab] = useState("All");
  const tabs = ["All", "High", "Medium", "Low", "Status"];

  const [metrics, setMetrics] = useState<any>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [threatIntel, setThreatIntel] = useState<any[]>([]);

  const highAlertsCount = useMemo(() => {
    return alerts.filter(a => ["high", "critical"].includes(a.severity?.toLowerCase())).length;
  }, [alerts]);

  const filteredRecentAlerts = useMemo(() => {
    let filtered = alerts;
    if (activeTab !== "All") {
      if (activeTab === "High") {
        filtered = alerts.filter(a => ["high", "critical"].includes(a.severity?.toLowerCase()));
      } else if (activeTab === "Medium") {
        filtered = alerts.filter(a => a.severity?.toLowerCase() === "medium");
      } else if (activeTab === "Low") {
        filtered = alerts.filter(a => a.severity?.toLowerCase() === "low");
      } else if (activeTab === "Status") {
        // Just show Open / In Progress for 'Status' tab
        filtered = alerts.filter(a => ["open", "in progress", "investigating"].includes(a.status?.toLowerCase()));
      }
    }
    return filtered.slice(0, 10); // Show max 10
  }, [alerts, activeTab]);

  useEffect(() => {
    async function loadDashboardData() {
      try {
        const metricsData = await fetchMetrics();
        setMetrics(metricsData);

        // Fetch recent alerts for the table
        const alertsData = await fetchAlerts({ limit: "50" }); // increase limit so we can aggregate charts
        setAlerts(alertsData.alerts || []);

        const threatData = await fetchThreatIntel(1, 5);
        setThreatIntel(threatData.threats || []);
      } catch (error) {
        console.error("Error loading dashboard data:", error);
      }
    }
    loadDashboardData();

    // Listen to the global WebSocket hook events to re-hydrate the frontend
    const handleNewAlert = () => {
      console.log("Real-time WS update received! Hard refreshing dashboard...");
      loadDashboardData();
    };

    window.addEventListener("new_alert", handleNewAlert);
    return () => window.removeEventListener("new_alert", handleNewAlert);
  }, []);

  const incidentTrendData = useMemo(() => {
    const counts: Record<string, any> = {};
    alerts.forEach(a => {
      const d = new Date(a.created_at).toLocaleDateString('default', { month: 'short', day: 'numeric' });
      if (!counts[d]) counts[d] = { date: d, high: 0, medium: 0, low: 0 };
      const sev = a.severity?.toLowerCase() || 'low';
      if (sev === 'critical' || sev === 'high') counts[d].high += 1;
      else if (sev === 'medium') counts[d].medium += 1;
      else counts[d].low += 1;
    });
    return Object.values(counts);
  }, [alerts]);

  const playbookExecutionData = useMemo(() => {
    return alerts.flatMap(a => (a.action_logs || []).map((log: any) => ({
      timestamp: new Date(log.executed_at).toLocaleDateString(),
      playbook: log.action_name,
      action: log.action_name,
      status: log.status,
      statusColor: log.status.toLowerCase() === 'success' || log.status.toLowerCase() === 'completed' ? 'green' : 'orange'
    })));
  }, [alerts]);

  // Compute statCards from backend metrics
  const statCards = metrics ? [
    { label: "Total Alerts", value: String(metrics.total_alerts), icon: Info, color: "blue" },
    { label: "High/Crit Alerts", value: String((metrics.by_severity?.High || 0) + (metrics.by_severity?.Critical || 0)), icon: Flame, color: "red" },
    { label: "Active Open", value: String(metrics.by_status?.Open || 0 + metrics.by_status?.InProgress || 0), icon: AlertTriangle, color: "orange" },
    { label: "Resolved", value: String(metrics.by_status?.Closed || 0), icon: Clock, color: "green" },
  ] : [
    { label: "Total Alerts", value: "--", icon: Info, color: "blue" },
    { label: "High Severity", value: "--", icon: Flame, color: "red" },
    { label: "Active Incidents", value: "--", icon: AlertTriangle, color: "orange" },
    { label: "Resolved", value: "--", icon: Clock, color: "green" },
  ];

  // Compute severity distribution
  const total = metrics?.total_alerts || 1;
  const severityData = [
    { name: "Low", value: metrics?.by_severity?.Low || 0, color: "#FFA726" },
    { name: "Medium", value: metrics?.by_severity?.Medium || 0, color: "#FB8C00" },
    { name: "High/Crit", value: (metrics?.by_severity?.High || 0) + (metrics?.by_severity?.Critical || 0), color: "#EF5350" },
  ];

  return (
    <div className="p-8 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-semibold text-white">Dashboard</h1>
        <div className="flex items-center gap-4">
          <div className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-slate-300 text-sm">
            {new Date().toLocaleDateString()}
          </div>
          <div className="w-10 h-10 bg-slate-700 rounded-full flex items-center justify-center">
            <span className="text-white text-sm font-medium">AD</span>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-6 mb-8">
        {statCards.map((card, index) => {
          const Icon = card.icon;
          const iconColors = {
            blue: "bg-blue-600",
            red: "bg-red-600",
            orange: "bg-orange-600",
            green: "bg-green-600",
          };
          return (
            <div key={index} className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <div className="flex items-start gap-4">
                <div className={`w-10 h-10 ${iconColors[card.color as keyof typeof iconColors]} rounded-lg flex items-center justify-center`}>
                  <Icon className="w-5 h-5 text-white" />
                </div>
                <div>
                  <div className="text-slate-400 text-sm mb-1">{card.label}</div>
                  <div className="text-white text-3xl font-semibold">{card.value}</div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-2 gap-6 mb-8">
        {/* Alerts by Severity */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white">Alerts by Severity</h2>
            <div className="flex items-center gap-2">
              <button className="p-1 hover:bg-slate-800 rounded">
                <ChevronLeft className="w-5 h-5 text-slate-400" />
              </button>
              <button className="p-1 hover:bg-slate-800 rounded">
                <ChevronRight className="w-5 h-5 text-slate-400" />
              </button>
            </div>
          </div>
          <div className="flex items-center">
            <div className="flex-1">
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={severityData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {severityData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex-1">
              <div className="space-y-4">
                <div className="flex items-center gap-3 text-slate-300 text-sm">
                  <div className="w-4 h-4 bg-[#FFA726] rounded"></div>
                  <span>Low</span>
                  <span className="ml-auto">44%</span>
                </div>
                <div className="flex items-center gap-3 text-slate-300 text-sm">
                  <div className="w-4 h-4 bg-[#FB8C00] rounded"></div>
                  <span>Medium</span>
                  <span className="ml-auto">35%</span>
                </div>
                <div className="flex items-center gap-3 text-slate-300 text-sm">
                  <div className="w-4 h-4 bg-[#EF5350] rounded"></div>
                  <span>High</span>
                  <span className="ml-auto">23%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Alerts */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white">Recent Alerts</h2>
            <button className="text-blue-400 text-sm hover:text-blue-300">View All →</button>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 mb-4">
            {tabs.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${activeTab === tab
                  ? "bg-slate-700 text-white"
                  : "text-slate-400 hover:bg-slate-800 hover:text-white"
                  }`}
              >
                {tab}
                {tab === "High" && highAlertsCount > 0 && <span className="ml-1 bg-red-600 text-white text-xs px-1.5 py-0.5 rounded-full">{highAlertsCount}</span>}
              </button>
            ))}
          </div>

          {/* Table */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-slate-400 text-xs">
                  <th className="text-left py-2 font-medium">Timestamp</th>
                  <th className="text-left py-2 font-medium">Type</th>
                  <th className="text-left py-2 font-medium">Severity</th>
                  <th className="text-left py-2 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredRecentAlerts.map((alert) => (
                  <tr key={alert.id} className="border-t border-slate-800">
                    <td className="py-3 text-slate-300 text-sm">{new Date(alert.created_at).toLocaleString()}</td>
                    <td className="py-3">
                      <span className="inline-flex items-center gap-2 text-slate-300 text-sm">
                        <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                        {alert.source_integration}
                      </span>
                    </td>
                    <td className="py-3">
                      <span className={`inline-flex items-center gap-1 text-sm ${["high", "critical"].includes((alert.severity || "").toLowerCase()) ? "text-red-400" :
                        (alert.severity || "").toLowerCase() === "medium" ? "text-orange-400" :
                          "text-yellow-400"
                        }`}>
                        {["high", "critical"].includes((alert.severity || "").toLowerCase()) && "🔴"}
                        {(alert.severity || "").toLowerCase() === "medium" && "🔥"}
                        {(alert.severity || "").toLowerCase() === "low" && "🔥"}
                        {alert.severity || "Unknown"}
                      </span>
                    </td>
                    <td className="py-3">
                      <span className={`px-3 py-1 rounded-full text-xs ${alert.status === "resolved" ? "bg-green-600/20 text-green-400" :
                        "bg-blue-600/20 text-blue-400"
                        }`}>
                        {alert.status}
                      </span>
                    </td>
                  </tr>
                ))}
                {filteredRecentAlerts.length === 0 && (
                  <tr>
                    <td colSpan={4} className="py-4 text-center text-slate-500">
                      No alerts found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Second Row Charts */}
      <div className="grid grid-cols-2 gap-6 mb-8">
        {/* Incident Summary Line Chart */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white">Incident Summary</h2>
            <button className="text-blue-400 text-sm hover:text-blue-300">View All →</button>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={incidentTrendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="date" stroke="#64748b" style={{ fontSize: '12px' }} />
              <YAxis stroke="#64748b" style={{ fontSize: '12px' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
              <Legend />
              <Line type="monotone" dataKey="high" stroke="#EF5350" strokeWidth={2} dot={{ fill: '#EF5350' }} />
              <Line type="monotone" dataKey="medium" stroke="#FB8C00" strokeWidth={2} dot={{ fill: '#FB8C00' }} />
              <Line type="monotone" dataKey="low" stroke="#64B5F6" strokeWidth={2} dot={{ fill: '#64B5F6' }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Playbook Execution */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white">Playbook Execution</h2>
            <button className="text-blue-400 text-sm hover:text-blue-300">View All →</button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-slate-400 text-xs">
                  <th className="text-left py-2 font-medium">Timestamp</th>
                  <th className="text-left py-2 font-medium">Playbook</th>
                  <th className="text-left py-2 font-medium">Action Taken</th>
                  <th className="text-left py-2 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {playbookExecutionData.slice(0, 5).map((row, index) => (
                  <tr key={index} className="border-t border-slate-800">
                    <td className="py-3 text-slate-300 text-sm">{row.timestamp}</td>
                    <td className="py-3 text-slate-300 text-sm">{row.playbook}</td>
                    <td className="py-3">
                      <span className="inline-flex items-center gap-2 text-slate-300 text-sm">
                        <span className={`w-2 h-2 rounded-full ${row.statusColor === "orange" ? "bg-orange-500" :
                          row.statusColor === "blue" ? "bg-blue-500" : "bg-green-500"
                          }`}></span>
                        {row.action}
                      </span>
                    </td>
                    <td className="py-3">
                      <span className={`px-3 py-1 rounded-full text-xs ${row.status === "Completed" ? "bg-green-600/20 text-green-400" :
                        "bg-orange-600/20 text-orange-400"
                        }`}>
                        {row.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-2 gap-6">
        {/* Incident Summary Bar Chart */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white">Incident Summary</h2>
            <button className="text-blue-400 text-sm hover:text-blue-300">View All →</button>
          </div>
          <div className="flex items-center gap-8 mb-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-[#EF5350] rounded"></div>
              <span className="text-slate-300">High</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-[#FB8C00] rounded"></div>
              <span className="text-slate-300">120 . Medium</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-[#64B5F6] rounded"></div>
              <span className="text-slate-300">Low</span>
            </div>
          </div>
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <span className="text-2xl font-semibold text-white w-8">7</span>
              <ArrowUp className="w-5 h-5 text-orange-400" />
            </div>
            <div className="flex items-center gap-4">
              <span className="text-2xl font-semibold text-white w-8">13</span>
              <ArrowUp className="w-5 h-5 text-green-400" />
            </div>
            <div className="flex items-center gap-4">
              <span className="text-2xl font-semibold text-white w-8">47</span>
              <ArrowDown className="w-5 h-5 text-blue-400" />
            </div>
          </div>
          <ResponsiveContainer width="100%" height={150}>
            <LineChart data={incidentTrendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="date" stroke="#64748b" style={{ fontSize: '10px' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
              <Line type="monotone" dataKey="high" stroke="#EF5350" strokeWidth={2} />
              <Line type="monotone" dataKey="medium" stroke="#FB8C00" strokeWidth={2} />
              <Line type="monotone" dataKey="low" stroke="#64B5F6" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Threat Intelligence Feed */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white">Threat Intelligence Feed</h2>
            <button className="text-blue-400 text-sm hover:text-blue-300">View All →</button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-slate-400 text-xs">
                  <th className="text-left py-2 font-medium">IP Address</th>
                  <th className="text-left py-2 font-medium">Type</th>
                  <th className="text-left py-2 font-medium">Risk Level</th>
                </tr>
              </thead>
              <tbody>
                {threatIntel.map((row, index) => (
                  <tr key={index} className="border-t border-slate-800">
                    <td className="py-3 text-slate-300 text-sm">{row.indicator_value}</td>
                    <td className="py-3 text-slate-300 text-sm">{row.indicator_type}</td>
                    <td className="py-3">
                      <span className="inline-flex items-center gap-2 text-red-400 text-sm">
                        <span className="w-2 h-2 bg-red-500 rounded-full"></span>
                        {row.risk_level}
                      </span>
                    </td>
                  </tr>
                ))}
                {threatIntel.length === 0 && (
                  <tr>
                    <td colSpan={3} className="py-4 text-center text-slate-500 text-sm">
                      No threat intel found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
