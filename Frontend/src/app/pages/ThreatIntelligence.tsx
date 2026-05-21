import { useState, useEffect } from "react";
import { Search, Filter, Download, Globe, AlertTriangle, Shield, TrendingUp } from "lucide-react";
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts";
import { fetchThreatIntel } from "../../api/client";

import { useMemo } from "react";

export function ThreatIntelligence() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedType, setSelectedType] = useState("All");
  const [selectedRisk, setSelectedRisk] = useState("All");
  const [dateStart, setDateStart] = useState("");
  const [dateEnd, setDateEnd] = useState("");
  const [threatFeedData, setThreatFeedData] = useState<any[]>([]);
  const [totalThreats, setTotalThreats] = useState(0);

  useEffect(() => {
    async function loadData() {
      try {
        const data = await fetchThreatIntel(1, 100);
        setThreatFeedData(data.threats || []);
        setTotalThreats(data.total || 0);
      } catch (error) {
        console.error("Failed to load threat intel", error);
      }
    }
    loadData();
  }, []);

  const filteredThreats = threatFeedData.filter((threat) => {
    const matchesSearch = threat.indicator_value?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      threat.indicator_type?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (threat.country && threat.country.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesType = selectedType === "All" || threat.indicator_type === selectedType;
    const matchesRisk = selectedRisk === "All" || threat.risk_level === selectedRisk;
    let matchesDate = true;
    if (dateStart) {
      const start = new Date(dateStart).getTime();
      const firstSeen = threat.first_seen ? new Date(threat.first_seen).getTime() : 0;
      matchesDate = firstSeen >= start;
    }
    if (matchesDate && dateEnd) {
      const end = new Date(dateEnd).getTime();
      const lastSeen = threat.last_seen ? new Date(threat.last_seen).getTime() : 0;
      matchesDate = lastSeen <= end;
    }
    return matchesSearch && matchesType && matchesRisk && matchesDate;
  });

  const countryData = useMemo(() => {
    const counts: Record<string, number> = {};
    threatFeedData.forEach(t => {
      const c = t.country || 'Unknown';
      counts[c] = (counts[c] || 0) + 1;
    });
    return Object.entries(counts).map(([country, threats]) => ({ country, threats }));
  }, [threatFeedData]);

  const threatTrendData = useMemo(() => {
    const grouped: Record<string, any> = {};
    threatFeedData.forEach(t => {
      if (!t.first_seen) return;
      const date = new Date(t.first_seen).toLocaleDateString('default', { month: 'short', day: 'numeric' });
      if (!grouped[date]) {
        grouped[date] = { date, malware: 0, phishing: 0, botnet: 0 };
      }
      const typeStr = t.indicator_type?.toLowerCase() || 'other';
      if (typeStr.includes('malware') || typeStr.includes('hash')) grouped[date].malware += 1;
      else if (typeStr.includes('phishing')) grouped[date].phishing += 1;
      else grouped[date].botnet += 1; // Fallback to botnet/other for simplicity
    });
    return Object.values(grouped);
  }, [threatFeedData]);

  const uniqueCountries = new Set(threatFeedData.map(t => t.country).filter(Boolean)).size;
  const blockedToday = useMemo(() => {
    const now = new Date();
    const todayStr = now.toLocaleDateString();
    return threatFeedData.filter((t) => {
      if (!t.last_seen) return false;
      const d = new Date(t.last_seen);
      return d.toLocaleDateString() === todayStr;
    }).length;
  }, [threatFeedData]);

  const trendPercent = useMemo(() => {
    if (!threatTrendData.length) return 0;
    const last = threatTrendData[threatTrendData.length - 1];
    const prev = threatTrendData[threatTrendData.length - 2] || null;
    const lastTotal = (last.malware || 0) + (last.phishing || 0) + (last.botnet || 0);
    const prevTotal = prev ? (prev.malware || 0) + (prev.phishing || 0) + (prev.botnet || 0) : 0;
    if (prevTotal === 0) return lastTotal > 0 ? 100 : 0;
    return Math.round(((lastTotal - prevTotal) / prevTotal) * 100);
  }, [threatTrendData]);

  const handleExportThreatsTxt = () => {
    const rows = filteredThreats.length ? filteredThreats : threatFeedData;
    if (!rows.length) return;
    const lines = rows.map((t) => {
      const firstSeen = t.first_seen ? new Date(t.first_seen).toLocaleDateString() : "";
      const lastSeen = t.last_seen ? new Date(t.last_seen).toLocaleDateString() : "";
      return [
        `ID: ${t.id}`,
        `Type: ${t.indicator_type || ""}`,
        `Indicator: ${t.indicator_value || ""}`,
        `Risk: ${t.risk_level || ""}`,
        `Country: ${t.country || ""}`,
        `First Seen: ${firstSeen}`,
        `Last Seen: ${lastSeen}`,
        `Occurrences: ${t.occurrences ?? ""}`,
        "---",
      ].join("\n");
    });
    const content = ["Threat Intelligence Export", "===========================", "", ...lines].join("\n");
    const blob = new Blob([content], { type: "text/plain;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "threat_intel.txt";
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-8 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-semibold text-white mb-2">Threat Intelligence</h1>
          <p className="text-slate-400">Monitor global threat landscape and IOCs</p>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={handleExportThreatsTxt}
            className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <Download className="w-4 h-4" />
            Export Feed
          </button>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-4 gap-6 mb-8">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-red-600 rounded-lg flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="text-slate-400 text-sm mb-1">Active Threats</div>
              <div className="text-white text-3xl font-semibold">{totalThreats}</div>
            </div>
          </div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-orange-600 rounded-lg flex items-center justify-center">
              <Globe className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="text-slate-400 text-sm mb-1">Countries</div>
              <div className="text-white text-3xl font-semibold">{uniqueCountries || 1}</div>
            </div>
          </div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-purple-600 rounded-lg flex items-center justify-center">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="text-slate-400 text-sm mb-1">Blocked Today</div>
              <div className="text-white text-3xl font-semibold">{blockedToday}</div>
            </div>
          </div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="text-slate-400 text-sm mb-1">Trend</div>
              <div className="text-white text-3xl font-semibold">
                {trendPercent > 0 ? `+${trendPercent}%` : `${trendPercent}%`}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-2 gap-6 mb-8">
        {/* Threat Activity Trend */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h2 className="text-xl font-semibold text-white mb-6">Threat Activity Trend</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={threatTrendData}>
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
              <Bar dataKey="malware" fill="#ef4444" radius={[4, 4, 0, 0]} />
              <Bar dataKey="phishing" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              <Bar dataKey="botnet" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <div className="flex items-center justify-center gap-6 mt-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-red-500 rounded"></div>
              <span className="text-slate-300 text-sm">Malware</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-orange-500 rounded"></div>
              <span className="text-slate-300 text-sm">Phishing</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-purple-500 rounded"></div>
              <span className="text-slate-300 text-sm">Botnet</span>
            </div>
          </div>
        </div>

        {/* Threats by Country */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h2 className="text-xl font-semibold text-white mb-6">Top Threat Sources</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={countryData} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis type="number" stroke="#64748b" style={{ fontSize: '12px' }} />
              <YAxis type="category" dataKey="country" stroke="#64748b" style={{ fontSize: '12px' }} width={100} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
              <Bar dataKey="threats" fill="#3b82f6" radius={[0, 4, 4, 0]} />
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
              placeholder="Search by IP address, type, or country..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 text-white pl-10 pr-4 py-2.5 rounded-lg focus:outline-none focus:border-blue-500"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-slate-400" />
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="bg-slate-800 border border-slate-700 text-white px-4 py-2.5 rounded-lg focus:outline-none focus:border-blue-500"
            >
              <option value="All">All Types</option>
              <option value="Malware">Malware</option>
              <option value="Phishing">Phishing</option>
              <option value="Botnet">Botnet</option>
              <option value="C&C Server">C&C Server</option>
              <option value="Tor Exit Node">Tor Exit Node</option>
              <option value="Scanning">Scanning</option>
            </select>
            <select
              value={selectedRisk}
              onChange={(e) => setSelectedRisk(e.target.value)}
              className="bg-slate-800 border border-slate-700 text-white px-4 py-2.5 rounded-lg focus:outline-none focus:border-blue-500"
            >
              <option value="All">All Risk Levels</option>
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
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
          </div>
        </div>
      </div>

      {/* Threat Feed Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-800 border-b border-slate-700">
              <tr>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">IP Address</th>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">Type</th>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">Risk Level</th>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">Country</th>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">First Seen</th>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">Last Seen</th>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">Occurrences</th>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredThreats.map((threat) => (
                <tr key={threat.id} className="border-b border-slate-800 hover:bg-slate-800/50 transition-colors">
                  <td className="py-4 px-6">
                    <span className="text-blue-400 font-mono text-sm">{threat.indicator_value}</span>
                  </td>
                  <td className="py-4 px-6">
                    <span className="inline-flex items-center px-3 py-1 bg-slate-700 rounded-full text-xs text-slate-300">
                      {threat.indicator_type}
                    </span>
                  </td>
                  <td className="py-4 px-6">
                    <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium ${threat.risk_level === "Critical" ? "bg-purple-600/20 text-purple-400" :
                      threat.risk_level === "High" ? "bg-red-600/20 text-red-400" :
                        threat.risk_level === "Medium" ? "bg-orange-600/20 text-orange-400" :
                          "bg-yellow-600/20 text-yellow-400"
                      }`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${threat.risk_level === "Critical" ? "bg-purple-400" :
                        threat.risk_level === "High" ? "bg-red-400" :
                          threat.risk_level === "Medium" ? "bg-orange-400" :
                            "bg-yellow-400"
                        }`}></span>
                      {threat.risk_level}
                    </span>
                  </td>
                  <td className="py-4 px-6 text-slate-300 text-sm">{threat.country || "Unknown"}</td>
                  <td className="py-4 px-6 text-slate-300 text-sm">{new Date(threat.first_seen).toLocaleDateString()}</td>
                  <td className="py-4 px-6 text-slate-300 text-sm">{new Date(threat.last_seen).toLocaleDateString()}</td>
                  <td className="py-4 px-6">
                    <span className="inline-flex items-center px-3 py-1 bg-slate-700 rounded-full text-xs text-slate-300 font-medium">
                      {threat.occurrence_count}
                    </span>
                  </td>
                  <td className="py-4 px-6">
                    <button className="text-blue-400 hover:text-blue-300 text-sm font-medium">
                      Block IP
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
            Showing {filteredThreats.length} of {threatFeedData.length} threats
          </div>
          <div className="flex items-center gap-2">
            <button className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm transition-colors">
              Previous
            </button>
            <button className="px-3 py-2 bg-blue-600 text-white rounded-lg text-sm">1</button>
            <button className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm transition-colors">2</button>
            <button className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm transition-colors">3</button>
            <button className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm transition-colors">
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
