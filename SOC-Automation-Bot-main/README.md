# SOC Automation Bot 🛡️

> **A SOAR-based Security Incident Automation System**  
> Automates the full lifecycle of security alerts: ingestion → enrichment → risk scoring → playbook response.

![Version](https://img.shields.io/badge/version-1.2.0-blue) ![Python](https://img.shields.io/badge/python-3.11-green) ![FastAPI](https://img.shields.io/badge/FastAPI-0.111-teal) ![License](https://img.shields.io/badge/license-MIT-orange)

---

## 🏗️ Architecture

```
Alert Source (Wazuh/Splunk)
        ↓
FastAPI Ingestion Service  ──→  Redis Queue
                                     ↓
                              Celery Worker
                            ┌────────────────┐
                            │  Normalize      │
                            │  Enrich (VT/   │
                            │  AbuseIPDB/OTX)│
                            │  Risk Score     │
                            │  Run Playbook   │
                            └────────────────┘
                            ↓           ↓
                      PostgreSQL    Actions
                          ↓       (Slack / Jira / Firewall)
                    React Dashboard
```

## 🚀 Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed

### 1. Clone & Configure

```bash
cd "c:\Users\USER\Desktop\New folder\soc-prj"

# Create environment file
copy .env.example .env
```

### 2. Setup Virtual Environment & Install Dependencies

```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Start The Core Services

Since this project now runs entirely natively without Docker, you will need to start the web server and the background worker in **two separate terminal windows**.

**Terminal 1 (The Web API):**
```bash
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 (The CELERY Background Worker):**
```bash
# Ensure you are in the same activated virtual environment
celery -A app.core.celery_app worker --loglevel=info
```

| Service | URL | Description |
|---------|-----|-------------|
| **API** | http://localhost:8000 | FastAPI Ingestion & REST |
| **Swagger Docs** | http://localhost:8000/docs | Interactive API docs |

### 4. Send a Test Alert

```bash
curl -X POST http://localhost:8000/api/v1/alert \
  -H "X-API-Key: dev-secret-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "Wazuh",
    "event_type": "brute_force",
    "src_ip": "45.33.32.156",
    "severity": "High"
  }'
```

**Response:**
```json
{
  "job_id": "<celery-task-uuid>",
  "alert_id": "<alert-uuid>",
  "status": "accepted",
  "message": "Alert queued for processing."
}
```

### 4. View Processed Alert

```bash
curl http://localhost:8000/api/v1/alerts/<alert_id> \
  -H "X-API-Key: dev-secret-key-change-in-production"
```

---

## 📁 Project Structure

```
soc-prj/
├── app/
│   ├── api/               # FastAPI routes, models, auth
│   ├── core/              # Config, Celery, task orchestrator
│   ├── database/          # SQLAlchemy models, CRUD, session
│   └── modules/
│       ├── normalization/ # Field mapping (Wazuh, Splunk → standard)
│       ├── enrichment/    # VirusTotal, AbuseIPDB, OTX enrichers
│       ├── analysis/      # Risk scoring engine
│       └── response/      # Host-based Blocking, Slack, Jira, Playbook engine
├── playbooks/             # YAML playbook definitions
├── alembic/               # Database migrations
├── tests/                 # Unit & integration tests
├── requirements.txt
└── .env.example
```

---

## 🔑 API Keys

All keys stored in `.env`. Set to `MOCK` by default — the system runs fully without real keys.

| Key | Get it from | Used for |
|-----|-------------|----------|
| `VIRUSTOTAL_API_KEY` | [virustotal.com](https://virustotal.com) | IP/Hash enrichment |
| `ABUSEIPDB_API_KEY` | [abuseipdb.com](https://abuseipdb.com) | IP reputation |
| `OTX_API_KEY` | [otx.alienvault.com](https://otx.alienvault.com) | Threat indicators |
| `SLACK_WEBHOOK_URL` | [api.slack.com](https://api.slack.com/messaging/webhooks) | Alert notifications |
| `JIRA_API_TOKEN` | [atlassian.com](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/) | Incident tickets |

---

## 🧪 Running Tests

```bash
# Install dependencies locally (optional, tests also run in Docker)
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v
```

---

## 🎭 Playbooks

Add YAML files to `/playbooks/` to define automated response workflows:

```yaml
name: "Block Malicious IP"
is_active: true
trigger:
  severity: ["High", "Critical"]
steps:
  - action: "block_ip"
    params:
      chain: "INPUT"
      simulate: true
  - action: "notify_slack"
    params:
      channel: "#security-alerts"
  - action: "create_jira_ticket"
    params: {}
```

**Available actions:** `block_ip`, `notify_slack`, `create_jira_ticket`

---

## 📊 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/alert` | ✅ | Ingest a new alert |
| `GET` | `/api/v1/alerts` | ✅ | List alerts (paginated) |
| `GET` | `/api/v1/alerts/{id}` | ✅ | Get alert details |
| `POST` | `/api/v1/alerts/{id}/actions/{name}` | ✅ | Trigger manual action |
| `GET` | `/api/v1/metrics` | ✅ | Dashboard metrics |
| `GET` | `/health` | ❌ | Health check |

**Auth:** Include `X-API-Key: <your-key>` header (configured via `API_KEY` in `.env`)

---

## 🛣️ Roadmap

- **Phase 1 (Complete):** Core ingestion pipeline + managed cloud PostgreSQL + Celery
- **Phase 2 (Complete):** Threat intel enrichment + risk scoring
- **Phase 3 (Complete):** Playbook engine + host-based and external response actions
- **Phase 4 (Next):** React dashboard with alert table, charts, alert detail page
- **Phase 5:** MITRE ATT&CK mapping, ML anomaly detection, multi-tenancy
