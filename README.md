# 🤖 MAPA — Multi-Agent Productivity Assistant

A multi-agent AI system built on **Google Cloud** that helps users manage tasks, schedules, and information through natural language conversation.

**Powered by Google Gemini 2.5 pro via Vertex AI**
## Architecture

The architecture of the Multi-Agent System is designed to facilitate efficient communication and interaction among autonomous agents. It is composed of several key components:

1. **Agents**: Autonomous entities that perform specific tasks. Each agent operates independently and can adapt to changing environments.
2. **Environment**: The context within which agents operate. It includes all the external factors that can affect the agents' decision-making and actions.
3. **Communication Layer**: This layer ensures that agents can communicate with each other and with the environment. It includes protocols and methods for message passing and data sharing.
4. **Centralized & Decentralized Architecture**: Depending on the application, the system can be configured to use either a centralized approach (one main controller) or a decentralized approach (agents communicate without a central coordinator).

## Tech Stack

| Technology        | Description                                                                                        |
|-------------------|----------------------------------------------------------------------------------------------------|
| **Programming Language**| Python: Chosen for its simplicity and extensive libraries for AI and machine learning.       |
| **Framework**      | Flask: A lightweight framework for building web applications and APIs to interface with agents.   |
| **Database**       | PostgreSQL: A powerful relational database to manage agent data and their interactions.           |
| **Containerization**| Docker: Used for creating, deploying, and running applications in containers to ensure consistency.|
| **Message Broker** | RabbitMQ: Facilitates communication between agents, allowing for asynchronous message passing.    |
| **Testing Framework**   | PyTest: A robust framework for testing Python applications to ensure reliability and quality.|


## Features

- 🗓️ **Calendar Management** — Create, list, update, delete events & check availability
- ✅ **Task Management** — Full CRUD with priorities, statuses, due dates, tags
- 📝 **Notes Management** — Create, search, pin, organize notes
- 🤖 **Multi-Agent Orchestration** — Automatic routing to the right sub-agent
- 🔄 **Multi-Step Workflows** — Sequential operations across multiple agents
- 📋 **Daily Briefings** — Summary of events, tasks, and pinned notes
- 🔗 **REST API** — Direct CRUD endpoints alongside AI chat

## Project Structure

<img width="1440" height="1524" alt="image" src="https://github.com/user-attachments/assets/6bb16a21-e06e-4bf8-8f13-37554f40de7b" />


## Quick Start

### Prerequisites
- Google Cloud account with billing enabled
- `gcloud` CLI installed
- Python 3.11+

### Deploy

```bash
# Clone
git clone https://github.com/SairajNarayankar/mapa-assistant.git
cd mapa-assistant
```

```bash
# Set up GCP
gcloud config set project YOUR_PROJECT_ID
gcloud services enable aiplatform.googleapis.com firestore.googleapis.com run.googleapis.com cloudbuild.googleapis.com
```

```bash
# Create Firestore
gcloud firestore databases create --location=us-central1
```

```bash
# Deploy backend
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/mapa-api:latest
gcloud run deploy mapa-api --image=gcr.io/YOUR_PROJECT_ID/mapa-api:latest --region=us-central1 --allow-unauthenticated
```

```bash
# Deploy frontend
cd frontend
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/mapa-frontend:latest
gcloud run deploy mapa-frontend --image=gcr.io/YOUR_PROJECT_ID/mapa-frontend:latest --region=us-central1 --allow-unauthenticated
```

```bash
# API Endpoints
Method	Endpoint	Description
POST	/chat	AI chat — natural language
POST	/chat/reset	Reset conversation
GET	/health	Health check
POST/GET/PATCH/DELETE	/tasks	Task CRUD
POST/GET/PATCH/DELETE	/events	Event CRUD
POST/GET/PATCH/DELETE	/notes	Note CRUD
POST/GET	/workflows	Workflow execution
```
