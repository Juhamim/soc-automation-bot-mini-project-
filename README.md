# 🛡️ SOC Automation Bot: Enterprise SOAR Platform

> **An Asynchronous, Multi-Tiered Security Orchestration, Automation, and Response (SOAR) System**  
> Automating the entire incident lifecycle: Ingestion ──→ Schema Normalization ──→ Threat Intelligence Enrichment ──→ Risk Scoring ──→ Automated Playbook Execution.

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3.1-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Celery](https://img.shields.io/badge/Celery-5.4.0-37814A?logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![Redis](https://img.shields.io/badge/Redis-5.0.4-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![Supabase/PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-orange.svg)](LICENSE)

---

## 📖 Table of Contents
* [✨ Key Features](#-key-features)
* [🏗️ System Architecture & Data Flow](#️-system-architecture--data-flow)
* [💻 Technology Stack](#-technology-stack)
* [🚀 Getting Started (Quick Start)](#-getting-started-quick-start)
  * [Prerequisites](#prerequisites)
  * [1. Clone & Environment Configuration](#1-clone--environment-configuration)
  * [2. Database Setup & Seeding](#2-database-setup--seeding)
  * [3. Start the Backend Services](#3-start-the-backend-services)
  * [4. Start the React Frontend Dashboard](#4-start-the-react-frontend-dashboard)
* [🎬 Running the Live Interactive Demo](#-running-the-live-interactive-demo)
* [🎭 Playbooks & Automated Responses](#-playbooks--automated-responses)
* [📊 REST API Documentation](#-rest-api-documentation)
* [📁 Project Directory Structure](#-project-directory-structure)
* [🛣️ Development Roadmap](#️-development-roadmap)

---

## ✨ Key Features

* **🔌 Multi-Source Alert Ingestion**: Exposes a secure REST API with custom connectors for Wazuh, Splunk, and generic webhooks, allowing seamless SIEM integration.
* **📐 Cyber Schema Normalization**: Standardizes raw, vendor-specific payloads (Wazuh, Splunk, EDRs) into a unified internal format using clean dataclass models.
* **⚡ High-Throughput Task Queue**: Leverages Celery and Redis to handle spikes in security alert volume asynchronously, separating API receipt from processing.
* **🌐 Threat Intelligence Enrichment**: Query multiple Threat Intelligence Providers (VirusTotal, AbuseIPDB, and AlienVault OTX) automatically for observables like IPs, domain names, and file hashes.
* **💾 Multi-Level Cache**: Caches threat intel responses in Redis (TTL: 24h) to avoid rate limit throttling and save operational API costs.
* **🧠 Multi-Dimensional Risk Scoring**: Computes an aggregate threat score (0-100) combining source severity, reputation scores, and asset criticality.
* **🛠️ Automated Response Playbooks**: Triggers customizable, YAML-defined playbooks executing actions such as firewall IP blocking (iptables/AWS), host isolation, Slack alerts, and Jira ticket creation.
* **🖥️ Reactive Analyst Dashboard**: Modern React + TypeScript dashboard with WebSocket notifications for new alerts, incident metrics, threat intelligence details, and an interactive **Playbook Builder**.

---

## 🏗️ System Architecture & Data Flow

The platform utilizes a modern, decoupled, event-driven architecture designed to minimize MTTR (Mean Time To Response) while maximizing ingestion performance.

```
                  ┌───────────────────────────────┐
                  │ Alert Sources (Wazuh, Splunk) │
                  └───────────────┬───────────────┘
                                  │ HTTPS POST
                                  ▼
                  ┌───────────────────────────────┐
                  │   FastAPI Ingestion Engine    │
                  └───────────────┬───────────────┘
                                  │ Enqueue Job
                                  ▼
                  ┌───────────────────────────────┐
                  │      Redis Message Queue      │
                  └───────────────┬───────────────┘
                                  │ Dequeue Task
                                  ▼
                        ┌──────────────────┐
                        │  Celery Workers  │
                        └────────┬─────────┘
                                 │
     ┌───────────────────────────┼───────────────────────────┐
     │ Normalization             │ Threat Intel Query        │ Playbook Execution
     ▼                           ▼                           ▼
┌──────────────┐         ┌───────────────┐           ┌──────────────┐
│ Standardize  │         │ VirusTotal    │           │ Slack Alert  │
│ Schema       │         │ AbuseIPDB     │           │ Jira Ticket  │
│ Dataclasses  │         │ AlienVault    │           │ Firewall Block│
└──────────────┘         └───────────────┘           └──────────────┘
     │                           │                           │
     └───────────────────────────┼───────────────────────────┘
                                 ▼
                     ┌───────────────────────┐
                     │ PostgreSQL (Supabase) │◄──────────────┐
                     └───────────┬───────────┘               │
                                 │ HTTP REST                 │ Websocket
                                 ▼                           │ Sync
                     ┌───────────────────────┐               │
                     │    React Dashboard    ├───────────────┘
                     └───────────────────────┘
```

### Incident Processing Pipeline Flow
1. **Ingest**: A SIEM triggers a webhook, pushing a JSON payload to `/api/v1/alert`. The backend validates the authorization header and schema, returning a job tracking ID within `< 200ms`.
2. **Normalize**: The Celery worker picks up the job and maps vendor fields to standard fields (e.g., standardizing `sourceAddress` or `ip_address` to `src_ip`).
3. **Enrich**: Worker parses observables. It queries the local Redis cache. On a miss, it queries external Threat Intel APIs and updates the cache.
4. **Evaluate & Respond**: The risk scoring engine runs. If the score exceeds configured thresholds, the playbook engine parses the matching active playbook and initiates containment (e.g., calling the firewall APIs, publishing Slack logs, opening Jira tickets).
5. **UI Update**: Changes are committed to PostgreSQL, broadcasting real-time updates to the active React dashboard via WebSockets.

---

## 💻 Technology Stack

| Layer | Component | Description & Rationale |
|:---|:---|:---|
| **Backend** | **FastAPI (Python 3.11)** | Ultra-fast, async web framework. Integrated OpenAPI UI (Swagger) and Pydantic validation. |
| **Worker Queue** | **Celery + Redis** | Industry-standard asynchronous task queue. Handles background tasks and cron jobs securely. |
| **Database** | **PostgreSQL (Supabase)** | Robust relational database using JSONB fields for high-flexibility schemaless logs. |
| **Frontend** | **React (Vite) + TS** | Modern, lightning-fast rendering. Component-driven single-page architecture. |
| **Styling & UI** | **Tailwind CSS v4 + Material UI** | Rich, premium dark-mode styling, charts, and responsive component UI. |
| **Threat Intel** | **VirusTotal, AbuseIPDB, OTX** | Multi-faceted API integrations for real-time observable reputation reporting. |
| **Integrations** | **Slack Webhooks, Jira Cloud** | Real-time security operations communications and incident tracking. |

---

## 🚀 Getting Started (Quick Start)

The local development environment runs the FastAPI server and Celery workers natively on Windows (PowerShell/CMD) and hooks into external services.

### Prerequisites
* **Python 3.11** or higher installed.
* **Node.js v18+** & **npm** installed.
* A running **Redis** server (or a free cloud Redis database instance on [Upstash](https://upstash.com)).
* A running **PostgreSQL** instance (or a free cloud DB on [Supabase](https://supabase.com)).

### 1. Clone & Environment Configuration
Clone the repository and enter the directory:
```bash
git clone https://github.com/Juhamim/soc-automation-bot-mini-project-.git
cd soc-automation-bot-mini-project-/SOC-Automation-Bot-main
```

Create your local `.env` configuration file from the template:
```powershell
# Copy the env template (Windows PowerShell)
copy .env.example .env
```

Open `.env` and configure your credentials. By default, the keys are set to `MOCK`, enabling a fully offline test run without requiring active external API keys.
To run with real data, set the connection URLs:
```env
DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<db>
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

### 2. Setup Virtual Environment & Install Dependencies
Set up the Python environment and install backend requirements:
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment (PowerShell)
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### 3. Database Setup & Seeding
Prepare the Postgres tables and run the migrations/seeding scripts to set up default playbooks and administrator login credentials:
```powershell
# Run Alembic migrations to build the tables
alembic upgrade head

# Seed core playbooks
python scripts/seed_playbook.py
python scripts/seed_additional_playbooks.py

# Seed the administrator user (For Frontend Login)
python scripts/seed_admin_user.py
```

> [!IMPORTANT]  
> The administrator seeding script creates the default analyst login credentials:
> * **Username**: `admin`
> * **Password**: `password123`

### 4. Start the Backend Services
To run the application, start the Web Server and Celery Worker in **two separate terminal windows** (both running inside the activated Python virtual environment).

**Terminal 1: FastAPI API Web Server**
```powershell
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2: Celery Background Worker**
```powershell
celery -A app.core.celery_app worker --loglevel=info -P solo
```
*(Note: `-P solo` or `-P gevent` is recommended when running Celery on Windows environments to avoid pool processes serialization bugs)*.

| Service | Access Link | Description |
|:---|:---|:---|
| **FastAPI REST API** | [http://localhost:8000](http://localhost:8000) | Core JSON ingestion API portal |
| **Interactive Swagger Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Complete interactive API explorer |

### 5. Start the React Frontend Dashboard
In a third terminal window, install npm packages and start the Vite development server:
```powershell
# Navigate to Frontend folder
cd Frontend

# Install node dependencies
npm install

# Start local server
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser and log in using the credentials:
* **Username**: `admin`
* **Password**: `password123`

---

## 🎬 Running the Live Interactive Demo

We have provided a demo script that submits a high-risk alert payload (containing a known malicious IP `185.220.101.14`) to demonstrate automated triage, risk score calculations, and playbook response actions in real-time.

Ensure that the FastAPI backend, Celery worker, Redis, and React frontend are running, then run:
```powershell
# Execute the live demo script inside the virtual environment
python run_demo.py
```

### What Happens in the Demo:
1. The script authenticates as `admin` to receive a JWT Bearer Token.
2. It constructs a high-risk ransomware alert containing the malicious IP.
3. The alert is POSTed to the API and placed in the Redis queue.
4. The Celery worker normalizes the alert, queries VirusTotal/AbuseIPDB/OTX, and updates the threat indicator database.
5. The Risk Score spikes (exceeding the critical threshold).
6. The playbook execution engine activates, blocks the IP address locally, triggers a Slack webhook alert notification, and creates a Jira Incident Ticket.
7. The React dashboard renders the update instantly.

---

## 🎭 Playbooks & Automated Responses

Playbooks are defined as YAML files stored in the database or `/playbooks/` folder. They consist of **triggers** (filter criteria) and **response steps** run sequentially.

### Example Playbook (`high_severity_ip_block.yml`)
```yaml
name: "Block Malicious IP"
description: "Triggers firewall block, slack notification, and Jira ticket for high severity IP threats"
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
    params:
      summary: "SOC Automated Incident Containment Ticket"
```

### Supported Response Actions:
1. **`block_ip`**: Configures rules to block traffic from/to a specific host. (Can execute command-line `iptables -A INPUT -s <ip> -j DROP` or simulate).
2. **`notify_slack`**: Posts structured security incident summaries directly to your Operations center channel.
3. **`create_jira_ticket`**: Auto-generates Atlassian Jira Cloud tasks logging enrichment details for level-2 analysts.

---

## 📊 REST API Documentation

All administrative endpoints require passing the API Key header `X-API-Key: <your_key>` or a JWT Bearer token obtained from `/api/v1/auth/login`.

| Method | Endpoint | Auth Required | Description |
|:---|:---|:---|:---|
| **POST** | `/api/v1/auth/login` | No | Authenticate and obtain a JWT Access Token. |
| **POST** | `/api/v1/alert` | Yes | Ingest a new security alert webhook. |
| **GET** | `/api/v1/alerts` | Yes | List alerts (paginated, with severity/status filters). |
| **GET** | `/api/v1/alerts/{id}` | Yes | Fetch complete details, indicators, and action logs. |
| **POST** | `/api/v1/alerts/{id}/actions/{name}`| Yes | Manually execute an automation playbook action. |
| **GET** | `/api/v1/metrics` | Yes | Fetch dashboard analytics and KPI metrics. |
| **GET** | `/health` | No | System health check and Redis/Postgres connection status. |

### Ingestion Payload Example (`POST /api/v1/alert`)
```bash
curl -X POST http://localhost:8000/api/v1/alert \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "Wazuh SIEM",
    "event_type": "Brute Force Attack",
    "severity": "High",
    "raw_data": {
      "src_ip": "185.220.101.14",
      "attempted_user": "root",
      "failure_count": 42
    }
  }'
```

---

## 📁 Project Directory Structure

```
soc-automation-bot-mini-project/
├── SOC-Automation-Bot-main/
│   ├── app/
│   │   ├── api/                    # API Endpoints, routers, authentication schemas
│   │   ├── core/                   # Global configuration, Celery worker task definitions, aggregation logic
│   │   ├── database/               # SQLAlchemy Models, Session creators, CRUD methods
│   │   └── modules/                # Core SOAR processing components
│   │       ├── normalization/      # Standardizes raw logs to dataclass fields
│   │       ├── enrichment/         # VirusTotal, AbuseIPDB, and AlienVault OTX integrations
│   │       ├── analysis/           # Custom Risk scoring and decision engines
│   │       └── response/           # Playbook executor, firewall blocking, Slack & Jira interfaces
│   ├── Frontend/                   # React (Vite) + TS web dashboard application
│   │   ├── src/
│   │   │   ├── app/
│   │   │   │   ├── pages/          # Pages (Dashboard, Alerts, Playbooks, ThreatIntel, Settings)
│   │   │   │   ├── components/     # UI Components (Alert tables, charts, navigation, modals)
│   │   │   │   └── routes.tsx      # Application routing
│   │   │   └── main.tsx            # React application mount root
│   ├── playbooks/                  # Default playbook YAML configuration structures
│   ├── alembic/                    # Database structure migration scripts
│   ├── scripts/                    # Database seeding and local demo scripts
│   ├── tests/                      # Pytest automated testing suite
│   ├── requirements.txt            # Backend Python dependencies
│   ├── run_demo.py                 # Live interactive demo transmission script
│   └── development_guide.md        # Comprehensive technical architecture guide
```

---

## 🛣️ Development Roadmap

* [x] **Phase 1**: Ingestion API & Celery asynchronous queue backbone.
* [x] **Phase 2**: Multi-API threat intelligence integration, redis caching, and risk scoring.
* [x] **Phase 3**: Extensible response system (Firewall, Slack, Jira) & YAML playbook engine.
* [x] **Phase 4**: Responsive React Frontend Dashboard with real-time websocket synchronization, charts, and a visual playbook builder modal.
* [ ] **Phase 5 (Future)**: 
  * MITRE ATT&CK technique mapping.
  * Multi-Tenancy support for MSSPs (Managed Security Service Providers).
  * Machine learning-driven anomaly detection models for zero-day behaviors.

---

*Developed by the Security Operations Team. For inquiries or contributions, please open an issue or pull request.*
