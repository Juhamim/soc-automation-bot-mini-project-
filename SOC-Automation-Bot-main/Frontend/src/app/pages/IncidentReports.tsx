import { useState, useEffect } from "react";
import { Search, Filter, Download, Plus, Calendar, ChevronDown } from "lucide-react";
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { createIncident, fetchIncidents } from "../../api/client";

import { useMemo } from "react";

export function IncidentReports() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSeverity, setSelectedSeverity] = useState("All");
  const [selectedStatus, setSelectedStatus] = useState("All");
  const [dateStart, setDateStart] = useState("");
  const [dateEnd, setDateEnd] = useState("");
  const [incidentsData, setIncidentsData] = useState<any[]>([]);
  const [totalIncidents, setTotalIncidents] = useState(0);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [createError, setCreateError] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [newIncident, setNewIncident] = useState({
    title: "",
    description: "",
    severity: "Medium",
    status: "Open",
    category: "",
    assignee: "",
  });

  useEffect(() => {
    async function loadIncidents() {
      try {
        const params: Record<string, string> = {};
        if (selectedSeverity !== "All") params.severity = selectedSeverity;
        if (selectedStatus !== "All") params.status = selectedStatus;
        if (dateStart) params.date_start = new Date(dateStart).toISOString();
        if (dateEnd) params.date_end = new Date(dateEnd).toISOString();
        const data = await fetchIncidents(1, 100, params);
        setIncidentsData(data.incidents || []);
        setTotalIncidents(data.total || 0);
      } catch (error) {
        console.error("Failed to load incidents", error);
      }
    }
    loadIncidents();
  }, [selectedSeverity, selectedStatus, dateStart, dateEnd]);

  const filteredIncidents = incidentsData.filter((incident) => {
    const matchesSearch = incident.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      incident.id?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesSeverity = selectedSeverity === "All" || incident.severity === selectedSeverity;
    const matchesStatus = selectedStatus === "All" || incident.status === selectedStatus;
    return matchesSearch && matchesSeverity && matchesStatus;
  });

  const categoryData = useMemo(() => {
    const counts: Record<string, number> = {};
    incidentsData.forEach(inc => {
      const cat = inc.category || 'Unknown';
      counts[cat] = (counts[cat] || 0) + 1;
    });
    return Object.entries(counts).map(([category, count]) => ({ category, count }));
  }, [incidentsData]);

  const trendData = useMemo(() => {
    const counts: Record<string, number> = {};
    incidentsData.forEach(inc => {
      if (!inc.created_at) return;
      const date = new Date(inc.created_at);
      const month = date.toLocaleString('default', { month: 'short' });
      counts[month] = (counts[month] || 0) + 1;
    });
    return Object.entries(counts).map(([month, incidents]) => ({ month, incidents }));
  }, [incidentsData]);

  // Calculate dynamic stats
  const openCount = incidentsData.filter(i => i.status === "Open" || i.status === "InProgress").length;
  const resolvedCount = incidentsData.filter(i => i.status === "Resolved").length;
  const averageResolutionHours = useMemo(() => {
    const durations: number[] = [];
    incidentsData.forEach((inc) => {
      if (inc.created_at && inc.resolved_at) {
        const start = new Date(inc.created_at).getTime();
        const end = new Date(inc.resolved_at).getTime();
        if (!Number.isNaN(start) && !Number.isNaN(end) && end > start) {
          const hours = (end - start) / (1000 * 60 * 60);
          durations.push(hours);
        }
      }
    });
    if (!durations.length) return null;
    const avg = durations.reduce((a, b) => a + b, 0) / durations.length;
    return avg.toFixed(1);
  }, [incidentsData]);

  const handleExportTxt = () => {
    const rows = filteredIncidents.length ? filteredIncidents : incidentsData;
    if (!rows.length) return;
    const lines = rows.map((i) => {
      const created = i.created_at ? new Date(i.created_at).toLocaleDateString() : "";
      return [
        `ID: ${i.id}`,
        `Title: ${i.title || ""}`,
        `Category: ${i.category || ""}`,
        `Severity: ${i.severity || ""}`,
        `Status: ${i.status || ""}`,
        `Created: ${created}`,
        `Assignee: ${i.assignee || ""}`,
        "---",
      ].join("\n");
    });
    const content = ["Incidents Export", "================", "", ...lines].join("\n");
    const blob = new Blob([content], { type: "text/plain;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "incidents.txt";
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-8 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-semibold text-white mb-2">Incident Reports</h1>
          <p className="text-slate-400">Track and manage security incidents</p>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={handleExportTxt}
            className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
          <button
            onClick={() => setIsCreateOpen((prev) => !prev)}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            Create Incident
          </button>
        </div>
      </div>

      {isCreateOpen && (
        <div className="mb-6 bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">New Incident</h2>
            <button
              onClick={() => setIsCreateOpen(false)}
              className="text-slate-400 hover:text-slate-200 text-sm"
            >
              Close
            </button>
          </div>
          {createError && (
            <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-xs text-red-300">
              {createError}
            </div>
          )}
          <div className="grid grid-cols-2 gap-4">
            <input
              type="text"
              placeholder="Title"
              value={newIncident.title}
              onChange={(e) => setNewIncident((prev) => ({ ...prev, title: e.target.value }))}
              className="bg-slate-800 border border-slate-700 text-white px-3 py-2 rounded-lg text-sm"
            />
            <input
              type="text"
              placeholder="Category"
              value={newIncident.category}
              onChange={(e) => setNewIncident((prev) => ({ ...prev, category: e.target.value }))}
              className="bg-slate-800 border border-slate-700 text-white px-3 py-2 rounded-lg text-sm"
            />
            <select
              value={newIncident.severity}
              onChange={(e) => setNewIncident((prev) => ({ ...prev, severity: e.target.value }))}
              className="bg-slate-800 border border-slate-700 text-white px-3 py-2 rounded-lg text-sm"
            >
              <option>Critical</option>
              <option>High</option>
              <option>Medium</option>
              <option>Low</option>
              <option>Info</option>
            </select>
            <select
              value={newIncident.status}
              onChange={(e) => setNewIncident((prev) => ({ ...prev, status: e.target.value }))}
              className="bg-slate-800 border border-slate-700 text-white px-3 py-2 rounded-lg text-sm"
            >
              <option>Open</option>
              <option>InProgress</option>
              <option>Resolved</option>
              <option>FalsePositive</option>
            </select>
            <input
              type="text"
              placeholder="Assignee"
              value={newIncident.assignee}
              onChange={(e) => setNewIncident((prev) => ({ ...prev, assignee: e.target.value }))}
              className="bg-slate-800 border border-slate-700 text-white px-3 py-2 rounded-lg text-sm"
            />
            <input
              type="text"
              placeholder="Description"
              value={newIncident.description}
              onChange={(e) => setNewIncident((prev) => ({ ...prev, description: e.target.value }))}
              className="bg-slate-800 border border-slate-700 text-white px-3 py-2 rounded-lg text-sm col-span-2"
            />
          </div>
          <div className="mt-4 flex items-center gap-2">
            <button
              onClick={async () => {
                try {
                  setIsCreating(true);
                  const created = await createIncident(newIncident);
                  setIncidentsData((prev) => [created, ...prev]);
                  setTotalIncidents((prev) => prev + 1);
                  setNewIncident({
                    title: "",
                    description: "",
                    severity: "Medium",
                    status: "Open",
                    category: "",
                    assignee: "",
                  });
                  setCreateError("");
                  setIsCreateOpen(false);
                } catch (err: any) {
                  setCreateError(err?.message || "Failed to create incident");
                } finally {
                  setIsCreating(false);
                }
              }}
              disabled={!newIncident.title || isCreating}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm transition-colors disabled:opacity-60"
            >
              {isCreating ? "Creating..." : "Create Incident"}
            </button>
          </div>
        </div>
      )}

      {/* Stats Row */}
      <div className="grid grid-cols-4 gap-6 mb-8">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="text-slate-400 text-sm mb-2">Total Incidents</div>
          <div className="text-white text-3xl font-semibold">{totalIncidents}</div>
          <div className="text-slate-400 text-sm mt-2">All time</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="text-slate-400 text-sm mb-2">Active Incidents</div>
          <div className="text-white text-3xl font-semibold">{openCount}</div>
          <div className="text-orange-400 text-sm mt-2">Requires attention</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="text-slate-400 text-sm mb-2">Resolved</div>
          <div className="text-white text-3xl font-semibold">{resolvedCount}</div>
          <div className="text-green-400 text-sm mt-2">Historically closed</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="text-slate-400 text-sm mb-2">Avg. Resolution Time</div>
          <div className="text-white text-3xl font-semibold">
            {averageResolutionHours !== null ? `${averageResolutionHours}h` : "--"}
          </div>
          <div className="text-green-400 text-sm mt-2">
            {averageResolutionHours !== null ? "Based on resolved incidents" : "No resolved incidents yet"}
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-2 gap-6 mb-8">
        {/* Incident Trend */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h2 className="text-xl font-semibold text-white mb-6">Incident Trend</h2>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="month" stroke="#64748b" style={{ fontSize: '12px' }} />
              <YAxis stroke="#64748b" style={{ fontSize: '12px' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
              <Line type="monotone" dataKey="incidents" stroke="#3b82f6" strokeWidth={2} dot={{ fill: '#3b82f6', r: 5 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Incidents by Category */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h2 className="text-xl font-semibold text-white mb-6">Incidents by Category</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={categoryData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="category" stroke="#64748b" style={{ fontSize: '11px' }} angle={-45} textAnchor="end" height={80} />
              <YAxis stroke="#64748b" style={{ fontSize: '12px' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
              <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-6">
        <div className="flex items-center gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              placeholder="Search incidents by title or ID..."
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
            </select>
            <button className="flex items-center gap-2 bg-slate-800 border border-slate-700 text-white px-4 py-2.5 rounded-lg hover:bg-slate-700 transition-colors">
              <Calendar className="w-4 h-4" />
              Date Range
            </button>
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
          </div>
        </div>
      </div>

      {/* Incidents Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-800 border-b border-slate-700">
              <tr>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">
                  <div className="flex items-center gap-2">
                    Incident ID
                    <ChevronDown className="w-4 h-4" />
                  </div>
                </th>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">Title</th>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">Category</th>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">
                  <div className="flex items-center gap-2">
                    Severity
                    <ChevronDown className="w-4 h-4" />
                  </div>
                </th>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">Status</th>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">Created</th>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">Assignee</th>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredIncidents.map((incident) => (
                <tr key={incident.id} className="border-b border-slate-800 hover:bg-slate-800/50 transition-colors">
                  <td className="py-4 px-6">
                    <span className="text-blue-400 font-mono text-sm">{incident.id.split('-')[0]}</span>
                  </td>
                  <td className="py-4 px-6 text-slate-300 text-sm font-medium">{incident.title}</td>
                  <td className="py-4 px-6">
                    <span className="inline-flex items-center px-3 py-1 bg-slate-700 rounded-full text-xs text-slate-300">
                      {incident.category || "Unknown"}
                    </span>
                  </td>
                  <td className="py-4 px-6">
                    <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium ${incident.severity === "Critical" ? "bg-purple-600/20 text-purple-400" :
                      incident.severity === "High" ? "bg-red-600/20 text-red-400" :
                        incident.severity === "Medium" ? "bg-orange-600/20 text-orange-400" :
                          "bg-yellow-600/20 text-yellow-400"
                      }`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${incident.severity === "Critical" ? "bg-purple-400" :
                        incident.severity === "High" ? "bg-red-400" :
                          incident.severity === "Medium" ? "bg-orange-400" :
                            "bg-yellow-400"
                        }`}></span>
                      {incident.severity}
                    </span>
                  </td>
                  <td className="py-4 px-6">
                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${incident.status === "Resolved" ? "bg-green-600/20 text-green-400" :
                      incident.status === "In Progress" ? "bg-blue-600/20 text-blue-400" :
                        "bg-slate-600/20 text-slate-400"
                      }`}>
                      {incident.status}
                    </span>
                  </td>
                  <td className="py-4 px-6 text-slate-300 text-sm">{new Date(incident.created_at).toLocaleDateString()}</td>
                  <td className="py-4 px-6 text-slate-300 text-sm">{incident.assignee || "Unassigned"}</td>
                  <td className="py-4 px-6">
                    <button className="text-blue-400 hover:text-blue-300 text-sm font-medium">
                      View Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between px-6 py-4 bg-slate-800 border-t border-slate-700">
          <div className="text-slate-400 text-sm">
            Showing {filteredIncidents.length} of {incidentsData.length} incidents
          </div>
          <div className="flex items-center gap-2">
            <button className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm transition-colors">
              Previous
            </button>
            <button className="px-3 py-2 bg-blue-600 text-white rounded-lg text-sm">1</button>
            <button className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm transition-colors">2</button>
            <button className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm transition-colors">
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
