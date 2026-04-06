# agents/orchestrator.py

"""
Primary Orchestrator Agent — coordinates all sub-agents.
Analyzes user intent, routes to correct sub-agent(s), manages workflows.
"""

from datetime import datetime

import google.genai as genai
from google.genai.types import (
    GenerateContentConfig,
    Tool,
    FunctionDeclaration,
    Schema,
    Type,
)

from agents.sub_agents import CalendarAgent, TaskAgent, NotesAgent
from db import firestore_client as db
from config.settings import get_settings

settings = get_settings()


class OrchestratorAgent:
    """
    Primary orchestrator that:
    1. Analyzes user intent
    2. Routes to appropriate sub-agent(s)
    3. Manages multi-step workflows
    4. Combines results and responds
    """

    def __init__(self):
        self.client = genai.Client(
            vertexai=True,
            project=settings.PROJECT_ID,
            location=settings.VERTEX_AI_LOCATION,
        )
        self.model_name = settings.MODEL_NAME
        self.calendar_agent = CalendarAgent()
        self.task_agent = TaskAgent()
        self.notes_agent = NotesAgent()
        self.conversation_history = []
        self.system_instruction = """You are the primary Orchestrator for a Multi-Agent Productivity Assistant called MAPA.
Your role is to understand the user's request and route it to the correct sub-agent(s).

Available routing functions:
- route_to_calendar: For calendar events, scheduling, meetings, appointments, availability
- route_to_tasks: For tasks, to-dos, task status updates, priorities, deadlines
- route_to_notes: For notes, note-taking, searching notes, organizing information
- route_to_multiple: When a request needs multiple agents (e.g., "create a task and schedule a meeting")
- execute_workflow: For multi-step sequential operations across agents
- get_daily_briefing: Summary of today's events, pending tasks, and pinned notes

ROUTING RULES:
1. Analyze intent carefully before routing.
2. Single domain requests go to one agent.
3. Multi-domain requests use route_to_multiple or execute_workflow.
4. Pass the COMPLETE user message to sub-agents — never summarize.
5. After getting results, synthesize into a friendly response.
6. For ambiguous requests, ask for clarification.

EXAMPLES:
- "Schedule a meeting tomorrow at 2pm" -> route_to_calendar
- "Add a task to prepare the report" -> route_to_tasks  
- "Save this as a note" -> route_to_notes
- "What's on my plate today?" -> get_daily_briefing
- "Create a task and schedule time for it" -> route_to_multiple
"""

    def _get_orchestrator_tools(self) -> list[Tool]:
        """Define routing tools for the orchestrator."""
        function_declarations = [
            FunctionDeclaration(
                name="route_to_calendar",
                description="Route request to Calendar sub-agent for event/scheduling operations.",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "message": Schema(type=Type.STRING, description="Complete user message for calendar agent"),
                        "user_id": Schema(type=Type.STRING, description="User ID"),
                    },
                    required=["message", "user_id"],
                ),
            ),
            FunctionDeclaration(
                name="route_to_tasks",
                description="Route request to Task sub-agent for task management operations.",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "message": Schema(type=Type.STRING, description="Complete user message for task agent"),
                        "user_id": Schema(type=Type.STRING, description="User ID"),
                    },
                    required=["message", "user_id"],
                ),
            ),
            FunctionDeclaration(
                name="route_to_notes",
                description="Route request to Notes sub-agent for note management operations.",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "message": Schema(type=Type.STRING, description="Complete user message for notes agent"),
                        "user_id": Schema(type=Type.STRING, description="User ID"),
                    },
                    required=["message", "user_id"],
                ),
            ),
            FunctionDeclaration(
                name="route_to_multiple",
                description="Route request to multiple sub-agents when it spans multiple domains.",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "user_id": Schema(type=Type.STRING, description="User ID"),
                        "calendar_message": Schema(type=Type.STRING, description="Message for calendar agent (empty if not needed)"),
                        "task_message": Schema(type=Type.STRING, description="Message for task agent (empty if not needed)"),
                        "notes_message": Schema(type=Type.STRING, description="Message for notes agent (empty if not needed)"),
                    },
                    required=["user_id"],
                ),
            ),
            FunctionDeclaration(
                name="execute_workflow",
                description="Execute a multi-step workflow with ordered steps assigned to specific agents.",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "user_id": Schema(type=Type.STRING, description="User ID"),
                        "workflow_name": Schema(type=Type.STRING, description="Name for this workflow"),
                        "steps": Schema(
                            type=Type.ARRAY,
                            description="Ordered list of workflow steps",
                            items=Schema(
                                type=Type.OBJECT,
                                properties={
                                    "agent": Schema(type=Type.STRING, description="Agent: calendar, tasks, or notes"),
                                    "message": Schema(type=Type.STRING, description="Instruction for this step"),
                                },
                                required=["agent", "message"],
                            ),
                        ),
                    },
                    required=["user_id", "workflow_name", "steps"],
                ),
            ),
            FunctionDeclaration(
                name="get_daily_briefing",
                description="Get daily briefing: today's events, pending tasks, and pinned notes.",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "user_id": Schema(type=Type.STRING, description="User ID"),
                    },
                    required=["user_id"],
                ),
            ),
        ]
        return [Tool(function_declarations=function_declarations)]

    async def _execute_routing(self, tool_name: str, tool_args: dict) -> dict:
        """Execute a routing function call and return results."""
        user_id = tool_args.get("user_id", "default_user")

        if tool_name == "route_to_calendar":
            result = await self.calendar_agent.process(tool_args["message"], user_id)
            return {"agent": "calendar", "response": result}

        elif tool_name == "route_to_tasks":
            result = await self.task_agent.process(tool_args["message"], user_id)
            return {"agent": "tasks", "response": result}

        elif tool_name == "route_to_notes":
            result = await self.notes_agent.process(tool_args["message"], user_id)
            return {"agent": "notes", "response": result}

        elif tool_name == "route_to_multiple":
            results = {}
            calendar_msg = tool_args.get("calendar_message", "")
            task_msg = tool_args.get("task_message", "")
            notes_msg = tool_args.get("notes_message", "")

            if calendar_msg and calendar_msg.strip():
                results["calendar"] = await self.calendar_agent.process(calendar_msg, user_id)
            if task_msg and task_msg.strip():
                results["tasks"] = await self.task_agent.process(task_msg, user_id)
            if notes_msg and notes_msg.strip():
                results["notes"] = await self.notes_agent.process(notes_msg, user_id)

            return {"agent": "multiple", "responses": results}

        elif tool_name == "execute_workflow":
            workflow_name = tool_args.get("workflow_name", "Unnamed Workflow")
            steps = tool_args.get("steps", [])

            workflow = await db.create_workflow(
                user_id=user_id,
                name=workflow_name,
                description=f"Auto-created workflow with {len(steps)} steps",
                steps=[{"agent": s.get("agent", ""), "message": s.get("message", "")} for s in steps],
            )
            workflow_id = workflow["id"]

            await db.update_workflow(workflow_id, status="running")

            agent_map = {
                "calendar": self.calendar_agent,
                "tasks": self.task_agent,
                "notes": self.notes_agent,
            }

            step_results = {}
            failed = False

            for i, step in enumerate(steps):
                agent_name = step.get("agent", "")
                step_message = step.get("message", "")
                agent = agent_map.get(agent_name)

                if agent is None:
                    step_results[f"step_{i + 1}"] = {"agent": agent_name, "error": f"Unknown agent: {agent_name}"}
                    continue

                try:
                    result = await agent.process(step_message, user_id)
                    step_results[f"step_{i + 1}"] = {
                        "agent": agent_name,
                        "message": step_message,
                        "response": result,
                    }
                    await db.update_workflow(workflow_id, current_step=i + 1, results=step_results)
                except Exception as e:
                    step_results[f"step_{i + 1}"] = {"agent": agent_name, "error": str(e)}
                    await db.update_workflow(
                        workflow_id,
                        status="failed",
                        error_message=f"Step {i + 1} failed: {str(e)}",
                        results=step_results,
                    )
                    failed = True
                    break

            if not failed:
                await db.update_workflow(
                    workflow_id,
                    status="completed",
                    results=step_results,
                    completed_at=datetime.utcnow().isoformat(),
                )

            return {
                "agent": "workflow",
                "workflow_id": workflow_id,
                "workflow_name": workflow_name,
                "total_steps": len(steps),
                "step_results": step_results,
            }

        elif tool_name == "get_daily_briefing":
            today = datetime.utcnow().date().isoformat()

            calendar_result = await self.calendar_agent.process(
                f"List all my events for today ({today})", user_id
            )
            task_result = await self.task_agent.process(
                "Show me my task summary — how many tasks in each status?", user_id
            )
            notes_result = await self.notes_agent.process(
                "List my pinned notes", user_id
            )

            return {
                "agent": "briefing",
                "date": today,
                "calendar_summary": calendar_result,
                "task_summary": task_result,
                "pinned_notes": notes_result,
            }

        else:
            return {"error": f"Unknown routing function: {tool_name}"}

    async def chat(self, user_message: str, user_id: str = "default_user") -> str:
        """Main entry point — process user message through orchestration."""
        augmented_message = (
            f"[User ID: {user_id}] [Timestamp: {datetime.utcnow().isoformat()}]\n"
            f"User: {user_message}"
        )

        self.conversation_history.append({
            "role": "user",
            "parts": [{"text": augmented_message}],
        })

        orchestrator_tools = self._get_orchestrator_tools()

        config = GenerateContentConfig(
            system_instruction=self.system_instruction,
            tools=orchestrator_tools,
            temperature=0.3,
            max_output_tokens=4096,
        )

        max_iterations = 15

        for iteration in range(max_iterations):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=self.conversation_history,
                    config=config,
                )
            except Exception as e:
                error_msg = str(e)
                if "not found" in error_msg.lower() or "access" in error_msg.lower():
                    return (
                        f"Model error: The model '{self.model_name}' is not available. "
                        f"Please check your Vertex AI setup. Detail: {error_msg}"
                    )
                return f"I'm sorry, I encountered an error: {error_msg}"

            candidate = response.candidates[0]
            has_function_call = False

            for part in candidate.content.parts:
                if hasattr(part, "function_call") and part.function_call:
                    has_function_call = True
                    fc = part.function_call
                    tool_name = fc.name
                    tool_args = dict(fc.args) if fc.args else {}
                    tool_args.setdefault("user_id", user_id)

                    result = await self._execute_routing(tool_name, tool_args)

                    self.conversation_history.append({
                        "role": "model",
                        "parts": [{"function_call": {"name": tool_name, "args": tool_args}}],
                    })
                    self.conversation_history.append({
                        "role": "user",
                        "parts": [{"function_response": {"name": tool_name, "response": result}}],
                    })
                    break

            if not has_function_call:
                final_text = ""
                for part in candidate.content.parts:
                    if hasattr(part, "text") and part.text:
                        final_text += part.text

                self.conversation_history.append({
                    "role": "model",
                    "parts": [{"text": final_text}],
                })
                return final_text

        return "I've reached the maximum processing steps. Please try a simpler request."

    def reset_conversation(self):
        """Reset all agent conversation histories."""
        self.conversation_history = []
        self.calendar_agent.reset()
        self.task_agent.reset()
        self.notes_agent.reset()