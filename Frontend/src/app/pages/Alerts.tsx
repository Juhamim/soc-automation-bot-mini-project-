import { useState, useEffect, useCallback } from "react";
import { Search, Filter, Download, ChevronDown } from "lucide-react";
import { fetchAlerts } from "../../api/client";


export function Alerts() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSeverity, setSelectedSeverity] = useState("All");
  const [selectedStatus, setSelectedStatus] = useState("All");
  const [dateStart, setDateStart] = useState("");
  const [dateEnd, setDateEnd] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [totalAlerts, setTotalAlerts] = useState(0);

  const loadAlerts = useCallback(async () => {
    try {
      const params: Record<string, string> = { page: String(currentPage), limit: "20" };
      if (selectedSeverity !== "All") params.severity = selectedSeverity.toLowerCase();
      if (selectedStatus !== "All") params.status = selectedStatus.toLowerCase();
      if (dateStart) params.date_start = new Date(dateStart).toISOString();
      if (dateEnd) params.date_end = new Date(dateEnd).toISOString();
      // search query isn't directly supported by backend yet, we'll filter locally later if needed
      const data = await fetchAlerts(params);
      setAlerts(data.alerts);
      setTotalAlerts(data.total);
    } catch (error) {
      console.error("Error loading alerts:", error);
    }
  }, [currentPage, selectedSeverity, selectedStatus]);

  useEffect(() => {
    loadAlerts();
  }, [loadAlerts]);

  const handleExportTxt = () => {
    const rows = filteredAlerts.length ? filteredAlerts : alerts;
    if (!rows.length) return;
    const lines = rows.map((a) => {
      const id = a.id ? String(a.id) : "";
      const ts = a.created_at ? new Date(a.created_at).toLocaleString() : "";
      return [
        `ID: ${id}`,
        `Time: ${ts}`,
        `Source IP: ${a.source_ip || "N/A"}`,
        `Type: ${a.source_integration || ""}`,
        `Severity: ${a.severity || ""}`,
        `Status: ${a.status || ""}`,
        "---",
      ].join("\n");
    });
    const content = ["Alerts Export", "================", "", ...lines].join("\n");
    const blob = new Blob([content], { type: "text/plain;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "alerts.txt";
    link.click();
    URL.revokeObjectURL(url);
  };

  const filteredAlerts = alerts.filter((alert) => {
    if (!searchQuery) return true;
    const ip = alert.source_ip || "";
    const type = alert.source_integration || "";
    const ext_id = alert.external_id || "";
    return ip.toLowerCase().includes(searchQuery.toLowerCase()) ||
      type.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ext_id.toLowerCase().includes(searchQuery.toLowerCase());
  });

  // DB alert statuses: 'New', 'InProgress', 'Closed', 'FalsePositive'
  const openCount = alerts.filter(a => ['new', 'inprogress'].includes(a.status?.toLowerCase())).length;
  const resolvedCount = alerts.filter(a => ['closed', 'falsepositive'].includes(a.status?.toLowerCase())).length;
  const criticalCount = alerts.filter(a => ['critical', 'high'].includes(a.severity?.toLowerCase())).length;
  const resolutionRate = totalAlerts > 0 ? Math.round((resolvedCount / totalAlerts) * 100) : 0;

  return (
    <div className="p-8 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-semibold text-white mb-2">Alerts</h1>
          <p className="text-slate-400">Monitor and manage security alerts</p>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={handleExportTxt}
            className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-4 gap-6 mb-8">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="text-slate-400 text-sm mb-2">Total Alerts</div>
          <div className="text-white text-3xl font-semibold">{totalAlerts}</div>
          <div className="text-slate-400 text-sm mt-2">All time</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="text-slate-400 text-sm mb-2">Critical/High</div>
          <div className="text-white text-3xl font-semibold">{criticalCount}</div>
          <div className="text-red-400 text-sm mt-2">Active severity level</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="text-slate-400 text-sm mb-2">Closed</div>
          <div className="text-white text-3xl font-semibold">{resolvedCount}</div>
          <div className="text-green-400 text-sm mt-2">{resolutionRate}% closure rate</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="text-slate-400 text-sm mb-2">Active Open</div>
          <div className="text-white text-3xl font-semibold">{openCount}</div>
          <div className="text-orange-400 text-sm mt-2">Requires attention</div>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-6">
        <div className="flex items-center gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              placeholder="Search by IP address, type, or ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 text-white pl-10 pr-4 py-2.5 rounded-lg focus:outline-none focus:border-blue-500"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-slate-400" />
            <select
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value)}
              className="bg-slate-800 border border-slate-700 text-white px-4 py-2.5 rounded-lg focus:outline-none focus:border-blue-500"
            >
              <option value="All">All Severities</option>
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="bg-slate-800 border border-slate-700 text-white px-4 py-2.5 rounded-lg focus:outline-none focus:border-blue-500"
            >
              <option value="All">All Statuses</option>
              <option value="Open">Open</option>
              <option value="In Progress">In Progress</option>
              <option value="Resolved">Resolved</option>
              <option value="Mitigated">Mitigated</option>
            </select>
            <input
              type="date"
              value={dateStart}
              onChange={(e) => setDateStart(e.target.value)}
              className="bg-slate-800 border border-slate-700 text-white px-3 py-2.5 rounded-lg text-sm"
            />
            <input
              type="date"
              value={dateEnd}
              onChange={(e) => setDateEnd(e.target.value)}
              className="bg-slate-800 border border-slate-700 text-white px-3 py-2.5 rounded-lg text-sm"
            />
            <button
              onClick={() => {
                setCurrentPage(1);
                loadAlerts();
              }}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2.5 rounded-lg text-sm transition-colors"
            >
              Apply Filters
            </button>
          </div>
        </div>
      </div>

      {/* Alerts Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-800 border-b border-slate-700">
              <tr>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">
                  <div className="flex items-center gap-2">
                    Alert ID
                    <ChevronDown className="w-4 h-4" />
                  </div>
                </th>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">
                  <div className="flex items-center gap-2">
                    Timestamp
                    <ChevronDown className="w-4 h-4" />
                  </div>
                </th>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">Source IP</th>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">Type</th>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">
                  <div className="flex items-center gap-2">
                    Severity
                    <ChevronDown className="w-4 h-4" />
                  </div>
                </th>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">Status</th>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">Assignee</th>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredAlerts.length > 0 ? (
                filteredAlerts.map((alert) => {
                  const severity = alert.severity?.toLowerCase() || "unknown";
                  const status = alert.status?.toLowerCase() || "unknown";
                  return (
                    <tr key={alert.id} className="border-b border-slate-800 hover:bg-slate-800/50 transition-colors">
                      <td className="py-4 px-6">
                        <span className="text-blue-400 font-mono text-sm" title={alert.id}>{alert.id.substring(0, 8)}...</span>
                      </td>
                      <td className="py-4 px-6 text-slate-300 text-sm">{new Date(alert.created_at).toLocaleString()}</td>
                      <td className="py-4 px-6 text-slate-300 text-sm font-mono">{alert.source_ip || "N/A"}</td>
                      <td className="py-4 px-6 text-slate-300 text-sm">{alert.source_integration}</td>
                      <td className="py-4 px-6">
                        <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium ${severity === "critical" ? "bg-purple-600/20 text-purple-400" :
                          severity === "high" ? "bg-red-600/20 text-red-400" :
                            severity === "medium" ? "bg-orange-600/20 text-orange-400" :
                              "bg-yellow-600/20 text-yellow-400"
                          }`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${severity === "critical" ? "bg-purple-400" :
                            severity === "high" ? "bg-red-400" :
                              severity === "medium" ? "bg-orange-400" :
                                "bg-yellow-400"
                            }`}></span>
                          {alert.severity}
                        </span>
                      </td>
                      <td className="py-4 px-6">
                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${["resolved", "mitigated"].includes(status) ? "bg-green-600/20 text-green-400" :
                          ["in progress", "investigating"].includes(status) ? "bg-blue-600/20 text-blue-400" :
                            "bg-slate-600/20 text-slate-400"
                          }`}>
                          {alert.status}
                        </span>
                      </td>
                      <td className="py-4 px-6 text-slate-300 text-sm">Unassigned</td>
                      <td className="py-4 px-6">
                        <button className="text-blue-400 hover:text-blue-300 text-sm font-medium">
                          View Details
                        </button>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-500">
                    No alerts found for the selected filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between px-6 py-4 bg-slate-800 border-t border-slate-700">
          <div className="text-slate-400 text-sm">
            Showing {filteredAlerts.length} of {totalAlerts || filteredAlerts.length} alerts
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm transition-colors disabled:opacity-50"
            >
              Previous
            </button>
            <span className="text-white text-sm">Page {currentPage}</span>
            <button
              onClick={() => setCurrentPage(currentPage + 1)}
              disabled={alerts.length < 20}
              className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm transition-colors disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
