# db/firestore_client.py

"""
Firestore client — handles all database operations for tasks, events, notes, and workflows.
"""

import uuid
from datetime import datetime, date, time
from typing import Optional, List, Dict, Any

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from config.settings import get_settings

settings = get_settings()

# Initialize Firestore client
_db = None


def get_db() -> firestore.AsyncClient:
    """Get or create Firestore async client."""
    global _db
    if _db is None:
        _db = firestore.AsyncClient(
            project=settings.FIRESTORE_PROJECT_ID,
            database=settings.FIRESTORE_DATABASE,
        )
    return _db


# ================================================================
#  COLLECTION NAMES
# ================================================================
TASKS_COLLECTION = "tasks"
EVENTS_COLLECTION = "events"
NOTES_COLLECTION = "notes"
WORKFLOWS_COLLECTION = "workflows"


# ================================================================
#  TASK OPERATIONS
# ================================================================

async def create_task(
    user_id: str,
    title: str,
    description: str = None,
    priority: str = "medium",
    due_date: str = None,
    tags: list = None,
) -> dict:
    """Create a new task in Firestore."""
    db = get_db()
    task_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    task_data = {
        "id": task_id,
        "user_id": user_id,
        "title": title,
        "description": description or "",
        "status": "todo",
        "priority": priority,
        "due_date": due_date,
        "tags": tags or [],
        "created_at": now,
        "updated_at": now,
    }

    await db.collection(TASKS_COLLECTION).document(task_id).set(task_data)
    return task_data


async def get_task(task_id: str) -> Optional[dict]:
    """Get a task by ID."""
    db = get_db()
    doc = await db.collection(TASKS_COLLECTION).document(task_id).get()
    if doc.exists:
        return doc.to_dict()
    return None


async def list_tasks(
    user_id: str,
    status: str = None,
    priority: str = None,
    due_before: str = None,
    due_after: str = None,
    limit: int = 50,
) -> List[dict]:
    """List tasks with optional filters."""
    db = get_db()
    query = db.collection(TASKS_COLLECTION).where(
        filter=FieldFilter("user_id", "==", user_id)
    )

    if status:
        query = query.where(filter=FieldFilter("status", "==", status))
    if priority:
        query = query.where(filter=FieldFilter("priority", "==", priority))
    if due_before:
        query = query.where(filter=FieldFilter("due_date", "<=", due_before))
    if due_after:
        query = query.where(filter=FieldFilter("due_date", ">=", due_after))

    query = query.limit(limit)
    docs = await query.get()
    return [doc.to_dict() for doc in docs]


async def update_task(task_id: str, **kwargs) -> Optional[dict]:
    """Update a task."""
    db = get_db()
    doc_ref = db.collection(TASKS_COLLECTION).document(task_id)
    doc = await doc_ref.get()

    if not doc.exists:
        return None

    update_data = {k: v for k, v in kwargs.items() if v is not None}
    update_data["updated_at"] = datetime.utcnow().isoformat()

    await doc_ref.update(update_data)

    updated_doc = await doc_ref.get()
    return updated_doc.to_dict()


async def delete_task(task_id: str) -> bool:
    """Delete a task."""
    db = get_db()
    doc_ref = db.collection(TASKS_COLLECTION).document(task_id)
    doc = await doc_ref.get()

    if not doc.exists:
        return False

    await doc_ref.delete()
    return True


async def get_task_summary(user_id: str) -> dict:
    """Get task summary grouped by status."""
    summary = {}
    for status_val in ["todo", "in_progress", "done", "cancelled"]:
        tasks = await list_tasks(user_id=user_id, status=status_val)
        summary[status_val] = {
            "count": len(tasks),
            "tasks": [
                {
                    "id": t["id"],
                    "title": t["title"],
                    "priority": t.get("priority", "medium"),
                    "due_date": t.get("due_date"),
                }
                for t in tasks
            ],
        }
    total = sum(s["count"] for s in summary.values())
    return {"total_tasks": total, "summary": summary}


# ================================================================
#  EVENT OPERATIONS
# ================================================================

async def create_event(
    user_id: str,
    title: str,
    event_date: str,
    start_time: str,
    end_time: str,
    description: str = None,
    location: str = None,
    attendees: list = None,
) -> dict:
    """Create a new calendar event."""
    db = get_db()
    event_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    event_data = {
        "id": event_id,
        "user_id": user_id,
        "title": title,
        "description": description or "",
        "event_date": event_date,
        "start_time": start_time,
        "end_time": end_time,
        "location": location or "",
        "attendees": attendees or [],
        "status": "scheduled",
        "created_at": now,
        "updated_at": now,
    }

    await db.collection(EVENTS_COLLECTION).document(event_id).set(event_data)
    return event_data


async def get_event(event_id: str) -> Optional[dict]:
    """Get an event by ID."""
    db = get_db()
    doc = await db.collection(EVENTS_COLLECTION).document(event_id).get()
    if doc.exists:
        return doc.to_dict()
    return None


async def list_events(
    user_id: str,
    date_from: str = None,
    date_to: str = None,
    status: str = None,
    limit: int = 50,
) -> List[dict]:
    """List events with optional filters."""
    db = get_db()
    query = db.collection(EVENTS_COLLECTION).where(
        filter=FieldFilter("user_id", "==", user_id)
    )

    if status:
        query = query.where(filter=FieldFilter("status", "==", status))
    if date_from:
        query = query.where(filter=FieldFilter("event_date", ">=", date_from))
    if date_to:
        query = query.where(filter=FieldFilter("event_date", "<=", date_to))

    query = query.limit(limit)
    docs = await query.get()
    return [doc.to_dict() for doc in docs]


async def update_event(event_id: str, **kwargs) -> Optional[dict]:
    """Update an event."""
    db = get_db()
    doc_ref = db.collection(EVENTS_COLLECTION).document(event_id)
    doc = await doc_ref.get()

    if not doc.exists:
        return None

    update_data = {k: v for k, v in kwargs.items() if v is not None}
    update_data["updated_at"] = datetime.utcnow().isoformat()

    await doc_ref.update(update_data)

    updated_doc = await doc_ref.get()
    return updated_doc.to_dict()


async def delete_event(event_id: str) -> bool:
    """Delete an event."""
    db = get_db()
    doc_ref = db.collection(EVENTS_COLLECTION).document(event_id)
    doc = await doc_ref.get()

    if not doc.exists:
        return False

    await doc_ref.delete()
    return True


async def check_availability(
    user_id: str,
    check_date: str,
    start_time: str,
    end_time: str,
) -> dict:
    """Check if a time slot is available."""
    events = await list_events(
        user_id=user_id,
        date_from=check_date,
        date_to=check_date,
        status="scheduled",
    )

    conflicts = []
    for ev in events:
        ev_start = ev.get("start_time", "")
        ev_end = ev.get("end_time", "")
        # Simple string comparison works for HH:MM format
        if start_time < ev_end and end_time > ev_start:
            conflicts.append(ev)

    return {
        "is_available": len(conflicts) == 0,
        "conflicts": conflicts,
        "message": (
            "Time slot is available."
            if len(conflicts) == 0
            else f"Found {len(conflicts)} conflicting event(s)."
        ),
    }


# ================================================================
#  NOTE OPERATIONS
# ================================================================

async def create_note(
    user_id: str,
    title: str,
    content: str,
    tags: list = None,
    is_pinned: bool = False,
) -> dict:
    """Create a new note."""
    db = get_db()
    note_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    note_data = {
        "id": note_id,
        "user_id": user_id,
        "title": title,
        "content": content,
        "tags": tags or [],
        "is_pinned": is_pinned,
        "created_at": now,
        "updated_at": now,
    }

    await db.collection(NOTES_COLLECTION).document(note_id).set(note_data)
    return note_data


async def get_note(note_id: str) -> Optional[dict]:
    """Get a note by ID."""
    db = get_db()
    doc = await db.collection(NOTES_COLLECTION).document(note_id).get()
    if doc.exists:
        return doc.to_dict()
    return None


async def list_notes(
    user_id: str,
    search: str = None,
    is_pinned: bool = None,
    limit: int = 50,
) -> List[dict]:
    """List notes with optional filters."""
    db = get_db()
    query = db.collection(NOTES_COLLECTION).where(
        filter=FieldFilter("user_id", "==", user_id)
    )

    if is_pinned is not None:
        query = query.where(filter=FieldFilter("is_pinned", "==", is_pinned))

    query = query.limit(limit)
    docs = await query.get()
    results = [doc.to_dict() for doc in docs]

    # Client-side text search (Firestore doesn't support full-text search natively)
    if search:
        search_lower = search.lower()
        results = [
            n for n in results
            if search_lower in n.get("title", "").lower()
            or search_lower in n.get("content", "").lower()
        ]

    return results


async def update_note(note_id: str, **kwargs) -> Optional[dict]:
    """Update a note."""
    db = get_db()
    doc_ref = db.collection(NOTES_COLLECTION).document(note_id)
    doc = await doc_ref.get()

    if not doc.exists:
        return None

    update_data = {k: v for k, v in kwargs.items() if v is not None}
    update_data["updated_at"] = datetime.utcnow().isoformat()

    await doc_ref.update(update_data)

    updated_doc = await doc_ref.get()
    return updated_doc.to_dict()


async def delete_note(note_id: str) -> bool:
    """Delete a note."""
    db = get_db()
    doc_ref = db.collection(NOTES_COLLECTION).document(note_id)
    doc = await doc_ref.get()

    if not doc.exists:
        return False

    await doc_ref.delete()
    return True


# ================================================================
#  WORKFLOW OPERATIONS
# ================================================================

async def create_workflow(
    user_id: str,
    name: str,
    description: str = None,
    steps: list = None,
) -> dict:
    """Create a workflow record."""
    db = get_db()
    workflow_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    workflow_data = {
        "id": workflow_id,
        "user_id": user_id,
        "name": name,
        "description": description or "",
        "status": "pending",
        "steps": steps or [],
        "current_step": 0,
        "results": {},
        "error_message": None,
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
    }

    await db.collection(WORKFLOWS_COLLECTION).document(workflow_id).set(workflow_data)
    return workflow_data


async def update_workflow(workflow_id: str, **kwargs) -> Optional[dict]:
    """Update a workflow."""
    db = get_db()
    doc_ref = db.collection(WORKFLOWS_COLLECTION).document(workflow_id)

    update_data = {k: v for k, v in kwargs.items() if v is not None}
    update_data["updated_at"] = datetime.utcnow().isoformat()

    await doc_ref.update(update_data)

    updated_doc = await doc_ref.get()
    return updated_doc.to_dict()


async def get_workflow(workflow_id: str) -> Optional[dict]:
    """Get a workflow by ID."""
    db = get_db()
    doc = await db.collection(WORKFLOWS_COLLECTION).document(workflow_id).get()
    if doc.exists:
        return doc.to_dict()
    return None


async def list_workflows(
    user_id: str,
    status: str = None,
    limit: int = 20,
) -> List[dict]:
    """List workflows for a user."""
    db = get_db()
    query = db.collection(WORKFLOWS_COLLECTION).where(
        filter=FieldFilter("user_id", "==", user_id)
    )
    if status:
        query = query.where(filter=FieldFilter("status", "==", status))
    query = query.limit(limit)
    docs = await query.get()
    return [doc.to_dict() for doc in docs]