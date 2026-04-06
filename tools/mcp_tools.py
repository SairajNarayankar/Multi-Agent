# tools/mcp_tools.py

"""
MCP Tool Definitions and Execution Engine.
All tools for calendar, tasks, and notes — called by sub-agents.
"""

from db import firestore_client as db


# ================================================================
#  TOOL DEFINITIONS
# ================================================================

CALENDAR_TOOLS = [
    {
        "name": "create_event",
        "description": "Create a new calendar event with title, date, start/end times, and optional location/attendees.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User ID"},
                "title": {"type": "string", "description": "Event title"},
                "event_date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                "start_time": {"type": "string", "description": "Start time in HH:MM format"},
                "end_time": {"type": "string", "description": "End time in HH:MM format"},
                "description": {"type": "string", "description": "Event description"},
                "location": {"type": "string", "description": "Event location"},
                "attendees": {"type": "array", "items": {"type": "string"}, "description": "List of attendees"},
            },
            "required": ["user_id", "title", "event_date", "start_time", "end_time"],
        },
    },
    {
        "name": "list_events",
        "description": "List calendar events for a user, optionally filtered by date range.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User ID"},
                "date_from": {"type": "string", "description": "Start date YYYY-MM-DD"},
                "date_to": {"type": "string", "description": "End date YYYY-MM-DD"},
                "status": {"type": "string", "enum": ["scheduled", "cancelled", "completed"]},
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "get_event",
        "description": "Get details of a specific event by ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "Event ID"},
            },
            "required": ["event_id"],
        },
    },
    {
        "name": "update_event",
        "description": "Update an existing calendar event.",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "Event ID"},
                "title": {"type": "string"},
                "event_date": {"type": "string"},
                "start_time": {"type": "string"},
                "end_time": {"type": "string"},
                "description": {"type": "string"},
                "location": {"type": "string"},
                "status": {"type": "string", "enum": ["scheduled", "cancelled", "completed"]},
            },
            "required": ["event_id"],
        },
    },
    {
        "name": "delete_event",
        "description": "Delete a calendar event.",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "Event ID"},
            },
            "required": ["event_id"],
        },
    },
    {
        "name": "check_availability",
        "description": "Check if a time slot is available on a given date.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "check_date": {"type": "string", "description": "Date YYYY-MM-DD"},
                "start_time": {"type": "string", "description": "Start HH:MM"},
                "end_time": {"type": "string", "description": "End HH:MM"},
            },
            "required": ["user_id", "check_date", "start_time", "end_time"],
        },
    },
]

TASK_TOOLS = [
    {
        "name": "create_task",
        "description": "Create a new task with title, description, priority, due date, and tags.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User ID"},
                "title": {"type": "string", "description": "Task title"},
                "description": {"type": "string", "description": "Task description"},
                "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
                "due_date": {"type": "string", "description": "Due date YYYY-MM-DD"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["user_id", "title"],
        },
    },
    {
        "name": "list_tasks",
        "description": "List tasks for a user with optional filters.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "status": {"type": "string", "enum": ["todo", "in_progress", "done", "cancelled"]},
                "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
                "due_before": {"type": "string"},
                "due_after": {"type": "string"},
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "get_task",
        "description": "Get a specific task by ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "update_task",
        "description": "Update a task's title, description, status, priority, due date, or tags.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "status": {"type": "string", "enum": ["todo", "in_progress", "done", "cancelled"]},
                "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
                "due_date": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "delete_task",
        "description": "Delete a task permanently.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "get_task_summary",
        "description": "Get summary of all tasks grouped by status with counts.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
            },
            "required": ["user_id"],
        },
    },
]

NOTES_TOOLS = [
    {
        "name": "create_note",
        "description": "Create a new note with title, content, tags, and pin status.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "title": {"type": "string", "description": "Note title"},
                "content": {"type": "string", "description": "Note content"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "is_pinned": {"type": "boolean"},
            },
            "required": ["user_id", "title", "content"],
        },
    },
    {
        "name": "list_notes",
        "description": "List notes for a user with optional search and pin filter.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "search": {"type": "string", "description": "Search keyword"},
                "is_pinned": {"type": "boolean"},
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "get_note",
        "description": "Get full content of a specific note.",
        "parameters": {
            "type": "object",
            "properties": {
                "note_id": {"type": "string"},
            },
            "required": ["note_id"],
        },
    },
    {
        "name": "update_note",
        "description": "Update a note's title, content, tags, or pin status.",
        "parameters": {
            "type": "object",
            "properties": {
                "note_id": {"type": "string"},
                "title": {"type": "string"},
                "content": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "is_pinned": {"type": "boolean"},
            },
            "required": ["note_id"],
        },
    },
    {
        "name": "delete_note",
        "description": "Delete a note permanently.",
        "parameters": {
            "type": "object",
            "properties": {
                "note_id": {"type": "string"},
            },
            "required": ["note_id"],
        },
    },
    {
        "name": "search_notes",
        "description": "Search through notes by keyword in title and content.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "query": {"type": "string", "description": "Search keyword"},
            },
            "required": ["user_id", "query"],
        },
    },
]


# ================================================================
#  TOOL EXECUTION ENGINE
# ================================================================

async def execute_tool(tool_name: str, arguments: dict) -> dict:
    """
    Universal tool executor — routes to the correct Firestore operation.
    Called by all sub-agents.
    """
    try:
        # ---- CALENDAR TOOLS ----
        if tool_name == "create_event":
            event = await db.create_event(
                user_id=arguments["user_id"],
                title=arguments["title"],
                event_date=arguments["event_date"],
                start_time=arguments["start_time"],
                end_time=arguments["end_time"],
                description=arguments.get("description"),
                location=arguments.get("location"),
                attendees=arguments.get("attendees", []),
            )
            return {"success": True, "message": f"Event '{event['title']}' created.", "event": event}

        elif tool_name == "list_events":
            events = await db.list_events(
                user_id=arguments["user_id"],
                date_from=arguments.get("date_from"),
                date_to=arguments.get("date_to"),
                status=arguments.get("status"),
            )
            return {"success": True, "count": len(events), "events": events}

        elif tool_name == "get_event":
            event = await db.get_event(event_id=arguments["event_id"])
            if event:
                return {"success": True, "event": event}
            return {"success": False, "message": "Event not found."}

        elif tool_name == "update_event":
            event_id = arguments.pop("event_id")
            event = await db.update_event(event_id=event_id, **arguments)
            if event:
                return {"success": True, "message": "Event updated.", "event": event}
            return {"success": False, "message": "Event not found."}

        elif tool_name == "delete_event":
            deleted = await db.delete_event(event_id=arguments["event_id"])
            return {"success": deleted, "message": "Event deleted." if deleted else "Event not found."}

        elif tool_name == "check_availability":
            result = await db.check_availability(
                user_id=arguments["user_id"],
                check_date=arguments["check_date"],
                start_time=arguments["start_time"],
                end_time=arguments["end_time"],
            )
            return {"success": True, **result}

        # ---- TASK TOOLS ----
        elif tool_name == "create_task":
            task = await db.create_task(
                user_id=arguments["user_id"],
                title=arguments["title"],
                description=arguments.get("description"),
                priority=arguments.get("priority", "medium"),
                due_date=arguments.get("due_date"),
                tags=arguments.get("tags", []),
            )
            return {"success": True, "message": f"Task '{task['title']}' created.", "task": task}

        elif tool_name == "list_tasks":
            tasks = await db.list_tasks(
                user_id=arguments["user_id"],
                status=arguments.get("status"),
                priority=arguments.get("priority"),
                due_before=arguments.get("due_before"),
                due_after=arguments.get("due_after"),
            )
            return {"success": True, "count": len(tasks), "tasks": tasks}

        elif tool_name == "get_task":
            task = await db.get_task(task_id=arguments["task_id"])
            if task:
                return {"success": True, "task": task}
            return {"success": False, "message": "Task not found."}

        elif tool_name == "update_task":
            task_id = arguments.pop("task_id")
            task = await db.update_task(task_id=task_id, **arguments)
            if task:
                return {"success": True, "message": "Task updated.", "task": task}
            return {"success": False, "message": "Task not found."}

        elif tool_name == "delete_task":
            deleted = await db.delete_task(task_id=arguments["task_id"])
            return {"success": deleted, "message": "Task deleted." if deleted else "Task not found."}

        elif tool_name == "get_task_summary":
            summary = await db.get_task_summary(user_id=arguments["user_id"])
            return {"success": True, **summary}

        # ---- NOTES TOOLS ----
        elif tool_name == "create_note":
            note = await db.create_note(
                user_id=arguments["user_id"],
                title=arguments["title"],
                content=arguments["content"],
                tags=arguments.get("tags", []),
                is_pinned=arguments.get("is_pinned", False),
            )
            return {"success": True, "message": f"Note '{note['title']}' created.", "note": note}

        elif tool_name == "list_notes":
            notes = await db.list_notes(
                user_id=arguments["user_id"],
                search=arguments.get("search"),
                is_pinned=arguments.get("is_pinned"),
            )
            return {"success": True, "count": len(notes), "notes": notes}

        elif tool_name == "get_note":
            note = await db.get_note(note_id=arguments["note_id"])
            if note:
                return {"success": True, "note": note}
            return {"success": False, "message": "Note not found."}

        elif tool_name == "update_note":
            note_id = arguments.pop("note_id")
            note = await db.update_note(note_id=note_id, **arguments)
            if note:
                return {"success": True, "message": "Note updated.", "note": note}
            return {"success": False, "message": "Note not found."}

        elif tool_name == "delete_note":
            deleted = await db.delete_note(note_id=arguments["note_id"])
            return {"success": deleted, "message": "Note deleted." if deleted else "Note not found."}

        elif tool_name == "search_notes":
            notes = await db.list_notes(
                user_id=arguments["user_id"],
                search=arguments["query"],
            )
            return {"success": True, "query": arguments["query"], "count": len(notes), "notes": notes}

        else:
            return {"success": False, "message": f"Unknown tool: {tool_name}"}

    except Exception as e:
        return {"success": False, "message": f"Tool execution error: {str(e)}"}