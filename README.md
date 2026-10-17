# Deep Agent Sandbox

An overpowered, Claude Code-comparable Deep Agent built on [Deep Agents](https://github.com/langchain-ai/deepagents), LangGraph, and Docker.

---

## Capabilities & Architecture

- **Claude Code-like Tooling**:
  - Full filesystem tool suite: `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`.
  - Sandboxed Shell Execution: `execute` runs arbitrary commands inside an isolated Docker container mounting the workspace.
  - Isolated Python Container Runner: `python_executor` runs Python scripts/snippets in Docker with resource limits.
  - Planning & Todo Management: Built-in `TodoListMiddleware` (`write_todos`) and specialized `planner-agent` for managing multi-step tasks.
  - Subagent Delegation: `task` tool dynamically routes specialized work to subagents.
- **Skills System**:
  - All 22 skills in `.agents/skills/` are loaded dynamically using progressive disclosure via `SkillsMiddleware`.
  - Comprehensive coverage of LangChain, LangGraph, Deep Agents, Swarm, HITL, persistence, and eval engineering.
- **Grounding Guard (`GroundingGuardMiddleware`)**:
  - Anti-hallucination guard that prevents models from fabricating file modifications or tool results.
  - Auto-normalizes file paths to the workspace mount.
- **Dynamic Component Stacking**:
  - Auto-discovering subagent registry (`src/agents/registry.py`).
  - Scaffolding scripts to stack new subagents, tools, and skills on the fly.

---

## Project Structure

```
├── .agents/skills/        # 22 built-in skills loaded progressively
├── scripts/
│   ├── new_agent.py       # Scaffold subagents (interactive or CLI)
│   ├── new_tool.py        # Scaffold standalone tools in src/tools/
│   └── new_skill.py       # Scaffold skills in .agents/skills/
├── src/
│   ├── main.py            # Deep agent console & streaming REPL
│   ├── config.py          # Workspace & project root config
│   ├── backend/
│   │   └── docker_sandbox.py # DockerSandboxBackend implementing SandboxBackendProtocol
│   ├── tools/
│   │   └── python_executor.py # Dockerized Python execution tool
│   └── agents/
│       ├── registry.py    # Auto-discovers and bundles subagents
│       ├── guard.py       # Grounding guard middleware
│       └── planner/       # Built-in planner subagent
└── tmp/                   # Workspace root mounted to /workspace in Docker
```

---

## Running the Agent

### Start the Interactive Console

```bash
uv run python src/main.py
```

### Environment Configuration

| Variable | Default | Purpose |
|---|---|---|
| `AGENT_MODEL` | `gemma4:e2b-it-qat` | Ollama model name / tag |
| `AGENT_WORKSPACE` | `tmp/` (under project root) | Workspace directory on host |
| `DOCKER_SANDBOX_IMAGE` | `python:3.12-slim` | Docker image used for sandbox command execution |
| `DOCKER_SANDBOX_TIMEOUT`| `120` | Timeout in seconds for shell commands |
| `DOCKER_SANDBOX_MEMORY` | `512m` | Memory limit for Docker container |
| `DOCKER_SANDBOX_CPUS`   | `1` | CPU limit for Docker container |

---

## Component Stacking (CLI Scaffolders)

### 1. Scaffold a Subagent
```bash
# Interactive:
uv run python scripts/new_agent.py

# Non-interactive CLI:
uv run python scripts/new_agent.py --name reviewer --description "Reviews code against style guidelines" --tools reviewCode,checkLints --with-store
```
Subagents created in `src/agents/<name>/` are **automatically discovered** and plugged into the main agent via `src/agents/registry.py`.

### 2. Scaffold a Tool
```bash
# Interactive:
uv run python scripts/new_tool.py

# Non-interactive CLI:
uv run python scripts/new_tool.py --name webSearch --description "Searches the web for documentation"
```

### 3. Scaffold a Skill
```bash
# Interactive:
uv run python scripts/new_skill.py

# Non-interactive CLI:
uv run python scripts/new_skill.py --name git-workflows --description "Best practices for branching and commit conventions"
```
New skills placed under `.agents/skills/<name>/SKILL.md` are immediately discoverable on the agent's next run.
