export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
const API_KEY = import.meta.env.VITE_API_KEY || "dev_api_key";

let currentToken: string | null = null;

export const api = {
  setToken: (token: string | null) => {
    currentToken = token;
  }
};

const getHeaders = () => {
  const h: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (currentToken) {
    h["Authorization"] = `Bearer ${currentToken}`;
  } else {
    // Fallback for dev mode if needed, though JWT is enforced now
    h["X-API-Key"] = API_KEY;
  }
  return h;
};

export async function fetchMetrics() {
  const response = await fetch(`${API_BASE_URL}/metrics`, { headers: getHeaders() });
  if (!response.ok) throw new Error("Failed to fetch metrics");
  return response.json();
}

export async function fetchAlerts(params?: Record<string, string>) {
  const url = new URL(`${API_BASE_URL}/alerts`);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      url.searchParams.append(key, value);
    });
  }
  const response = await fetch(url.toString(), { headers: getHeaders() });
  if (!response.ok) throw new Error("Failed to fetch alerts");
  return response.json();
}

export async function fetchAlertDetail(alertId: string) {
  const response = await fetch(`${API_BASE_URL}/alerts/${alertId}`, { headers: getHeaders() });
  if (!response.ok) throw new Error("Failed to fetch alert detail");
  return response.json();
}

export async function triggerAction(alertId: string, actionName: string, params: Record<string, any> = {}) {
  const response = await fetch(`${API_BASE_URL}/alerts/${alertId}/actions/${actionName}`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ parameters: params, executed_by: "analyst" }),
  });
  if (!response.ok) throw new Error("Failed to trigger action");
  return response.json();
}

export async function fetchPlaybooks(includeInactive = true) {
  const response = await fetch(`${API_BASE_URL}/playbooks?include_inactive=${includeInactive}`, { headers: getHeaders() });
  if (!response.ok) throw new Error("Failed to fetch playbooks");
  return response.json();
}

export async function togglePlaybookAPI(playbookId: string, isActive: boolean) {
  const response = await fetch(`${API_BASE_URL}/playbooks/${playbookId}/toggle`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ is_active: isActive }),
  });
  if (!response.ok) throw new Error("Failed to toggle playbook");
  return response.json();
}

export async function fetchExecutions(limit = 50) {
  const response = await fetch(`${API_BASE_URL}/playbooks/executions?limit=${limit}`, { headers: getHeaders() });
  if (!response.ok) throw new Error("Failed to fetch executions");
  return response.json();
}

export async function createPlaybookAPI(playbookData: any) {
  const response = await fetch(`${API_BASE_URL}/playbooks`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(playbookData),
  });
  if (!response.ok) {
    const errData = await response.json();
    throw new Error(errData.detail || "Failed to create playbook");
  }
  return response.json();
}

export async function fetchIncidents(page = 1, limit = 20, params?: Record<string, string>) {
  const url = new URL(`${API_BASE_URL}/incidents`);
  url.searchParams.append("page", String(page));
  url.searchParams.append("limit", String(limit));
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value) url.searchParams.append(key, value);
    });
  }
  const response = await fetch(url.toString(), { headers: getHeaders() });
  if (!response.ok) throw new Error("Failed to fetch incidents");
  return response.json();
}

export async function createIncident(payload: Record<string, any>) {
  const response = await fetch(`${API_BASE_URL}/incidents`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error((errData as any).detail || "Failed to create incident");
  }
  return response.json();
}

export async function fetchThreatIntel(page = 1, limit = 20) {
  const response = await fetch(`${API_BASE_URL}/threat-intel?page=${page}&limit=${limit}`, { headers: getHeaders() });
  if (!response.ok) throw new Error("Failed to fetch threat intel");
  return response.json();
}

export async function fetchSettings() {
  const response = await fetch(`${API_BASE_URL}/settings`, { headers: getHeaders() });
  if (!response.ok) throw new Error("Failed to fetch settings");
  return response.json();
}

export async function updateSettings(payload: Record<string, any>) {
  const response = await fetch(`${API_BASE_URL}/settings`, {
    method: "PUT",
    headers: getHeaders(),
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error("Failed to update settings");
  return response.json();
}

export async function fetchIntegrations() {
  const response = await fetch(`${API_BASE_URL}/integrations`, { headers: getHeaders() });
  if (!response.ok) throw new Error("Failed to fetch integrations");
  return response.json();
}

export async function fetchApiKeys() {
  const response = await fetch(`${API_BASE_URL}/settings/api-keys`, { headers: getHeaders() });
  if (!response.ok) throw new Error("Failed to fetch API keys");
  return response.json();
}

export async function fetchUsers() {
  const response = await fetch(`${API_BASE_URL}/users`, { headers: getHeaders() });
  if (!response.ok) throw new Error("Failed to fetch users");
  return response.json();
}

export async function createUser(payload: { username: string; email: string; password: string; role: string }) {
  const response = await fetch(`${API_BASE_URL}/users`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error((errData as any).detail || "Failed to create user");
  }
  return response.json();
}

export async function updateUser(userId: string, payload: Record<string, any>) {
  const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
    method: "PUT",
    headers: getHeaders(),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error((errData as any).detail || "Failed to update user");
  }
  return response.json();
}
