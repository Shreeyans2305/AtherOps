# AtherOps

<p align="center">
  <strong>🛡️ AI-Powered Self-Healing Operations Platform</strong>
</p>

<p align="center">
  A multi-agent system that automatically detects, diagnoses, and remediates production incidents in real-time using LangGraph and local LLMs.
</p>

---

## 🌟 Overview

AtherOps is an intelligent incident management platform that leverages a multi-agent AI architecture to provide autonomous self-healing capabilities for e-commerce and SaaS platforms. It continuously monitors your systems, detects anomalies, diagnoses root causes, and takes corrective actions—all with minimal human intervention.

### Key Features

- **🤖 Multi-Agent Architecture**: Four specialized AI agents work together (Observer → Reasoner → Decision → Executor)
- **🧠 Local LLM Integration**: Powered by Ollama (Llama 3.1:8b) for privacy-first, on-premise AI processing
- **📊 Real-Time Dashboard**: Live monitoring with WebSocket-powered updates
- **🔐 Multi-Tenant Support**: Organization-based isolation with Clerk authentication
- **📧 Automated Communications**: Smart email notifications to merchants and engineering teams
- **🎫 Ticket Integration**: Support ticket processing with extensible provider architecture (Jira, Zendesk, etc.)
- **💾 Dual Memory System**: Working memory for active incidents + Long-term memory for pattern learning

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              AtherOps                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌────────┐ │
│  │   Observer   │───▶│   Reasoner   │───▶│   Decision   │───▶│Executor│ │
│  │   Agent      │    │   Agent      │    │   Agent      │    │ Agent  │ │
│  │              │    │              │    │              │    │        │ │
│  │ Detects      │    │ Diagnoses    │    │ Plans        │    │Executes│ │
│  │ Patterns     │    │ Root Cause   │    │ Actions      │    │Remedi- │ │
│  │              │    │              │    │              │    │ation   │ │
│  └──────────────┘    └──────────────┘    └──────────────┘    └────────┘ │
│         ▲                   │                   │                  │    │
│         │                   ▼                   ▼                  ▼    │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      Memory System                                │  │
│  │  ┌─────────────────┐           ┌─────────────────┐               │  │
│  │  │  Working Memory │           │  Long-Term      │               │  │
│  │  │  (Active State) │           │  Memory         │               │  │
│  │  │  - Events       │           │  (Historical)   │               │  │
│  │  │  - Observations │           │  - Past         │               │  │
│  │  │  - Hypotheses   │           │    Incidents    │               │  │
│  │  │  - Action Plans │           │  - Resolutions  │               │  │
│  │  └─────────────────┘           └─────────────────┘               │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Agent Pipeline

| Agent | Role | Technology |
|-------|------|------------|
| **Observer** | Detects patterns and anomalies in event streams | Hybrid: Rule-based + LLM validation |
| **Reasoner** | Analyzes observations and diagnoses root causes | LLM-powered (Llama 3.1:8b) |
| **Decision** | Creates action plans based on hypotheses | Hybrid: Rule-based + LLM for complex cases |
| **Executor** | Executes approved remediation actions | Integration layer (Email, Slack, Jira) |

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.12+)
- **AI/ML**: LangGraph, LangChain, Ollama
- **LLM**: Llama 3.1:8b (local inference)
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Real-time**: WebSockets
- **Authentication**: Clerk JWT verification

### Frontend
- **Framework**: React 19 with Vite
- **UI Components**: Lucide React icons, Recharts
- **Auth**: Clerk React SDK
- **Routing**: React Router v7
- **Styling**: CSS Modules with animations

---

## 📦 Project Structure

```
AtherOps/
├── Backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── app.py                  # Alternative simplified app
│   ├── agent_langgraph.py      # LangGraph-based healing agent
│   ├── auth.py                 # Clerk JWT authentication
│   ├── database.py             # SQLAlchemy configuration
│   ├── db_models.py            # Database ORM models
│   │
│   ├── agents/                 # Multi-agent system
│   │   ├── orchestrator.py     # Coordinates agent pipeline
│   │   ├── observer.py         # Pattern detection agent
│   │   ├── observer_hybrid.py  # Hybrid rule+LLM observer
│   │   ├── reasoner.py         # Root cause analysis agent
│   │   ├── decision.py         # Action planning agent
│   │   ├── executor.py         # Action execution agent
│   │   └── prompts/            # LLM system prompts
│   │
│   ├── ingestion/              # Event ingestion layer
│   │   ├── receivers.py        # WebSocket/API receivers
│   │   └── normalizer.py       # Event schema normalization
│   │
│   ├── memory/                 # Memory subsystem
│   │   ├── working_memory.py   # Active incident state
│   │   └── long_memory.py      # Historical pattern storage
│   │
│   ├── models/                 # Data models
│   │   └── schemas.py          # Pydantic schemas
│   │
│   └── services/               # External integrations
│       ├── email_service.py    # SMTP email service
│       └── ticket_service.py   # Ticket system abstraction
│
└── Frontend/
    ├── src/
    │   ├── App.jsx             # Main app with routing
    │   ├── Dashboard.jsx       # Primary dashboard view
    │   │
    │   ├── components/         # UI components
    │   │   ├── AgentPipelineView.jsx  # Agent status visualization
    │   │   ├── EventTimeline.jsx      # Event feed
    │   │   ├── IncidentTable.jsx      # Incident list
    │   │   ├── MetricCard.jsx         # KPI cards
    │   │   ├── ObservationCard.jsx    # Pattern cards
    │   │   ├── ActionPlanCard.jsx     # Action plan display
    │   │   └── ...
    │   │
    │   ├── services/           # API layer
    │   │   ├── api.js          # REST API client
    │   │   └── websocket.js    # WebSocket client
    │   │
    │   ├── pages/              # Auth pages
    │   │   ├── SignInPage.jsx
    │   │   └── SignUpPage.jsx
    │   │
    │   └── hooks/              # Custom React hooks
    │       └── useChartData.js
    │
    └── package.json
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.12+**
- **Node.js 18+**
- **Ollama** with Llama 3.1 model
- **Clerk account** (for authentication)

### 1. Install Ollama and Download Model

```bash
# Install Ollama (macOS)
brew install ollama

# Start Ollama service
ollama serve

# Pull the Llama 3.1 model (in a new terminal)
ollama pull llama3.1:8b
```

### 2. Backend Setup

```bash
cd Backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your configuration
```

#### Environment Variables (.env)

```env
# Clerk Authentication
CLERK_PUBLISHABLE_KEY=pk_test_xxx
CLERK_SECRET_KEY=sk_test_xxx

# Database (optional - defaults to SQLite)
DATABASE_URL=sqlite:///./atherops.db
# For Supabase: postgresql://user:password@db.supabase.co:5432/postgres

# Email Service (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true

# Engineer Notifications (optional)
ENGINEER_EMAILS=engineer1@company.com,engineer2@company.com
```

### 3. Frontend Setup

```bash
cd Frontend

# Install dependencies
npm install

# Configure environment
# Create .env file with:
echo "VITE_CLERK_PUBLISHABLE_KEY=pk_test_xxx" > .env
```

### 4. Run the Application

```bash
# Terminal 1: Start Backend
cd Backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Frontend
cd Frontend
npm run dev
```

Access the application at `http://localhost:5173`

---

## 📡 API Endpoints

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | System status and health check |
| `GET` | `/stats` | Dashboard statistics |
| `GET` | `/api/recent-events` | Recent events with pagination |
| `POST` | `/api/tickets` | Create support ticket |
| `GET` | `/api/tickets` | List all tickets |
| `PATCH` | `/api/tickets/{id}/status` | Update ticket status |

### WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `/ws/sdk` | SDK telemetry ingestion |
| `/ws/dashboard` | Real-time dashboard updates |

### WebSocket Event Types

```javascript
// Incoming events to dashboard
{
  "type": "new_event",          // New event received
  "type": "agent_step",         // Agent pipeline progress
  "type": "observation_created", // Pattern detected
  "type": "hypothesis_generated",// Root cause identified
  "type": "action_planned",     // Remediation planned
  "type": "action_executed",    // Action completed
  "type": "email_sent"          // Notification sent
}
```

---

## 🔄 Agent Pipeline Workflow

1. **Event Ingestion**
   - SDK sends telemetry via WebSocket
   - Events normalized to unified schema
   - Stored in working memory

2. **Observer Agent** (Every 30s)
   - Analyzes recent events
   - Detects patterns using hybrid approach
   - Creates observations for significant patterns

3. **Reasoner Agent**
   - Receives observations
   - Queries historical incidents
   - Generates hypothesis with root cause

4. **Decision Agent**
   - Evaluates hypothesis
   - Applies rule-based logic for common cases
   - Uses LLM for complex decisions
   - Creates action plan with risk assessment

5. **Executor Agent**
   - Auto-executes low-risk actions
   - Awaits approval for high-risk actions
   - Sends notifications (email, Slack)
   - Creates tickets (Jira, Zendesk)

---

## 📊 Data Models

### UnifiedEvent
```python
{
  "event_id": "uuid",
  "merchant_id": "string",
  "timestamp": "datetime",
  "event_type": "api_error | checkout_failure | webhook_failure | ...",
  "severity": "critical | high | medium | low",
  "message": "string",
  "metadata": {},
  "source": "sdk | webhook | log | api"
}
```

### Observation
```python
{
  "observation_id": "uuid",
  "pattern_key": "string",
  "description": "string",
  "affected_merchants": ["merchant_ids"],
  "event_count": 5,
  "severity": "high",
  "confidence": 0.85
}
```

### ActionPlan
```python
{
  "plan_id": "uuid",
  "action_type": "merchant_communication | engineering_escalation | ...",
  "priority": "critical | high | medium | low",
  "risk_level": "low | medium | high",
  "requires_approval": false,
  "action_details": {}
}
```

---

## 🔐 Security

- **Authentication**: Clerk-based JWT verification
- **Multi-tenancy**: Organization-level data isolation
- **Local LLM**: No data sent to external AI providers
- **CORS**: Configurable origin restrictions
- **Environment Variables**: Sensitive data in .env files

---

## 🧪 Development

### Running Tests

```bash
# Backend tests
cd Backend
python -m pytest

# Test email service
python test_merchant_email.py

# Test ticket creation
python test_ticket.py
```

### Code Structure Guidelines

- **Agents**: Each agent is self-contained with clear input/output contracts
- **Prompts**: LLM prompts are externalized in `agents/prompts/`
- **Services**: External integrations are abstracted behind service classes
- **Schemas**: All data models use Pydantic for validation

---

## 🗺️ Roadmap

- [ ] RAG integration for documentation search
- [ ] Slack bot integration
- [ ] Jira/Zendesk ticket providers
- [ ] Custom runbook execution
- [ ] ML-based anomaly detection
- [ ] Kubernetes operator for deployment
- [ ] Prometheus/Grafana integration

---

## 📄 License

This project is proprietary software. All rights reserved.

---

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

---

<p align="center">
  Built with ❤️ for reliable operations
</p>
