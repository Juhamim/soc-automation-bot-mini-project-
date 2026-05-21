# SOC Automation Bot - Development Guide

**Version:** 1.1  
**Last Updated:** 2026-02-15

---

## Table of Contents
1. [Primary User Journey](#primary-user-journey)
2. [MVP Dataflow](#mvp-dataflow)
3. [Component Architecture Hierarchy](#component-architecture-hierarchy)
4. [Development Timeline](#development-timeline)
5. [State Management Flow](#state-management-flow)
6. [Development Strategy & Approach](#development-strategy--approach)
7. [Technical Priority Matrix](#technical-priority-matrix)
8. [Phase-by-Phase Implementation](#phase-by-phase-implementation)
9. [Flow Diagrams](#flow-diagrams)
10. [Development Environment Setup](#development-environment-setup)
11. [Testing Strategy](#testing-strategy)
12. [Deployment Strategy](#deployment-strategy)

---

## Primary User Journey

### SOC Analyst Alert Investigation Workflow

This diagram shows the primary user journey for a SOC analyst using the automation bot.

```mermaid
journey
    title SOC Analyst Daily Workflow with Automation Bot
    section Morning Review
      Login to Dashboard: 5: Analyst
      View Alert Summary: 5: Analyst
      Check Critical Alerts: 4: Analyst
    section Alert Investigation
      Select High-Priority Alert: 5: Analyst
      Review Enrichment Data: 5: Analyst, Bot
      Analyze Risk Score: 4: Analyst, Bot
      Check Automated Actions: 5: Bot
    section Decision Making
      Review Playbook Execution: 4: Analyst, Bot
      Verify IP Block Status: 5: Bot
      Check Slack Notifications: 5: Bot
      Manual Override if Needed: 3: Analyst
    section Case Management
      Create Jira Ticket: 5: Bot
      Add Investigation Notes: 4: Analyst
      Close False Positives: 5: Analyst
      Escalate Critical Issues: 3: Analyst
    section End of Day
      Review Metrics Dashboard: 5: Analyst
      Check MTTR Improvements: 5: Analyst
      Plan Next Day Priorities: 4: Analyst
```

### Detailed User Flow (Alert Triage)

```mermaid
flowchart TD
    Start([Analyst Logs In]) --> Dashboard[View Dashboard]
    Dashboard --> Filter{Filter Alerts}
    
    Filter -->|By Severity| Critical[Critical Alerts]
    Filter -->|By Status| New[New Alerts]
    Filter -->|By Source| SIEM[SIEM Alerts]
    
    Critical --> Select[Select Alert]
    New --> Select
    SIEM --> Select
    
    Select --> Detail[View Alert Detail Page]
    Detail --> Review[Review Enrichment Data]
    
    Review --> Check{Automated Actions<br/>Executed?}
    
    Check -->|Yes| Verify[Verify Action Success]
    Check -->|No| Manual[Trigger Manual Action]
    
    Verify --> Assess{Threat<br/>Legitimate?}
    Manual --> Assess
    
    Assess -->|True Positive| Escalate[Escalate to L2/L3]
    Assess -->|False Positive| Close[Mark as False Positive]
    Assess -->|Needs More Info| Investigate[Deep Investigation]
    
    Escalate --> Ticket[Jira Ticket Created]
    Close --> Update[Update Alert Status]
    Investigate --> External[Query External Tools]
    
    External --> Assess
    Ticket --> End([Complete])
    Update --> End
    
    style Start fill:#90EE90
    style End fill:#FFB6C1
    style Assess fill:#FFD700
```

---

## MVP Dataflow

### End-to-End Data Flow (MVP)

This diagram shows how data flows through the entire system from alert ingestion to analyst review.

```mermaid
flowchart LR
    subgraph "External Sources"
        SIEM[SIEM<br/>Splunk/Wazuh]
        IDS[IDS/IPS]
        EDR[EDR System]
    end
    
    subgraph "Ingestion Layer"
        API[FastAPI<br/>Ingestion Service]
        Validate[Schema<br/>Validator]
    end
    
    subgraph "Queue Layer"
        Redis[(Redis Queue)]
    end
    
    subgraph "Processing Layer"
        Worker[Celery Worker]
        Normalize[Normalizer]
        Enrich[Enrichment<br/>Engine]
        Analyze[Risk<br/>Analyzer]
        Execute[Playbook<br/>Executor]
    end
    
    subgraph "External APIs"
        VT[VirusTotal]
        AB[AbuseIPDB]
        OTX[AlienVault]
    end
    
    subgraph "Action Layer"
        FW[Firewall API]
        Slack[Slack API]
        Jira[Jira API]
    end
    
    subgraph "Storage Layer"
        DB[(PostgreSQL)]
        Cache[(Redis Cache)]
        Logs[(Elasticsearch)]
    end
    
    subgraph "Presentation Layer"
        UI[React Dashboard]
        API2[REST API]
    end
    
    SIEM --> API
    IDS --> API
    EDR --> API
    
    API --> Validate
    Validate --> Redis
    
    Redis --> Worker
    Worker --> Normalize
    Normalize --> Enrich
    
    Enrich --> VT
    Enrich --> AB
    Enrich --> OTX
    Enrich --> Cache
    
    Enrich --> Analyze
    Analyze --> Execute
    
    Execute --> FW
    Execute --> Slack
    Execute --> Jira
    
    Worker --> DB
    Worker --> Logs
    
    DB --> API2
    Logs --> API2
    API2 --> UI
    
    style API fill:#4A90E2
    style Worker fill:#7ED321
    style DB fill:#BD10E0
    style UI fill:#50E3C2
```

---

## Component Architecture Hierarchy

### System Component Hierarchy

```mermaid
graph TD
    Root[SOC Automation Bot]
    
    Root --> Frontend[Frontend Layer]
    Root --> Backend[Backend Layer]
    Root --> Data[Data Layer]
    Root --> External[External Integrations]
    
    Frontend --> UI[React Dashboard]
    UI --> Pages[Pages]
    UI --> Components[Components]
    UI --> State[State Management]
    
    Pages --> DashPage[Dashboard Page]
    Pages --> AlertPage[Alert Detail Page]
    Pages --> MetricsPage[Metrics Page]
    
    Components --> Table[Alert Table]
    Components --> Cards[Metric Cards]
    Components --> Charts[Charts]
    Components --> Actions[Action Buttons]
    
    State --> Redux[Redux Store]
    Redux --> AlertSlice[Alert Slice]
    Redux --> UserSlice[User Slice]
    
    Backend --> API[API Service]
    Backend --> Worker[Worker Service]
    Backend --> Core[Core Logic]
    
    API --> Routes[Route Handlers]
    API --> Auth[Authentication]
    API --> Middleware[Middleware]
    
    Routes --> AlertRoutes[Alert Routes]
    Routes --> MetricRoutes[Metric Routes]
    Routes --> ActionRoutes[Action Routes]
    
    Worker --> Tasks[Celery Tasks]
    Tasks --> ProcessTask[Process Alert Task]
    Tasks --> EnrichTask[Enrichment Task]
    Tasks --> ActionTask[Action Task]
    
    Core --> Modules[Modules]
    Modules --> Ingestion[Ingestion Module]
    Modules --> Normalization[Normalization Module]
    Modules --> Enrichment[Enrichment Module]
    Modules --> Analysis[Analysis Module]
    Modules --> Response[Response Module]
    
    Enrichment --> VTProvider[VirusTotal Provider]
    Enrichment --> ABProvider[AbuseIPDB Provider]
    Enrichment --> OTXProvider[OTX Provider]
    
    Response --> FirewallAction[Firewall Action]
    Response --> NotifyAction[Notification Action]
    Response --> TicketAction[Ticketing Action]
    
    Data --> Database[PostgreSQL]
    Data --> Cache[Redis Cache]
    Data --> Logs[Elasticsearch]
    
    Database --> Models[ORM Models]
    Models --> AlertModel[Alert Model]
    Models --> EnrichModel[Enrichment Model]
    Models --> ActionModel[Action Model]
    Models --> UserModel[User Model]
    
    External --> ThreatIntel[Threat Intel APIs]
    External --> ActionAPIs[Action APIs]
    External --> Monitoring[Monitoring Tools]
    
    ThreatIntel --> VT2[VirusTotal]
    ThreatIntel --> AB2[AbuseIPDB]
    
    ActionAPIs --> FW2[Firewall]
    ActionAPIs --> Slack2[Slack]
    ActionAPIs --> Jira2[Jira]
    
    style Root fill:#FF6B6B
    style Frontend fill:#4ECDC4
    style Backend fill:#95E1D3
    style Data fill:#F38181
    style External fill:#AA96DA
```

---

## Development Timeline

### 12-Week MVP Development Timeline

```mermaid
gantt
    title SOC Automation Bot - MVP Development Timeline
    dateFormat YYYY-MM-DD
    section Phase 0: Setup
    Environment Setup           :p0, 2026-02-17, 5d
    Docker Configuration        :p0-1, 2026-02-17, 3d
    Database Setup             :p0-2, 2026-02-19, 2d
    
    section Phase 1: Core Pipeline
    API Development            :p1, 2026-02-24, 7d
    Queue Integration          :p1-1, 2026-02-26, 5d
    Worker Implementation      :p1-2, 2026-03-03, 7d
    Database Models            :p1-3, 2026-03-05, 5d
    Integration Testing        :p1-4, 2026-03-10, 3d
    
    section Phase 2: Enrichment
    Enrichment Framework       :p2, 2026-03-13, 5d
    VirusTotal Integration     :p2-1, 2026-03-17, 3d
    AbuseIPDB Integration      :p2-2, 2026-03-19, 3d
    Caching Layer             :p2-3, 2026-03-21, 3d
    Risk Scoring Engine        :p2-4, 2026-03-24, 5d
    
    section Phase 3: Response
    Playbook Engine            :p3, 2026-03-31, 7d
    Firewall Integration       :p3-1, 2026-04-02, 5d
    Slack Notifications        :p3-2, 2026-04-07, 3d
    Jira Integration          :p3-3, 2026-04-09, 5d
    Action Logging            :p3-4, 2026-04-11, 3d
    
    section Phase 4: Dashboard
    Frontend Setup            :p4, 2026-04-14, 3d
    Dashboard Page            :p4-1, 2026-04-16, 5d
    Alert Detail Page         :p4-2, 2026-04-21, 5d
    Metrics & Charts          :p4-3, 2026-04-23, 5d
    API Integration           :p4-4, 2026-04-28, 3d
    
    section Phase 5: Polish
    E2E Testing               :p5, 2026-05-01, 5d
    Documentation             :p5-1, 2026-05-05, 3d
    Performance Optimization   :p5-2, 2026-05-07, 3d
    Security Hardening        :p5-3, 2026-05-09, 3d
    MVP Release               :milestone, 2026-05-12, 0d
```

---

## State Management Flow

### Alert State Machine

```mermaid
stateDiagram-v2
    [*] --> New: Alert Ingested
    
    New --> Enriching: Start Processing
    Enriching --> Analyzing: Enrichment Complete
    
    Analyzing --> Low: Risk Score < 40
    Analyzing --> Medium: Risk Score 40-70
    Analyzing --> High: Risk Score 70-90
    Analyzing --> Critical: Risk Score > 90
    
    Low --> Closed: Auto-Close
    Medium --> InProgress: Analyst Review
    High --> InProgress: Playbook Executed
    Critical --> InProgress: Playbook Executed
    
    InProgress --> Investigating: Deep Dive
    InProgress --> Escalated: L2/L3 Handoff
    InProgress --> FalsePositive: Analyst Decision
    InProgress --> Resolved: Threat Mitigated
    
    Investigating --> InProgress: More Data Needed
    Investigating --> Resolved: Investigation Complete
    
    Escalated --> Resolved: External Team Resolves
    FalsePositive --> Closed: Mark as FP
    Resolved --> Closed: Close Ticket
    
    Closed --> [*]
    
    note right of New
        Initial state after
        API ingestion
    end note
    
    note right of Enriching
        Querying threat intel
        providers
    end note
    
    note right of InProgress
        Awaiting analyst
        action or playbook
        completion
    end note
```

### Frontend State Management (Redux)

```mermaid
flowchart TD
    Component[React Component] --> Dispatch[Dispatch Action]
    
    Dispatch --> Action[Action Creator]
    Action --> Middleware{Middleware}
    
    Middleware -->|Async| Thunk[Redux Thunk]
    Middleware -->|Sync| Reducer[Reducer]
    
    Thunk --> API[API Call]
    API --> Success{Success?}
    
    Success -->|Yes| SuccessAction[Success Action]
    Success -->|No| ErrorAction[Error Action]
    
    SuccessAction --> Reducer
    ErrorAction --> Reducer
    
    Reducer --> Store[(Redux Store)]
    Store --> Selector[Selector]
    Selector --> Component
    
    style Component fill:#61DAFB
    style Store fill:#764ABC
    style API fill:#4A90E2
```

---

## Development Strategy & Approach

### Agile Development Strategy

```mermaid
mindmap
  root((Development<br/>Strategy))
    Methodology
      2-Week Sprints
      Daily Standups
      Sprint Reviews
      Retrospectives
    Principles
      Start Simple
      Iterate Fast
      Test Early
      Security First
      Document Always
    Team Structure
      Backend Dev
      Frontend Dev
      DevOps Engineer
      Security Analyst
    Tools
      Git/GitHub
      Jira/Linear
      Slack
      Docker
      CI/CD Pipeline
    Quality Gates
      Code Review
      Unit Tests 80%+
      Integration Tests
      Security Scan
      Performance Check
```

### Development Workflow

```mermaid
flowchart TD
    Start([Sprint Planning]) --> Backlog[Select User Stories]
    Backlog --> Design[Technical Design]
    Design --> Branch[Create Feature Branch]
    
    Branch --> Dev[Development]
    Dev --> UnitTest[Write Unit Tests]
    UnitTest --> LocalTest[Local Testing]
    
    LocalTest --> Pass{Tests Pass?}
    Pass -->|No| Dev
    Pass -->|Yes| Commit[Commit Code]
    
    Commit --> PR[Create Pull Request]
    PR --> Review[Code Review]
    
    Review --> Approved{Approved?}
    Approved -->|No| Dev
    Approved -->|Yes| Merge[Merge to Main]
    
    Merge --> CI[CI Pipeline]
    CI --> Build[Build & Test]
    Build --> Deploy[Deploy to Staging]
    
    Deploy --> E2E[E2E Tests]
    E2E --> QA{QA Pass?}
    
    QA -->|No| Bug[Create Bug Ticket]
    QA -->|Yes| Prod[Deploy to Production]
    
    Bug --> Backlog
    Prod --> Monitor[Monitor Metrics]
    Monitor --> End([Sprint Complete])
    
    style Start fill:#90EE90
    style End fill:#FFB6C1
    style Approved fill:#FFD700
    style QA fill:#FFD700
```

---

## Technical Priority Matrix

### Feature Priority Matrix (MoSCoW Method)

```mermaid
quadrantChart
    title Feature Priority Matrix
    x-axis Low Effort --> High Effort
    y-axis Low Impact --> High Impact
    quadrant-1 Plan Carefully
    quadrant-2 Do First
    quadrant-3 Do Later
    quadrant-4 Quick Wins
    
    Alert Ingestion API: [0.3, 0.9]
    VirusTotal Integration: [0.4, 0.85]
    Risk Scoring: [0.5, 0.8]
    Slack Notifications: [0.2, 0.7]
    IP Blocking: [0.6, 0.75]
    Dashboard UI: [0.7, 0.7]
    Jira Integration: [0.5, 0.6]
    MITRE Mapping: [0.8, 0.5]
    Multi-tenancy: [0.9, 0.4]
    ML Anomaly Detection: [0.95, 0.6]
```

### Implementation Priority Table

| Priority | Feature | Complexity | Impact | Phase | Dependencies |
|----------|---------|------------|--------|-------|--------------|
| **P0** | Alert Ingestion API | Medium | Critical | 1 | None |
| **P0** | Database Models | Medium | Critical | 1 | None |
| **P0** | Celery Worker | Medium | Critical | 1 | Redis, DB |
| **P1** | VirusTotal Integration | Low | High | 2 | API Key |
| **P1** | Risk Scoring Engine | Medium | High | 2 | Enrichment |
| **P1** | Slack Notifications | Low | High | 3 | Webhook URL |
| **P2** | IP Blocking (iptables) | Medium | High | 3 | Firewall Access |
| **P2** | Dashboard UI | High | Medium | 4 | API Complete |
| **P2** | Jira Integration | Medium | Medium | 3 | Jira API |
| **P3** | AbuseIPDB Integration | Low | Medium | 2 | API Key |
| **P3** | Metrics & Charts | Medium | Medium | 4 | Dashboard |
| **P4** | MITRE ATT&CK Mapping | High | Low | 5 | Alert Data |
| **P4** | ML Anomaly Detection | Very High | Medium | 5 | Historical Data |

### Technical Debt vs Feature Development

```mermaid
pie title Development Time Allocation (Per Sprint)
    "New Features" : 50
    "Bug Fixes" : 20
    "Technical Debt" : 15
    "Testing" : 10
    "Documentation" : 5
```

---

## Development Approach

### Recommended Development Methodology

**Iterative Agile Approach** with 2-week sprints focusing on vertical slices of functionality.

#### Core Principles
1. **Start Simple, Iterate Fast:** Build the simplest working version first
2. **Test Early, Test Often:** Write tests alongside code
3. **Document as You Go:** Update docs with each feature
4. **Security First:** Never defer security considerations

### Development Phases Overview

```mermaid
graph LR
    A[Phase 0: Setup] --> B[Phase 1: Core Pipeline]
    B --> C[Phase 2: Enrichment]
    C --> D[Phase 3: Response Actions]
    D --> E[Phase 4: Dashboard]
    E --> F[Phase 5: Advanced Features]
    
    style A fill:#e1f5ff
    style B fill:#fff4e1
    style C fill:#ffe1f5
    style D fill:#e1ffe1
    style E fill:#f5e1ff
    style F fill:#ffe1e1
```

---

## Phase-by-Phase Implementation

### Phase 0: Environment Setup (Week 1)

**Goal:** Set up development infrastructure

#### Tasks
- [ ] Initialize Git repository
- [ ] Set up Python virtual environment
- [ ] Configure Docker & Docker Compose
- [ ] Set up PostgreSQL database
- [ ] Set up Redis
- [ ] Configure environment variables (`.env`)
- [ ] Create initial project structure

#### Deliverables
- Working `docker-compose.yml`
- Database migrations (Alembic)
- Basic README with setup instructions

---

### Phase 1: Core Pipeline (Weeks 2-3)

**Goal:** Build the alert ingestion and processing backbone

```mermaid
flowchart TD
    Start([Start Development]) --> API[Build FastAPI Ingestion Endpoint]
    API --> Validate[Add Schema Validation]
    Validate --> Queue[Integrate Redis Queue]
    Queue --> Worker[Create Celery Worker]
    Worker --> DB[Store Alert in PostgreSQL]
    DB --> Test[Write Integration Tests]
    Test --> End([Phase 1 Complete])
    
    style Start fill:#90EE90
    style End fill:#FFB6C1
```

#### Key Components to Build
1. **API Layer** (`app/api/`)
   - `main.py`: FastAPI app initialization
   - `routes.py`: `/api/v1/alert` endpoint
   - `models.py`: Pydantic request/response models
   - `auth.py`: API key validation middleware

2. **Core Logic** (`app/core/`)
   - `celery_app.py`: Celery configuration
   - `tasks.py`: `process_alert` task

3. **Database** (`app/database/`)
   - `models.py`: SQLAlchemy Alert model
   - `crud.py`: Create/Read operations

#### Testing Checklist
- [ ] POST valid alert → Returns 202 with job_id
- [ ] POST invalid JSON → Returns 400
- [ ] POST without API key → Returns 401
- [ ] Worker processes alert and saves to DB

---

### Phase 2: Threat Intelligence Enrichment (Weeks 4-5)

**Goal:** Integrate external threat intel APIs

```mermaid
flowchart TD
    Alert[Alert Received] --> Extract[Extract Observables]
    Extract --> Cache{Check Cache}
    Cache -->|Hit| UseCache[Use Cached Result]
    Cache -->|Miss| VT[Query VirusTotal]
    VT --> Abuse[Query AbuseIPDB]
    Abuse --> OTX[Query AlienVault OTX]
    OTX --> Store[Store Enrichment Results]
    UseCache --> Store
    Store --> Score[Calculate Risk Score]
    Score --> End([Enrichment Complete])
    
    style Alert fill:#FFE4B5
    style End fill:#98FB98
```

#### Key Components to Build
1. **Enrichment Module** (`app/modules/enrichment/`)
   - `base.py`: Abstract enrichment provider
   - `virustotal.py`: VirusTotal integration
   - `abuseipdb.py`: AbuseIPDB integration
   - `otx.py`: AlienVault OTX integration
   - `cache.py`: Redis caching layer

2. **Analysis Module** (`app/modules/analysis/`)
   - `risk_scorer.py`: Risk score calculation logic

#### Configuration Needed
```python
# .env
VIRUSTOTAL_API_KEY=your_key_here
ABUSEIPDB_API_KEY=your_key_here
OTX_API_KEY=your_key_here
ENRICHMENT_CACHE_TTL=86400  # 24 hours
```

#### Testing Checklist
- [ ] Extract IPs, domains, hashes from alert
- [ ] Query each TIP and get results
- [ ] Cache results in Redis
- [ ] Calculate accurate risk score
- [ ] Handle API rate limits gracefully

---

### Phase 3: Automated Response Actions (Weeks 6-7)

**Goal:** Implement playbook execution engine

```mermaid
stateDiagram-v2
    [*] --> EvaluateAlert
    EvaluateAlert --> CheckSeverity
    
    CheckSeverity --> Low: Score < 40
    CheckSeverity --> Medium: 40-70
    CheckSeverity --> High: 70-90
    CheckSeverity --> Critical: > 90
    
    Low --> LogOnly
    Medium --> NotifySlack
    High --> BlockIP
    Critical --> BlockIP_IsolateHost
    
    LogOnly --> [*]
    NotifySlack --> [*]
    BlockIP --> NotifySlack
    BlockIP_IsolateHost --> NotifySlack
```

#### Key Components to Build
1. **Response Module** (`app/modules/response/`)
   - `base.py`: Abstract action executor
   - `firewall.py`: IP blocking (iptables/AWS SG)
   - `notification.py`: Slack/Email notifications
   - `ticketing.py`: Jira integration
   - `playbook_engine.py`: Playbook parser and executor

2. **Playbook Definition** (YAML format)
```yaml
# playbooks/high_severity_ip_block.yml
name: "Block Malicious IP"
trigger:
  severity: ["High", "Critical"]
  observable_type: "ip"
steps:
  - action: "block_ip_iptables"
    params:
      chain: "INPUT"
  - action: "notify_slack"
    params:
      channel: "#security-alerts"
```

#### Testing Checklist
- [ ] Parse YAML playbook correctly
- [ ] Execute actions in sequence
- [ ] Log action outcomes
- [ ] Handle action failures gracefully
- [ ] Test Slack notification delivery

---

### Phase 4: Web Dashboard (Weeks 8-9)

**Goal:** Build React-based monitoring UI

```mermaid
graph TD
    subgraph "Frontend Components"
        A[Dashboard Page] --> B[Alert List Table]
        A --> C[Metrics Cards]
        A --> D[Charts - Recharts]
        
        E[Alert Detail Page] --> F[Raw Data Viewer]
        E --> G[Enrichment Results]
        E --> H[Action History Timeline]
        E --> I[Manual Action Buttons]
    end
    
    subgraph "API Endpoints"
        J[GET /api/v1/alerts]
        K[GET /api/v1/alerts/:id]
        L[POST /api/v1/alerts/:id/actions/:name]
        M[GET /api/v1/metrics]
    end
    
    B --> J
    F --> K
    I --> L
    C --> M
```

#### Key Components to Build
1. **Backend API Extensions**
   - Add pagination to alerts endpoint
   - Create metrics aggregation endpoint
   - Add manual action trigger endpoint

2. **Frontend** (`frontend/`)
   - `pages/Dashboard.jsx`: Main overview
   - `pages/AlertDetail.jsx`: Single alert view
   - `components/AlertTable.jsx`: Reusable table
   - `components/MetricsCard.jsx`: Stats display

#### Testing Checklist
- [ ] Dashboard loads and displays alerts
- [ ] Pagination works correctly
- [ ] Alert detail page shows all data
- [ ] Manual actions can be triggered
- [ ] Real-time updates (WebSocket/polling)

---

### Phase 5: Advanced Features (Weeks 10+)

**Goal:** Add production-ready features

#### Features to Implement
1. **Human-in-the-Loop Approvals**
   - Slack interactive buttons
   - Approval workflow state machine

2. **Alert Correlation**
   - Group related alerts
   - Pattern detection

3. **MITRE ATT&CK Mapping**
   - Tag alerts with tactics/techniques
   - Visualization of attack chain

---

## Flow Diagrams

### Enrichment Flow (Detailed)

```mermaid
sequenceDiagram
    participant Worker
    participant Cache as Redis Cache
    participant VT as VirusTotal
    participant AB as AbuseIPDB
    participant DB as Database

    Worker->>Worker: Extract IP: 192.168.1.50
    Worker->>Cache: GET enrichment:ip:192.168.1.50
    
    alt Cache Hit
        Cache-->>Worker: Return cached data
    else Cache Miss
        Worker->>VT: GET /ip-address/192.168.1.50
        VT-->>Worker: {malicious_score: 8/90}
        
        Worker->>AB: GET /check/192.168.1.50
        AB-->>Worker: {abuseConfidence: 100}
        
        Worker->>Cache: SET enrichment:ip:192.168.1.50 (TTL: 24h)
        Worker->>DB: INSERT INTO enrichment_results
    end
    
    Worker->>Worker: Calculate Risk Score: 85
```

### Playbook Execution Flow

```mermaid
flowchart TD
    Start([Alert Classified]) --> Load[Load Matching Playbooks]
    Load --> Filter{Filter by Severity}
    
    Filter -->|Critical| PB1[Playbook: Block + Isolate]
    Filter -->|High| PB2[Playbook: Block IP]
    Filter -->|Medium| PB3[Playbook: Notify Only]
    
    PB1 --> Step1[Step 1: Block IP]
    Step1 --> Step2[Step 2: Isolate Host]
    Step2 --> Step3[Step 3: Create Jira Ticket]
    Step3 --> Step4[Step 4: Notify Slack]
    
    PB2 --> Step5[Step 1: Block IP]
    Step5 --> Step6[Step 2: Notify Slack]
    
    PB3 --> Step7[Step 1: Send Email]
    
    Step4 --> Log[Log All Actions]
    Step6 --> Log
    Step7 --> Log
    
    Log --> End([Playbook Complete])
    
    style Start fill:#FFD700
    style End fill:#32CD32
```

### Deployment Architecture

```mermaid
graph TB
    subgraph "Docker Compose Stack"
        API[API Container<br/>FastAPI]
        Worker1[Worker Container 1<br/>Celery]
        Worker2[Worker Container 2<br/>Celery]
        Redis[(Redis<br/>Queue + Cache)]
        DB[(PostgreSQL<br/>Database)]
        UI[Frontend Container<br/>Next.js]
        
        API --> Redis
        Worker1 --> Redis
        Worker2 --> Redis
        API --> DB
        Worker1 --> DB
        Worker2 --> DB
        UI --> API
    end
    
    External[External Alert Sources] --> API
    Worker1 --> TIP[Threat Intel APIs]
    Worker2 --> TIP
    Worker1 --> Actions[Firewalls/Slack/Jira]
    Worker2 --> Actions
    
    style API fill:#4A90E2
    style Worker1 fill:#7ED321
    style Worker2 fill:#7ED321
    style Redis fill:#F5A623
    style DB fill:#BD10E0
    style UI fill:#50E3C2
```

---

## Development Environment Setup

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Node.js 18+ (for frontend)
- Git

### Initial Setup Commands

```bash
# Clone repository
git clone <repo-url>
cd soc-automation-bot

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Start infrastructure
docker-compose up -d postgres redis

# Run database migrations
alembic upgrade head

# Start API server (development)
uvicorn app.api.main:app --reload --port 8000

# Start Celery worker (separate terminal)
celery -A app.core.celery_app worker --loglevel=info

# Start frontend (separate terminal)
cd frontend
npm install
npm run dev
```

---

## Testing Strategy

### Test Pyramid

```mermaid
graph TD
    A[E2E Tests<br/>10%] --> B[Integration Tests<br/>30%]
    B --> C[Unit Tests<br/>60%]
    
    style A fill:#FF6B6B
    style B fill:#4ECDC4
    style C fill:#95E1D3
```

### Unit Tests
- Test individual functions (enrichment, scoring, parsing)
- Mock external API calls
- Fast execution (< 1 second total)

### Integration Tests
- Test API endpoints with real database
- Test Celery task execution
- Use Docker containers for dependencies

### E2E Tests
- Simulate full alert lifecycle
- Test UI interactions (Playwright/Cypress)
- Run in staging environment

### Example Test Structure
```python
# tests/unit/test_risk_scorer.py
def test_calculate_risk_score_high_threat():
    alert = {
        "severity": "High",
        "enrichment": {"vt_score": 10, "abuse_confidence": 100}
    }
    score = calculate_risk_score(alert)
    assert score >= 70

# tests/integration/test_alert_ingestion.py
def test_post_alert_creates_db_record(client, db_session):
    response = client.post("/api/v1/alert", json=sample_alert)
    assert response.status_code == 202
    alert = db_session.query(Alert).first()
    assert alert is not None
```

---

## Deployment Strategy

### Development
- Local Docker Compose
- Hot reload enabled
- Debug logging

### Staging
- AWS ECS or DigitalOcean App Platform
- Separate database instance
- Real external API integrations

### Production
- Kubernetes cluster (optional for scale)
- High availability (3+ worker replicas)
- Monitoring: Prometheus + Grafana
- Logging: ELK Stack
- Secrets: AWS Secrets Manager / HashiCorp Vault

### CI/CD Pipeline

```mermaid
flowchart LR
    A[Git Push] --> B[GitHub Actions]
    B --> C[Run Tests]
    C --> D{Tests Pass?}
    D -->|Yes| E[Build Docker Images]
    D -->|No| F[Notify Developer]
    E --> G[Push to Registry]
    G --> H[Deploy to Staging]
    H --> I[Run E2E Tests]
    I --> J{E2E Pass?}
    J -->|Yes| K[Deploy to Production]
    J -->|No| F
    
    style A fill:#90EE90
    style K fill:#FFD700
    style F fill:#FF6347
```

---

## Best Practices

### Code Organization
- Keep modules small and focused
- Use dependency injection
- Follow PEP 8 style guide

### Security
- Never commit secrets to Git
- Validate all inputs
- Use parameterized SQL queries
- Implement rate limiting

### Performance
- Use async/await for I/O operations
- Batch database operations
- Implement caching strategically
- Monitor query performance

### Documentation
- Docstrings for all public functions
- API documentation (Swagger/OpenAPI)
- Architecture Decision Records (ADRs)

---

## Next Steps

1. **Review this guide** and the PRD thoroughly
2. **Set up your development environment** (Phase 0)
3. **Create a project board** (GitHub Projects/Jira) with tasks
4. **Start with Phase 1** - build the core pipeline
5. **Iterate and test** each phase before moving forward

**Remember:** It's better to have a working simple system than a complex broken one. Build incrementally!
