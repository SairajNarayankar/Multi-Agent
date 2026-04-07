# 🤖 MAPA — Multi-Agent Productivity Assistant

A multi-agent AI system built on **Google Cloud** that helps users manage tasks, schedules, and information through natural language conversation.

**Powered by Google Gemini 2.5 pro via Vertex AI**
## Architecture


User → Frontend (Cloud Run) → FastAPI Backend (Cloud Run) → Orchestrator Agent
↓
┌──────────────┼──────────────┐
↓ ↓ ↓
Calendar Agent Task Agent Notes Agent
↓ ↓ ↓
Calendar Tools Task Tools Notes Tools
↓ ↓ ↓
└──────── Firestore ──────────┘


## Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Google Gemini 2.5 pro (Vertex AI) |
| Backend | FastAPI (Python 3.11) |
| Database | Google Cloud Firestore |
| Frontend | HTML/CSS/JS served via Nginx |
| Deployment | Google Cloud Run |
| CI/CD | Google Cloud Build |
| Tool Protocol | MCP (Model Context Protocol) |

## Features

- 🗓️ **Calendar Management** — Create, list, update, delete events & check availability
- ✅ **Task Management** — Full CRUD with priorities, statuses, due dates, tags
- 📝 **Notes Management** — Create, search, pin, organize notes
- 🤖 **Multi-Agent Orchestration** — Automatic routing to the right sub-agent
- 🔄 **Multi-Step Workflows** — Sequential operations across multiple agents
- 📋 **Daily Briefings** — Summary of events, tasks, and pinned notes
- 🔗 **REST API** — Direct CRUD endpoints alongside AI chat

## Project Structure

mapa/
├── agents/
│ ├── base_agent.py # Base agent with Gemini tool-calling loop
│ ├── orchestrator.py # Primary orchestrator — routes to sub-agents
│ └── sub_agents.py # Calendar, Task, Notes sub-agents
├── api/
│ └── main.py # FastAPI app with all endpoints
├── config/
│ └── settings.py # Configuration management
├── db/
│ └── firestore_client.py # Firestore CRUD operations
├── frontend/
│ ├── Dockerfile # Nginx container for frontend
│ ├── index.html # Chat UI
│ └── nginx.conf # Nginx configuration
├── tools/
│ └── mcp_tools.py # MCP tool definitions & execution engine
├── tests/
│ └── test_api.py # API tests
├── .env.example # Environment template
├── .gitignore # Git ignore rules
├── Dockerfile # Backend container
├── requirements.txt # Python dependencies
└── README.md # This file

## Quick Start

### Prerequisites
- Google Cloud account with billing enabled
- `gcloud` CLI installed
- Python 3.11+

### Deploy

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/mapa-assistant.git
cd mapa-assistant

# Set up GCP
gcloud config set project YOUR_PROJECT_ID
gcloud services enable aiplatform.googleapis.com firestore.googleapis.com run.googleapis.com cloudbuild.googleapis.com

# Create Firestore
gcloud firestore databases create --location=us-central1

# Deploy backend
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/mapa-api:latest
gcloud run deploy mapa-api --image=gcr.io/YOUR_PROJECT_ID/mapa-api:latest --region=us-central1 --allow-unauthenticated

# Deploy frontend
cd frontend
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/mapa-frontend:latest
gcloud run deploy mapa-frontend --image=gcr.io/YOUR_PROJECT_ID/mapa-frontend:latest --region=us-central1 --allow-unauthenticated

API Endpoints
Method	Endpoint	Description
POST	/chat	AI chat — natural language
POST	/chat/reset	Reset conversation
GET	/health	Health check
POST/GET/PATCH/DELETE	/tasks	Task CRUD
POST/GET/PATCH/DELETE	/events	Event CRUD
POST/GET/PATCH/DELETE	/notes	Note CRUD
POST/GET	/workflows	Workflow execution
