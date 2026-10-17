import os
from pathlib import Path

from deepagents import create_deep_agent
from langchain_core.messages import AIMessageChunk
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel

from backend.docker_sandbox import DockerSandboxBackend
from tools.python_executor import python_executor
from agents.guard import GroundingGuardMiddleware
from agents.registry import get_all_subagents
from config import PROJECT_ROOT, WORKSPACE_ROOT

console = Console()

# The model is swappable: set AGENT_MODEL to any Ollama model/tag, e.g.
#   AGENT_MODEL=gemma4:e2b-it-qat uv run ./src/main.py
MODEL_NAME = os.getenv("AGENT_MODEL", "gemma4:e2b-it-qat")
WORKSPACE_MOUNT = "/workspace/"
SKILLS_DIR = PROJECT_ROOT / ".agents" / "skills"

# Docker sandbox backend isolates bash & shell command execution in a container
# while mounting the host workspace directory (defaults to tmp/).
backend = DockerSandboxBackend(root_dir=str(WORKSPACE_ROOT))

model = ChatOllama(
    model=MODEL_NAME,
    temperature=0,
    num_ctx=16384,
    top_k=50,
    reasoning=True,
)

# Load skills progressively from .agents/skills
skills_paths = [str(SKILLS_DIR)] if SKILLS_DIR.exists() else None

# Auto-discover all subagents registered in src/agents/
subagents = get_all_subagents(model)

agent = create_deep_agent(
    model=model,
    checkpointer=MemorySaver(),
    store=InMemoryStore(),
    backend=backend,
    skills=skills_paths,
    tools=[
        python_executor,
    ],
    subagents=subagents,
    middleware=[
        GroundingGuardMiddleware(workspace_path=WORKSPACE_MOUNT),
    ],
)

config = {"configurable": {"thread_id": "user-123"}}


def _text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                parts.append(str(block.get("text", "")))
            else:
                parts.append(str(getattr(block, "text", "") or ""))
        return "".join(parts)
    return ""


def _tool_names(chunk) -> list[str]:
    names = []
    for call in getattr(chunk, "tool_call_chunks", None) or []:
        name = call.get("name") if isinstance(call, dict) else getattr(call, "name", None)
        if name:
            names.append(name)
    return names


skills_count = len([d for d in SKILLS_DIR.iterdir() if d.is_dir()]) if SKILLS_DIR.exists() else 0
subagent_names = [s["name"] for s in subagents]

banner = (
    f"[bold cyan]Deep Agent Console[/bold cyan] (Claude Code Comparable)\n"
    f"[dim]Model:[/dim] [yellow]{MODEL_NAME}[/yellow]   "
    f"[dim]Workspace:[/dim] [green]{WORKSPACE_ROOT}[/green]   "
    f"[dim]Docker Sandbox:[/dim] [cyan]{backend.docker_image}[/cyan]\n"
    f"[dim]Skills loaded:[/dim] [bold]{skills_count}[/bold] skills in .agents/skills/   "
    f"[dim]Subagents:[/dim] [magenta]{', '.join(subagent_names) or 'None'}[/magenta]"
)
console.print(Panel(banner, border_style="cyan"))

while True:
    try:
        user_input = console.input("[bold green]You:[/bold green] ")
    except (EOFError, KeyboardInterrupt):
        console.print()
        break

    buffer = ""
    used: list[str] = []
    with Live(
        Markdown(""),
        console=console,
        refresh_per_second=12,
        vertical_overflow="visible",
    ) as live:
        for chunk in agent.stream(
            {"messages": [{"role": "user", "content": user_input}]},
            stream_mode="messages",
            subgraphs=True,
            version="v2",
            config=config,
        ):
            if isinstance(chunk, dict) and chunk.get("type") == "messages":
                token, metadata = chunk["data"]
                if isinstance(token, AIMessageChunk):
                    used.extend(_tool_names(token))
                    text = _text(token.content)
                    if text:
                        buffer += text
                        live.update(Markdown(buffer))
    if used:
        console.print(f"[dim]· tools: {', '.join(dict.fromkeys(used))}[/dim]")
    console.print()
