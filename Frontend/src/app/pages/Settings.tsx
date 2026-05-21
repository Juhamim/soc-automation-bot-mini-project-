import { useEffect, useState } from "react";
import { Bell, Shield, Users, Database, Mail, Globe, Key, Save } from "lucide-react";
import {
  fetchApiKeys,
  fetchIntegrations,
  fetchSettings,
  updateSettings,
  fetchUsers,
  createUser,
  updateUser,
} from "../../api/client";

export function Settings() {
  const [activeTab, setActiveTab] = useState("general");
  const [general, setGeneral] = useState({
    organization_name: "",
    time_zone: "",
    date_format: "",
    language: "",
  });
  const [notifications, setNotifications] = useState({
    critical_alerts: false,
    incident_updates: false,
    playbook_failures: false,
    weekly_reports: false,
    email: "",
  });
  const [security, setSecurity] = useState({
    two_factor_enabled: false,
    session_timeout_minutes: 30,
    password_min_length: 12,
    require_special_chars: true,
  });
  const [integrations, setIntegrations] = useState<any[]>([]);
  const [apiKeys, setApiKeys] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [isUsersLoading, setIsUsersLoading] = useState(false);
  const [userError, setUserError] = useState("");
  const [newUser, setNewUser] = useState({ username: "", email: "", password: "", role: "Analyst" });
  const [isCreatingUser, setIsCreatingUser] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [loadError, setLoadError] = useState("");

  useEffect(() => {
    async function loadSettings() {
      try {
        setIsUsersLoading(true);
        const [settingsData, integrationsData, apiKeysData, usersData] = await Promise.all([
          fetchSettings(),
          fetchIntegrations(),
          fetchApiKeys(),
          fetchUsers(),
        ]);
        setGeneral(settingsData.general);
        setNotifications(settingsData.notifications);
        setSecurity(settingsData.security);
        setIntegrations(integrationsData.integrations || []);
        setApiKeys(apiKeysData.keys || []);
        setUsers(usersData || []);
      } catch (err: any) {
        const msg = err?.message || "Failed to load settings";
        setLoadError(msg);
        setUserError(msg);
      } finally {
        setIsUsersLoading(false);
      }
    }
    loadSettings();
  }, []);

  const handleSaveGeneral = async () => {
    setIsSaving(true);
    try {
      const updated = await updateSettings({ general });
      setGeneral(updated.general);
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveNotifications = async () => {
    setIsSaving(true);
    try {
      const updated = await updateSettings({ notifications });
      setNotifications(updated.notifications);
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveSecurity = async () => {
    setIsSaving(true);
    try {
      const updated = await updateSettings({ security });
      setSecurity(updated.security);
    } finally {
      setIsSaving(false);
    }
  };

  const tabs = [
    { id: "general", label: "General", icon: Globe },
    { id: "notifications", label: "Notifications", icon: Bell },
    { id: "security", label: "Security", icon: Shield },
    { id: "users", label: "Users & Permissions", icon: Users },
    { id: "integrations", label: "Integrations", icon: Database },
    { id: "api", label: "API Keys", icon: Key },
  ];
  const notificationItems = [
    {
      key: "critical_alerts",
      label: "Critical Alerts",
      description: "Receive emails for critical severity alerts",
    },
    {
      key: "incident_updates",
      label: "Incident Updates",
      description: "Get notified about incident status changes",
    },
    {
      key: "playbook_failures",
      label: "Playbook Failures",
      description: "Alert when automated playbooks fail",
    },
    {
      key: "weekly_reports",
      label: "Weekly Reports",
      description: "Receive weekly summary reports",
    },
  ] as const;

  return (
    <div className="p-8 min-h-screen">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-semibold text-white mb-2">Settings</h1>
        <p className="text-slate-400">Configure your SOC Automation Bot preferences</p>
      </div>
      {loadError && (
        <div className="mb-6 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {loadError}
        </div>
      )}

      <div className="flex gap-6">
        {/* Sidebar Tabs */}
        <div className="w-64 bg-slate-900 border border-slate-800 rounded-xl p-4 h-fit">
          <nav className="space-y-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-colors ${
                    activeTab === tab.id
                      ? "bg-blue-600 text-white"
                      : "text-slate-400 hover:bg-slate-800 hover:text-white"
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="text-sm">{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Content Area */}
        <div className="flex-1">
          {activeTab === "general" && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <h2 className="text-xl font-semibold text-white mb-6">General Settings</h2>
              
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Organization Name
                  </label>
                  <input
                    type="text"
                    value={general.organization_name}
                    onChange={(e) =>
                      setGeneral((prev) => ({ ...prev, organization_name: e.target.value }))
                    }
                    className="w-full bg-slate-800 border border-slate-700 text-white px-4 py-2.5 rounded-lg focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Time Zone
                  </label>
                  <select
                    value={general.time_zone}
                    onChange={(e) =>
                      setGeneral((prev) => ({ ...prev, time_zone: e.target.value }))
                    }
                    className="w-full bg-slate-800 border border-slate-700 text-white px-4 py-2.5 rounded-lg focus:outline-none focus:border-blue-500"
                  >
                    <option>UTC (GMT+0:00)</option>
                    <option>EST (GMT-5:00)</option>
                    <option>PST (GMT-8:00)</option>
                    <option>CET (GMT+1:00)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Date Format
                  </label>
                  <select
                    value={general.date_format}
                    onChange={(e) =>
                      setGeneral((prev) => ({ ...prev, date_format: e.target.value }))
                    }
                    className="w-full bg-slate-800 border border-slate-700 text-white px-4 py-2.5 rounded-lg focus:outline-none focus:border-blue-500"
                  >
                    <option>MM/DD/YYYY</option>
                    <option>DD/MM/YYYY</option>
                    <option>YYYY-MM-DD</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Language
                  </label>
                  <select
                    value={general.language}
                    onChange={(e) =>
                      setGeneral((prev) => ({ ...prev, language: e.target.value }))
                    }
                    className="w-full bg-slate-800 border border-slate-700 text-white px-4 py-2.5 rounded-lg focus:outline-none focus:border-blue-500"
                  >
                    <option>English (US)</option>
                    <option>English (UK)</option>
                    <option>Spanish</option>
                    <option>French</option>
                    <option>German</option>
                  </select>
                </div>

                <button
                  onClick={handleSaveGeneral}
                  disabled={isSaving}
                  className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2.5 rounded-lg transition-colors disabled:opacity-60"
                >
                  <Save className="w-4 h-4" />
                  {isSaving ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </div>
          )}

          {activeTab === "notifications" && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <h2 className="text-xl font-semibold text-white mb-6">Notification Preferences</h2>
              
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-white mb-4">Email Notifications</h3>
                  <div className="space-y-4">
                    {notificationItems.map((item) => (
                      <div key={item.key} className="flex items-center justify-between p-4 bg-slate-800 rounded-lg">
                        <div>
                          <div className="text-white font-medium text-sm">{item.label}</div>
                          <div className="text-slate-400 text-xs mt-1">{item.description}</div>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={notifications[item.key]}
                            onChange={(e) =>
                              setNotifications((prev) => ({ ...prev, [item.key]: e.target.checked }))
                            }
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                        </label>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-white mb-4">Notification Channels</h3>
                  <div className="space-y-3">
                    <div className="flex items-center gap-3 p-4 bg-slate-800 rounded-lg">
                      <Mail className="w-5 h-5 text-blue-400" />
                      <div className="flex-1">
                        <div className="text-white font-medium text-sm">Email</div>
                        <div className="text-slate-400 text-xs">{notifications.email || "Not set"}</div>
                      </div>
                      <button className="text-blue-400 hover:text-blue-300 text-sm">Configure</button>
                    </div>
                  </div>
                </div>

                <button
                  onClick={handleSaveNotifications}
                  disabled={isSaving}
                  className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2.5 rounded-lg transition-colors disabled:opacity-60"
                >
                  <Save className="w-4 h-4" />
                  {isSaving ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </div>
          )}

          {activeTab === "security" && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <h2 className="text-xl font-semibold text-white mb-6">Security Settings</h2>
              
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-white mb-4">Authentication</h3>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-slate-800 rounded-lg">
                      <div>
                        <div className="text-white font-medium text-sm">Two-Factor Authentication</div>
                        <div className="text-slate-400 text-xs mt-1">Add an extra layer of security</div>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={security.two_factor_enabled}
                          onChange={(e) =>
                            setSecurity((prev) => ({ ...prev, two_factor_enabled: e.target.checked }))
                          }
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                      </label>
                    </div>

                    <div className="flex items-center justify-between p-4 bg-slate-800 rounded-lg">
                      <div>
                        <div className="text-white font-medium text-sm">Session Timeout</div>
                        <div className="text-slate-400 text-xs mt-1">Automatically log out after inactivity</div>
                      </div>
                      <select
                        value={String(security.session_timeout_minutes)}
                        onChange={(e) =>
                          setSecurity((prev) => ({
                            ...prev,
                            session_timeout_minutes: Number(e.target.value),
                          }))
                        }
                        className="bg-slate-700 border border-slate-600 text-white px-3 py-2 rounded-lg text-sm focus:outline-none focus:border-blue-500"
                      >
                        <option value="15">15 minutes</option>
                        <option value="30">30 minutes</option>
                        <option value="60">1 hour</option>
                        <option value="0">Never</option>
                      </select>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-white mb-4">Password Policy</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        Minimum Password Length
                      </label>
                      <input
                        type="number"
                        value={security.password_min_length}
                        min="8"
                        onChange={(e) =>
                          setSecurity((prev) => ({
                            ...prev,
                            password_min_length: Number(e.target.value),
                          }))
                        }
                        className="w-full bg-slate-800 border border-slate-700 text-white px-4 py-2.5 rounded-lg focus:outline-none focus:border-blue-500"
                      />
                    </div>

                    <div className="flex items-center justify-between p-4 bg-slate-800 rounded-lg">
                      <div>
                        <div className="text-white font-medium text-sm">Require Special Characters</div>
                        <div className="text-slate-400 text-xs mt-1">Passwords must include symbols</div>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={security.require_special_chars}
                          onChange={(e) =>
                            setSecurity((prev) => ({
                              ...prev,
                              require_special_chars: e.target.checked,
                            }))
                          }
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                      </label>
                    </div>
                  </div>
                </div>

                <button
                  onClick={handleSaveSecurity}
                  disabled={isSaving}
                  className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2.5 rounded-lg transition-colors disabled:opacity-60"
                >
                  <Save className="w-4 h-4" />
                  {isSaving ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </div>
          )}

          {activeTab === "users" && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-white">Users & Permissions</h2>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    placeholder="Username"
                    value={newUser.username}
                    onChange={(e) => setNewUser((prev) => ({ ...prev, username: e.target.value }))}
                    className="bg-slate-800 border border-slate-700 text-white px-3 py-2 rounded-lg text-sm"
                  />
                  <input
                    type="email"
                    placeholder="Email"
                    value={newUser.email}
                    onChange={(e) => setNewUser((prev) => ({ ...prev, email: e.target.value }))}
                    className="bg-slate-800 border border-slate-700 text-white px-3 py-2 rounded-lg text-sm"
                  />
                  <input
                    type="password"
                    placeholder="Password"
                    value={newUser.password}
                    onChange={(e) => setNewUser((prev) => ({ ...prev, password: e.target.value }))}
                    className="bg-slate-800 border border-slate-700 text-white px-3 py-2 rounded-lg text-sm"
                  />
                  <select
                    value={newUser.role}
                    onChange={(e) => setNewUser((prev) => ({ ...prev, role: e.target.value }))}
                    className="bg-slate-800 border border-slate-700 text-white px-3 py-2 rounded-lg text-sm"
                  >
                    <option value="Admin">Admin</option>
                    <option value="Analyst">Analyst</option>
                    <option value="Auditor">Auditor</option>
                  </select>
                  <button
                    onClick={async () => {
                      try {
                        setIsCreatingUser(true);
                        const created = await createUser(newUser);
                        setUsers((prev) => [created, ...prev]);
                        setNewUser({ username: "", email: "", password: "", role: "Analyst" });
                        setUserError("");
                      } catch (err: any) {
                        setUserError(err?.message || "Failed to create user");
                      } finally {
                        setIsCreatingUser(false);
                      }
                    }}
                    disabled={isCreatingUser || !newUser.username || !newUser.email || !newUser.password}
                    className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-60"
                  >
                    <Users className="w-4 h-4" />
                    {isCreatingUser ? "Creating..." : "Add User"}
                  </button>
                </div>
              </div>

              {userError && (
                <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-xs text-red-300">
                  {userError}
                </div>
              )}
              
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-slate-800 border-b border-slate-700">
                    <tr>
                      <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">Username</th>
                      <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">Email</th>
                      <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">Role</th>
                      <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">Status</th>
                      <th className="text-left py-4 px-6 text-slate-300 font-medium text-sm">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {isUsersLoading ? (
                      <tr>
                        <td colSpan={5} className="py-6 px-6 text-center text-slate-400 text-sm">
                          Loading users...
                        </td>
                      </tr>
                    ) : users.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="py-6 px-6 text-center text-slate-500 text-sm">
                          No users found.
                        </td>
                      </tr>
                    ) : (
                      users.map((user: any) => (
                        <tr key={user.id} className="border-b border-slate-800 hover:bg-slate-800/50 transition-colors">
                          <td className="py-4 px-6 text-white text-sm font-medium">{user.username}</td>
                          <td className="py-4 px-6 text-slate-300 text-sm">{user.email}</td>
                          <td className="py-4 px-6">
                            <select
                              value={user.role}
                              onChange={async (e) => {
                                const role = e.target.value;
                                try {
                                  const updated = await updateUser(user.id, { role });
                                  setUsers((prev) => prev.map((u) => (u.id === user.id ? updated : u)));
                                } catch (err: any) {
                                  setUserError(err?.message || "Failed to update role");
                                }
                              }}
                              className="bg-slate-800 border border-slate-700 text-white px-3 py-1.5 rounded-full text-xs"
                            >
                              <option value="Admin">Admin</option>
                              <option value="Analyst">Analyst</option>
                              <option value="Auditor">Auditor</option>
                            </select>
                          </td>
                          <td className="py-4 px-6">
                            <span
                              className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                                user.is_active
                                  ? "bg-green-600/20 text-green-400"
                                  : "bg-slate-600/20 text-slate-400"
                              }`}
                            >
                              {user.is_active ? "Active" : "Inactive"}
                            </span>
                          </td>
                          <td className="py-4 px-6 flex items-center gap-2">
                            <button
                              onClick={async () => {
                                try {
                                  const updated = await updateUser(user.id, { is_active: !user.is_active });
                                  setUsers((prev) => prev.map((u) => (u.id === user.id ? updated : u)));
                                } catch (err: any) {
                                  setUserError(err?.message || "Failed to update status");
                                }
                              }}
                              className="text-blue-400 hover:text-blue-300 text-xs font-medium"
                            >
                              {user.is_active ? "Disable" : "Enable"}
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === "integrations" && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <h2 className="text-xl font-semibold text-white mb-6">Integrations</h2>
              
              <div className="grid grid-cols-2 gap-6">
                {integrations.map((integration, index) => {
                  const iconMap: Record<string, any> = {
                    "SIEM Integration": Database,
                    "Email Gateway": Mail,
                    "Firewall API": Shield,
                    "Threat Intel Feed": Globe,
                  };
                  const Icon = iconMap[integration.name] || Database;
                  return (
                    <div key={index} className="p-6 bg-slate-800 border border-slate-700 rounded-xl">
                      <div className="flex items-start gap-4 mb-4">
                        <div className="w-12 h-12 bg-slate-700 rounded-lg flex items-center justify-center">
                          <Icon className="w-6 h-6 text-blue-400" />
                        </div>
                        <div className="flex-1">
                          <h3 className="text-white font-semibold mb-1">{integration.name}</h3>
                          <p className="text-slate-400 text-sm">{integration.description}</p>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                          integration.status === "Connected"
                            ? "bg-green-600/20 text-green-400"
                            : "bg-slate-600/20 text-slate-400"
                        }`}>
                          {integration.status}
                        </span>
                        <button className="text-blue-400 hover:text-blue-300 text-sm font-medium">
                          {integration.status_detail || "Configure"}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {activeTab === "api" && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-white">API Keys</h2>
                <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors">
                  <Key className="w-4 h-4" />
                  Generate New Key
                </button>
              </div>
              
              <div className="space-y-4">
                {apiKeys.map((apiKey, index) => (
                  <div key={index} className="p-6 bg-slate-800 border border-slate-700 rounded-xl">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <h3 className="text-white font-semibold mb-2">{apiKey.name}</h3>
                        <div className="flex items-center gap-2 mb-3">
                          <code className="bg-slate-900 border border-slate-700 text-blue-400 px-3 py-2 rounded font-mono text-sm">
                            {apiKey.key}
                          </code>
                          <button className="text-blue-400 hover:text-blue-300 text-sm">Copy</button>
                        </div>
                        <div className="flex items-center gap-6 text-xs text-slate-400">
                          <span>Created: {apiKey.created || "N/A"}</span>
                          <span>Last used: {apiKey.last_used || "N/A"}</span>
                        </div>
                      </div>
                      <button className="text-red-400 hover:text-red-300 text-sm font-medium">
                        Revoke
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
