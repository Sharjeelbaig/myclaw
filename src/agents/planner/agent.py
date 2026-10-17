from __future__ import annotations

from typing import Any, Sequence
from deepagents import SubAgent
from agents.planner.prompt import SYSTEM_PROMPT
from agents.planner.tools.create_or_update_todo import createOrUpdateTodo
from agents.planner.tools.render_todo_board import renderTodoBoard


def create_planner_subagent(
    model: Any = None,
    *,
    name: str = "planner-agent",
    description: str = "Used for planning the steps to complete user requests. It can create and manage todo boards and tasks.",
    system_prompt: str = SYSTEM_PROMPT,
    tools: Sequence[Any] | None = None,
    skills: list[str] | None = None,
    interrupt_on: dict[str, Any] | None = None,
    middleware: list[Any] | None = None,
    **kwargs: Any,
) -> SubAgent:
    """Create a configured SubAgent dictionary for the planner agent.

    Supports custom overrides and kwargs accepted by deepagents.SubAgent:
    (e.g., response_format, permissions, mode, etc.).
    """
    subagent: dict[str, Any] = {
        "name": name,
        "description": description,
        "system_prompt": system_prompt,
        "tools": list(tools) if tools is not None else [createOrUpdateTodo, renderTodoBoard],
    }

    if model is not None:
        subagent["model"] = model
    if skills is not None:
        subagent["skills"] = skills
    if interrupt_on is not None:
        subagent["interrupt_on"] = interrupt_on
    if middleware is not None:
        subagent["middleware"] = middleware

    subagent.update(kwargs)
    return subagent  # type: ignore[return-value]
