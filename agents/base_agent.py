# agents/base_agent.py

"""
Base Agent class — shared logic for all sub-agents.
Handles Gemini API interaction and tool-calling loop.
"""

import google.genai as genai
from google.genai.types import (
    GenerateContentConfig,
    Tool,
    FunctionDeclaration,
    Schema,
    Type,
)

from tools.mcp_tools import execute_tool
from config.settings import get_settings

settings = get_settings()


class BaseAgent:
    """Base class for all agents. Provides Gemini + tool-calling loop."""

    def __init__(self, system_instruction: str, tools: list[dict]):
        self.client = genai.Client(
            vertexai=True,
            project=settings.PROJECT_ID,
            location=settings.VERTEX_AI_LOCATION,
        )
        self.model_name = settings.MODEL_NAME
        self.system_instruction = system_instruction
        self.tool_definitions = tools
        self.conversation_history = []

    def _build_gemini_tools(self) -> list[Tool]:
        """Convert MCP tool definitions to Gemini Tool objects."""
        function_declarations = []

        type_mapping = {
            "STRING": Type.STRING,
            "INTEGER": Type.INTEGER,
            "NUMBER": Type.NUMBER,
            "BOOLEAN": Type.BOOLEAN,
            "ARRAY": Type.ARRAY,
            "OBJECT": Type.OBJECT,
        }

        for tool_def in self.tool_definitions:
            properties = {}
            required = tool_def["parameters"].get("required", [])

            for prop_name, prop_schema in tool_def["parameters"]["properties"].items():
                prop_type = prop_schema.get("type", "string").upper()
                schema_type = type_mapping.get(prop_type, Type.STRING)

                schema_kwargs = {
                    "type": schema_type,
                    "description": prop_schema.get("description", ""),
                }

                if "enum" in prop_schema:
                    schema_kwargs["enum"] = prop_schema["enum"]

                if schema_type == Type.ARRAY and "items" in prop_schema:
                    items_type = prop_schema["items"].get("type", "string").upper()
                    schema_kwargs["items"] = Schema(
                        type=type_mapping.get(items_type, Type.STRING)
                    )

                properties[prop_name] = Schema(**schema_kwargs)

            fd = FunctionDeclaration(
                name=tool_def["name"],
                description=tool_def["description"],
                parameters=Schema(
                    type=Type.OBJECT,
                    properties=properties,
                    required=required,
                ),
            )
            function_declarations.append(fd)

        return [Tool(function_declarations=function_declarations)]

    def _get_required_params(self, tool_name: str) -> list:
        """Get required parameters for a tool."""
        for t in self.tool_definitions:
            if t["name"] == tool_name:
                return t["parameters"].get("required", [])
        return []

    async def process(self, user_message: str, user_id: str) -> str:
        """
        Process a user message through the Gemini tool-calling loop.
        Keeps calling tools until the model returns a text response.
        """
        augmented_message = f"[User ID: {user_id}]\nUser request: {user_message}"

        self.conversation_history.append({
            "role": "user",
            "parts": [{"text": augmented_message}],
        })

        gemini_tools = self._build_gemini_tools()

        config = GenerateContentConfig(
            system_instruction=self.system_instruction,
            tools=gemini_tools,
            temperature=0.2,
            max_output_tokens=2048,
        )

        max_iterations = 10

        for iteration in range(max_iterations):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=self.conversation_history,
                    config=config,
                )
            except Exception as e:
                return f"Error communicating with AI model: {str(e)}"

            candidate = response.candidates[0]
            has_function_call = False

            for part in candidate.content.parts:
                if hasattr(part, "function_call") and part.function_call:
                    has_function_call = True
                    fc = part.function_call
                    tool_name = fc.name
                    tool_args = dict(fc.args) if fc.args else {}

                    # Auto-inject user_id if required
                    if "user_id" in self._get_required_params(tool_name):
                        tool_args.setdefault("user_id", user_id)

                    # Execute the tool
                    result = await execute_tool(tool_name, tool_args)

                    # Add function call to history
                    self.conversation_history.append({
                        "role": "model",
                        "parts": [{"function_call": {"name": tool_name, "args": tool_args}}],
                    })

                    # Add function response to history
                    self.conversation_history.append({
                        "role": "user",
                        "parts": [{
                            "function_response": {
                                "name": tool_name,
                                "response": result,
                            }
                        }],
                    })
                    break  # Process one function call per iteration

            if not has_function_call:
                # Model returned text — we're done
                final_text = ""
                for part in candidate.content.parts:
                    if hasattr(part, "text") and part.text:
                        final_text += part.text

                self.conversation_history.append({
                    "role": "model",
                    "parts": [{"text": final_text}],
                })
                return final_text

        return "Reached maximum processing steps. Please try a simpler request."

    def reset(self):
        """Clear conversation history."""
        self.conversation_history = []