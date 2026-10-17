"""Dynamic registry and auto-discovery for Deep Agents subagents.

Scans the src/agents/ directory for agent packages that expose a
`create_<name>_subagent` factory and provides them as a unified list.
"""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import Any

from deepagents import SubAgent

logger = logging.getLogger(__name__)

AGENTS_DIR = Path(__file__).resolve().parent


def discover_subagent_factories() -> dict[str, Any]:
    """Scan src/agents for subagent factories."""
    factories = {}
    for item in AGENTS_DIR.iterdir():
        if item.is_dir() and not item.name.startswith(("_", ".")):
            agent_file = item / "agent.py"
            if agent_file.exists():
                module_name = f"agents.{item.name}.agent"
                try:
                    module = importlib.import_module(module_name)
                    expected_func = f"create_{item.name}_subagent"
                    if hasattr(module, expected_func):
                        factories[item.name] = getattr(module, expected_func)
                    elif hasattr(module, "create_subagent"):
                        factories[item.name] = getattr(module, "create_subagent")
                except Exception as e:
                    logger.warning("Could not load subagent module %s: %s", module_name, e)
    return factories


def get_all_subagents(model: Any = None, **overrides: Any) -> list[SubAgent]:
    """Instantiate and return all discovered subagents."""
    factories = discover_subagent_factories()
    subagents = []
    for name, factory in factories.items():
        try:
            agent_overrides = overrides.get(name, {})
            subagents.append(factory(model, **agent_overrides))
        except Exception as e:
            logger.warning("Failed to initialize subagent %s: %s", name, e)
    return subagents
