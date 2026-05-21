import { useState, useEffect } from "react";
import { Search, Filter, Plus, Play, Edit, Copy, Trash2, Clock, CheckCircle, XCircle } from "lucide-react";
import { triggerAction, fetchPlaybooks, togglePlaybookAPI, fetchExecutions } from "../../api/client";
import { PlaybookBuilderModal } from "./PlaybookBuilderModal";


export function Playbooks() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("All");
  const [isExecuting, setIsExecuting] = useState(false);
  const [playbooks, setPlaybooks] = useState<any[]>([]);
  const [executions, setExecutions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isBuilderOpen, setIsBuilderOpen] = useState(false);

  useEffect(() => {
    loadPlaybooks();
  }, []);

  const loadPlaybooks = async () => {
    try {
      setLoading(true);
      const data = await fetchPlaybooks(true);
      setPlaybooks(data);
      const execs = await fetchExecutions();
      setExecutions(execs);
    } catch (err) {
      console.error("Error loading playbooks/executions:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (playbookId: string, currentStatus: boolean) => {
    try {
      await togglePlaybookAPI(playbookId, !currentStatus);
      await loadPlaybooks();
    } catch (e: any) {
      alert("Failed to toggle playbook: " + e.message);
    }
  };

  const filteredPlaybooks = playbooks.filter((playbook) => {
    const statusText = playbook.is_active ? "Active" : "Inactive";
    const matchesSearch = playbook.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (playbook.description && playbook.description.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesStatus = selectedStatus === "All" || statusText === selectedStatus;
    return matchesSearch && matchesStatus;
  });

  const handleRunPlaybook = async (actionName: string) => {
    // We are simulating a manual run on a mock alert ID since Playbooks require an alert context
    try {
      setIsExecuting(true);
      await triggerAction("test-alert-id-001", actionName, { test: true });
      alert(`Playbook Action '${actionName}' executed successfully`);
    } catch (e: any) {
      alert(`Simulation failed (likely no test alert in DB): ${e.message}`);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="p-8 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-semibold text-white mb-2">Playbooks</h1>
          <p className="text-slate-400">Automate security response workflows</p>
        </div>
        <div className="flex items-center gap-4">
          <button
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
            onClick={() => setIsBuilderOpen(true)}
          >
            <Plus className="w-4 h-4" />
            Create Playbook
          </button>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-4 gap-6 mb-8">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="text-slate-400 text-sm mb-2">Total Playbooks</div>
          <div className="text-white text-3xl font-semibold">{playbooks.length}</div>
          <div className="text-green-400 text-sm mt-2">{playbooks.filter(p => p.is_active).length} Active</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="text-slate-400 text-sm mb-2">Total Executions</div>
          <div className="text-white text-3xl font-semibold">1,247</div>
          <div className="text-slate-400 text-sm mt-2">Last 30 days</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="text-slate-400 text-sm mb-2">Success Rate</div>
          <div className="text-white text-3xl font-semibold">96%</div>
          <div className="text-green-400 text-sm mt-2">↑ 2% from last month</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="text-slate-400 text-sm mb-2">Avg. Execution Time</div>
          <div className="text-white text-3xl font-semibold">1.6s</div>
          <div className="text-green-400 text-sm mt-2">↓ 0.4s improvement</div>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-6">
        <div className="flex items-center gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              placeholder="Search playbooks by name or description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 text-white pl-10 pr-4 py-2.5 rounded-lg focus:outline-none focus:border-blue-500"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-slate-400" />
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="bg-slate-800 border border-slate-700 text-white px-4 py-2.5 rounded-lg focus:outline-none focus:border-blue-500"
            >
              <option value="All">All Statuses</option>
              <option value="Active">Active</option>
              <option value="Inactive">Inactive</option>
            </select>
          </div>
        </div>
      </div>

      {/* Playbooks Grid */}
      <div className="grid grid-cols-2 gap-6 mb-8">
        {loading ? (
          <div className="text-slate-400">Loading playbooks...</div>
        ) : filteredPlaybooks.map((playbook) => (
          <div key={playbook.id} className="bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-slate-700 transition-colors">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-lg font-semibold text-white">{playbook.name}</h3>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium cursor-pointer ${playbook.is_active
                    ? "bg-green-600/20 text-green-400"
                    : "bg-slate-600/20 text-slate-400"
                    }`}
                    onClick={() => handleToggle(playbook.id, playbook.is_active)}
                  >
                    {playbook.is_active ? "Active (Click to Disable)" : "Disabled (Click to Enable)"}
                  </span>
                </div>
                <p className="text-slate-400 text-sm mb-3">{playbook.description || "No description provided."}</p>
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    Last run: Unknown
                  </span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4 mb-4 pb-4 border-b border-slate-800">
              <div>
                <div className="text-slate-400 text-xs mb-1">Executions</div>
                <div className="text-white font-semibold">0</div>
              </div>
              <div>
                <div className="text-slate-400 text-xs mb-1">Success Rate</div>
                <div className="text-green-400 font-semibold">-%</div>
              </div>
              <div>
                <div className="text-slate-400 text-xs mb-1">Trigger</div>
                <div className="text-white text-xs">{playbook.trigger_severity?.join(", ") || "Any"}</div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => handleRunPlaybook("test")} // Replace logic here to actually test it if needed
                disabled={isExecuting}
                className="flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition-colors disabled:opacity-50"
              >
                <Play className="w-4 h-4" />
                {isExecuting ? "Testing..." : "Test Playbook"}
              </button>
              <button className="flex items-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white rounded-lg text-sm transition-colors">
                <Edit className="w-4 h-4" />
                Edit
              </button>
              <button className="flex items-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white rounded-lg text-sm transition-colors">
                <Copy className="w-4 h-4" />
              </button>
              <button className="flex items-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-red-400 rounded-lg text-sm transition-colors ml-auto">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Executions */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="p-6 border-b border-slate-800">
          <h2 className="text-xl font-semibold text-white">Recent Executions</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-800 border-b border-slate-700">
              <tr>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">Playbook</th>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">Action Name</th>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">Timestamp</th>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">Trigger</th>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">Status</th>
                <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">Duration</th>
              </tr>
            </thead>
            <tbody>
              {executions.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400">No recent playbook executions found. Wait for a new alert to trigger the system.</td>
                </tr>
              ) : executions.map((execution, index) => (
                <tr key={index} className="border-b border-slate-800 hover:bg-slate-800/50 transition-colors">
                  <td className="py-4 px-6 text-white text-sm font-medium">{execution.playbook}</td>
                  <td className="py-4 px-6 text-slate-300 text-sm font-mono">{execution.action_name}</td>
                  <td className="py-4 px-6 text-slate-300 text-sm">{execution.timestamp}</td>
                  <td className="py-4 px-6">
                    <span className="inline-flex items-center px-3 py-1 bg-slate-700 rounded-full text-xs text-slate-300">
                      {execution.trigger}
                    </span>
                  </td>
                  <td className="py-4 px-6">
                    <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium ${execution.status === "Success"
                      ? "bg-green-600/20 text-green-400"
                      : "bg-orange-600/20 text-orange-400"
                      }`}>
                      {execution.status === "Success" ? (
                        <CheckCircle className="w-3 h-3" />
                      ) : (
                        <Clock className="w-3 h-3" />
                      )}
                      {execution.status}
                    </span>
                  </td>
                  <td className="py-4 px-6 text-slate-300 text-sm font-mono">{execution.duration}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Playbook Builder Modal */}
      {isBuilderOpen && (
        <PlaybookBuilderModal
          onClose={() => setIsBuilderOpen(false)}
          onSuccess={() => {
            setIsBuilderOpen(false);
            loadPlaybooks();
          }}
        />
      )}
    </div>
  );
}
