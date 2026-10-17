#!/usr/bin/env python3
"""Scaffold a new generic and highly customizable subagent.

Usage:
    # Interactive mode:
    uv run python scripts/new_agent.py

    # Non-interactive CLI mode:
    uv run python scripts/new_agent.py --name weather --description "Weather forecaster" --tools getWeather,getForecast
    uv run python scripts/new_agent.py --name reviewer --description "Code reviewer" --with-store
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = ROOT / "src" / "agents"

NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def camel_to_snake(name: str) -> str:
    """createOrUpdateTodo -> create_or_update_todo"""
    step1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    step2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", step1)
    return step2.lower()


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or default


def ask_bool(prompt: str, default: bool = False) -> bool:
    default_str = "Y/n" if default else "y/N"
    value = input(f"{prompt} [{default_str}]: ").strip().lower()
    if not value:
        return default
    return value in ("y", "yes")


def parse_tools_str(raw: str) -> list[str]:
    if not raw:
        return []
    names = [t.strip() for t in raw.split(",") if t.strip()]
    bad = [t for t in names if not IDENT_RE.match(t)]
    if bad:
        raise ValueError(f"Invalid tool identifiers: {', '.join(bad)}")
    seen: set[str] = set()
    unique: list[str] = []
    for t in names:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return unique


def prompt_source(system_prompt: str) -> str:
    safe = system_prompt.replace('"""', '\\"\\"\\"')
    return f'SYSTEM_PROMPT = """{safe}"""\n'


def agent_source(name: str, description: str, tools: list[str]) -> str:
    imports = [
        "from __future__ import annotations",
        "",
        "from typing import Any, Sequence",
        "from deepagents import SubAgent",
        f"from agents.{name}.prompt import SYSTEM_PROMPT",
    ]
    for tool in tools:
        imports.append(f"from agents.{name}.tools.{camel_to_snake(tool)} import {tool}")

    tools_list_repr = f"[{', '.join(tools)}]" if tools else "[]"

    fn_body = f'''def create_{name}_subagent(
    model: Any = None,
    *,
    name: str = "{name}",
    description: str = {json.dumps(description)},
    system_prompt: str = SYSTEM_PROMPT,
    tools: Sequence[Any] | None = None,
    skills: list[str] | None = None,
    interrupt_on: dict[str, Any] | None = None,
    middleware: list[Any] | None = None,
    **kwargs: Any,
) -> SubAgent:
    """Create a configured SubAgent dictionary for the {name} agent.

    Supports custom overrides and kwargs accepted by deepagents.SubAgent:
    (e.g., response_format, permissions, mode, etc.).
    """
    subagent: dict[str, Any] = {{
        "name": name,
        "description": description,
        "system_prompt": system_prompt,
        "tools": list(tools) if tools is not None else {tools_list_repr},
    }}

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
'''

    return "\n".join(imports) + "\n\n\n" + fn_body


def tool_source(tool_name: str) -> str:
    return (
        "from langchain.tools import tool\n"
        "\n"
        "\n"
        "@tool\n"
        f"def {tool_name}() -> str:\n"
        '    """TODO: describe what this tool does and when the model should call it."""\n'
        "    return \"\"\n"
    )


def store_source(name: str) -> str:
    return (
        "import json\n"
        "from pathlib import Path\n"
        "\n"
        "from config import WORKSPACE_ROOT\n"
        "\n"
        "\n"
        f"def {name}_store_file() -> Path:\n"
        f'    """Return the persistent file path used by the {name} agent."""\n'
        f'    return WORKSPACE_ROOT / "{name}" / "data.json"\n'
        "\n"
        "\n"
        "def load_data() -> dict:\n"
        f"    path = {name}_store_file()\n"
        "    if not path.exists():\n"
        "        return {}\n"
        "    return json.loads(path.read_text())\n"
        "\n"
        "\n"
        "def save_data(data: dict) -> None:\n"
        f"    path = {name}_store_file()\n"
        "    path.parent.mkdir(parents=True, exist_ok=True)\n"
        "    path.write_text(json.dumps(data, indent=2))\n"
    )


def scaffold_subagent(
    name: str,
    description: str,
    system_prompt: str,
    tools: list[str],
    with_store: bool = False,
) -> Path:
    agent_dir = AGENTS_DIR / name
    tools_dir = agent_dir / "tools"
    classes_dir = agent_dir / "classes"

    tools_dir.mkdir(parents=True)
    classes_dir.mkdir(parents=True)

    (agent_dir / "__init__.py").write_text("")
    (classes_dir / "__init__.py").write_text("")
    (tools_dir / "__init__.py").write_text("")
    (agent_dir / "prompt.py").write_text(prompt_source(system_prompt))
    (agent_dir / "agent.py").write_text(agent_source(name, description, tools))

    for tool in tools:
        (tools_dir / f"{camel_to_snake(tool)}.py").write_text(tool_source(tool))

    if with_store:
        (agent_dir / "store.py").write_text(store_source(name))

    return agent_dir


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold a generic, highly customizable subagent for deep-agents."
    )
    parser.add_argument("--name", help="Agent name in snake_case (e.g. researcher)")
    parser.add_argument(
        "--description",
        help="Agent description used by orchestrator to pick the agent",
    )
    parser.add_argument("--prompt", help="System prompt for the subagent")
    parser.add_argument(
        "--tools",
        help="Comma-separated list of tool names (e.g. searchWeb,fetchDoc)",
    )
    parser.add_argument(
        "--with-store",
        action="store_true",
        help="Scaffold store.py for local workspace disk persistence",
    )

    args = parser.parse_args()

    # If flags were provided via CLI
    if args.name or args.description or args.tools:
        name = (args.name or "").strip()
        if not NAME_RE.match(name):
            print(f"Error: Invalid agent name '{name}'. Use snake_case starting with a letter.", file=sys.stderr)
            return 1
        if (AGENTS_DIR / name).exists():
            print(f"Error: Agent src/agents/{name} already exists.", file=sys.stderr)
            return 1

        description = (args.description or "").strip()
        if not description:
            print("Error: --description is required.", file=sys.stderr)
            return 1

        system_prompt = args.prompt or f"You are the {name} agent. {description}"
        try:
            tools = parse_tools_str(args.tools or "")
        except ValueError as err:
            print(f"Error: {err}", file=sys.stderr)
            return 1
        with_store = args.with_store
    else:
        # Interactive mode
        print("== New subagent ==\n")
        while True:
            name = ask("Agent name (snake_case, e.g. weather)")
            if not NAME_RE.match(name):
                print("  ! lowercase letters/digits/underscores only, start with a letter")
                continue
            if (AGENTS_DIR / name).exists():
                print(f"  ! src/agents/{name} already exists")
                continue
            break

        while True:
            description = ask("Description (the orchestrator reads this to pick the agent)")
            if description:
                break
            print("  ! description is required")

        default_prompt = f"You are the {name} agent. {description}"
        system_prompt = ask("System prompt", default=default_prompt)

        while True:
            raw_tools = ask("Tools (comma separated, e.g. getWeather, getForecast)")
            try:
                tools = parse_tools_str(raw_tools)
                break
            except ValueError as err:
                print(f"  ! {err}")

        with_store = ask_bool("Include store.py for disk persistence?", default=False)

    agent_dir = scaffold_subagent(
        name=name,
        description=description,
        system_prompt=system_prompt,
        tools=tools,
        with_store=with_store,
    )

    print(f"\nCreated src/agents/{name}/\n")
    for path in sorted(agent_dir.rglob("*.py")):
        print(f"  {path.relative_to(ROOT)}")

    print("\nNext steps:")
    if tools:
        print(f"  1. Fill in the tool bodies in src/agents/{name}/tools/")
    else:
        print(f"  1. Define tools in src/agents/{name}/tools/ (if any)")
    print("  2. Wire it into src/main.py:")
    print(f"       from agents.{name}.agent import create_{name}_subagent")
    print(f"       subagents=[..., create_{name}_subagent(model)]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
