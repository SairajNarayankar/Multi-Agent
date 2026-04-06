# api/main.py

"""
FastAPI Application — Main entry point for MAPA (Multi-Agent Productivity Assistant).
"""

from contextlib import asynccontextmanager
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

from fastapi import FastAPI, HTTPException, Query, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from agents.orchestrator import OrchestratorAgent
from db import firestore_client as db
from config.settings import get_settings

settings = get_settings()

# ================================================================
#  PYDANTIC SCHEMAS
# ================================================================

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    user_id: str = Field(default="default_user", max_length=255)
    reset_conversation: bool = Field(default=False)


class ChatResponse(BaseModel):
    response: str
    user_id: str
    timestamp: str
    conversation_reset: bool = False


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    priority: Optional[str] = "medium"
    due_date: Optional[str] = None
    tags: Optional[List[str]] = []
    user_id: str = "default_user"


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None
    tags: Optional[List[str]] = None


class EventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    event_date: str
    start_time: str
    end_time: str
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[str]] = []
    user_id: str = "default_user"


class EventUpdate(BaseModel):
    title: Optional[str] = None
    event_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None


class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    tags: Optional[List[str]] = []
    is_pinned: Optional[bool] = False
    user_id: str = "default_user"


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    is_pinned: Optional[bool] = None


class WorkflowStep(BaseModel):
    agent: str
    message: str


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    steps: List[WorkflowStep]
    user_id: str = "default_user"


# ================================================================
#  APP LIFESPAN
# ================================================================

_orchestrator: Optional[OrchestratorAgent] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown."""
    global _orchestrator
    print(f"[STARTUP] MAPA starting — project={settings.PROJECT_ID}, model={settings.MODEL_NAME}")
    _orchestrator = OrchestratorAgent()
    print("[STARTUP] Orchestrator agent initialized")
    print(f"[STARTUP] Firestore project={settings.FIRESTORE_PROJECT_ID}")
    print("[STARTUP] Ready to serve requests")
    yield
    print("[SHUTDOWN] MAPA shutting down")


# ================================================================
#  FASTAPI APP
# ================================================================

app = FastAPI(
    title="MAPA — Multi-Agent Productivity Assistant",
    description="AI-powered productivity assistant with calendar, task, and notes management.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================================================================
#  AUTH
# ================================================================

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify API key if configured."""
    if settings.API_KEY and settings.API_KEY.strip():
        if x_api_key != settings.API_KEY:
            raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return True


# ================================================================
#  MIDDLEWARE
# ================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = datetime.utcnow()
    response = await call_next(request)
    duration = (datetime.utcnow() - start).total_seconds()
    print(f"[HTTP] {request.method} {request.url.path} -> {response.status_code} ({duration:.3f}s)")
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"[ERROR] {request.method} {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.ENVIRONMENT != "production" else None,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


# ================================================================
#  HEALTH ENDPOINTS
# ================================================================

@app.get("/")
async def root():
    return {
        "name": "MAPA — Multi-Agent Productivity Assistant",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "model": settings.MODEL_NAME,
        "project": settings.PROJECT_ID,
        "environment": settings.ENVIRONMENT,
    }


# ================================================================
#  CHAT ENDPOINTS
# ================================================================

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, _auth=Depends(verify_api_key)):
    """Send a natural language message to the AI orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OrchestratorAgent()

    if request.reset_conversation:
        _orchestrator.reset_conversation()

    try:
        response_text = await _orchestrator.chat(
            user_message=request.message,
            user_id=request.user_id,
        )
        return ChatResponse(
            response=response_text,
            user_id=request.user_id,
            timestamp=datetime.utcnow().isoformat(),
            conversation_reset=request.reset_conversation,
        )
    except Exception as e:
        print(f"[ERROR] Chat failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/reset")
async def reset_chat(user_id: str = "default_user", _auth=Depends(verify_api_key)):
    """Reset conversation history."""
    global _orchestrator
    if _orchestrator:
        _orchestrator.reset_conversation()
    return {"message": "Conversation reset successfully.", "user_id": user_id, "timestamp": datetime.utcnow().isoformat()}


# ================================================================
#  TASK ENDPOINTS
# ================================================================

@app.post("/tasks", status_code=201)
async def create_task(task: TaskCreate, _auth=Depends(verify_api_key)):
    try:
        result = await db.create_task(
            user_id=task.user_id,
            title=task.title,
            description=task.description,
            priority=task.priority or "medium",
            due_date=task.due_date,
            tags=task.tags or [],
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks")
async def list_tasks(
    user_id: str = Query(default="default_user"),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    due_before: Optional[str] = Query(None),
    due_after: Optional[str] = Query(None),
    limit: int = Query(default=50, le=100),
    _auth=Depends(verify_api_key),
):
    try:
        tasks = await db.list_tasks(
            user_id=user_id,
            status=status,
            priority=priority,
            due_before=due_before,
            due_after=due_after,
            limit=limit,
        )
        return {"count": len(tasks), "tasks": tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/{task_id}")
async def get_task(task_id: str, _auth=Depends(verify_api_key)):
    task = await db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.patch("/tasks/{task_id}")
async def update_task(task_id: str, task_update: TaskUpdate, _auth=Depends(verify_api_key)):
    update_data = task_update.model_dump(exclude_unset=True)
    task = await db.update_task(task_id, **update_data)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str, _auth=Depends(verify_api_key)):
    deleted = await db.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted", "task_id": task_id}


@app.get("/tasks/summary/{user_id}")
async def task_summary(user_id: str, _auth=Depends(verify_api_key)):
    try:
        summary = await db.get_task_summary(user_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================================================================
#  EVENT ENDPOINTS
# ================================================================

@app.post("/events", status_code=201)
async def create_event(event: EventCreate, _auth=Depends(verify_api_key)):
    try:
        result = await db.create_event(
            user_id=event.user_id,
            title=event.title,
            event_date=event.event_date,
            start_time=event.start_time,
            end_time=event.end_time,
            description=event.description,
            location=event.location,
            attendees=event.attendees or [],
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events")
async def list_events(
    user_id: str = Query(default="default_user"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(default=50, le=100),
    _auth=Depends(verify_api_key),
):
    try:
        events = await db.list_events(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            status=status,
            limit=limit,
        )
        return {"count": len(events), "events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events/{event_id}")
async def get_event(event_id: str, _auth=Depends(verify_api_key)):
    event = await db.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@app.patch("/events/{event_id}")
async def update_event(event_id: str, event_update: EventUpdate, _auth=Depends(verify_api_key)):
    update_data = event_update.model_dump(exclude_unset=True)
    event = await db.update_event(event_id, **update_data)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@app.delete("/events/{event_id}")
async def delete_event(event_id: str, _auth=Depends(verify_api_key)):
    deleted = await db.delete_event(event_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"message": "Event deleted", "event_id": event_id}


@app.get("/events/availability/check")
async def check_availability(
    user_id: str = Query(...),
    check_date: str = Query(...),
    start_time: str = Query(...),
    end_time: str = Query(...),
    _auth=Depends(verify_api_key),
):
    try:
        result = await db.check_availability(user_id, check_date, start_time, end_time)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================================================================
#  NOTES ENDPOINTS
# ================================================================

@app.post("/notes", status_code=201)
async def create_note(note: NoteCreate, _auth=Depends(verify_api_key)):
    try:
        result = await db.create_note(
            user_id=note.user_id,
            title=note.title,
            content=note.content,
            tags=note.tags or [],
            is_pinned=note.is_pinned or False,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/notes")
async def list_notes(
    user_id: str = Query(default="default_user"),
    search: Optional[str] = Query(None),
    is_pinned: Optional[bool] = Query(None),
    limit: int = Query(default=50, le=100),
    _auth=Depends(verify_api_key),
):
    try:
        notes = await db.list_notes(
            user_id=user_id,
            search=search,
            is_pinned=is_pinned,
            limit=limit,
        )
        return {"count": len(notes), "notes": notes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/notes/{note_id}")
async def get_note(note_id: str, _auth=Depends(verify_api_key)):
    note = await db.get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@app.patch("/notes/{note_id}")
async def update_note(note_id: str, note_update: NoteUpdate, _auth=Depends(verify_api_key)):
    update_data = note_update.model_dump(exclude_unset=True)
    note = await db.update_note(note_id, **update_data)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@app.delete("/notes/{note_id}")
async def delete_note(note_id: str, _auth=Depends(verify_api_key)):
    deleted = await db.delete_note(note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"message": "Note deleted", "note_id": note_id}


# ================================================================
#  WORKFLOW ENDPOINTS
# ================================================================

@app.post("/workflows", status_code=201)
async def create_workflow(workflow: WorkflowCreate, _auth=Depends(verify_api_key)):
    """Create and execute a multi-step workflow."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OrchestratorAgent()

    try:
        steps_list = [{"agent": s.agent, "message": s.message} for s in workflow.steps]
        result = await _orchestrator._execute_routing(
            "execute_workflow",
            {
                "user_id": workflow.user_id,
                "workflow_name": workflow.name,
                "steps": steps_list,
            },
        )
        workflow_id = result.get("workflow_id")
        wf = await db.get_workflow(workflow_id)
        return wf if wf else result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflows")
async def list_workflows(
    user_id: str = Query(default="default_user"),
    status: Optional[str] = Query(None),
    limit: int = Query(default=20, le=50),
    _auth=Depends(verify_api_key),
):
    try:
        workflows = await db.list_workflows(user_id=user_id, status=status, limit=limit)
        return {"count": len(workflows), "workflows": workflows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str, _auth=Depends(verify_api_key)):
    wf = await db.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf


# ================================================================
#  RUN
# ================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)