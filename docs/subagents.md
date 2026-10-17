# Creating a subagent

A **subagent** is a smaller, focused agent that the main agent can delegate to via `deepagents`'s `task` tool.
Every subagent lives in its own folder and follows the same unified shape, making scaffolding and registration standardized.

> Rule: subagents are self-contained. A subagent never imports another subagent.
> If two agents need the same code, move that code somewhere shared instead.

## 1. Run the scaffolder

From the project root, you can run the scaffolder either **interactively** or directly via **CLI flags**:

### Interactive mode:
```bash
uv run python scripts/new_agent.py
```

It prompts for:

| Prompt | Example | Notes |
|---|---|---|
| Agent name | `weather` | lowercase `snake_case`; becomes the folder name |
| Description | `Looks up weather for a city.` | the main agent reads this to decide when to delegate |
| System prompt | *(press Enter to accept the default)* | the agent's instructions |
| Tools | `getWeather, getForecast` | comma separated; each becomes a tool file |
| Include store.py? | `y/N` | scaffolds a disk-backed persistence helper (`store.py`) |

### Non-interactive CLI mode:
```bash
# Basic agent
uv run python scripts/new_agent.py --name weather --description "Looks up weather for a city." --tools getWeather,getForecast

# Agent with disk persistence
uv run python scripts/new_agent.py --name reviewer --description "Reviews code against style rules" --with-store
```

The script **never overwrites** an existing agent folder.

## 2. What it creates

```
src/agents/weather/
├─ __init__.py
├─ agent.py          # create_weather_subagent(...) -> SubAgent
├─ prompt.py         # SYSTEM_PROMPT
├─ tools/
│  ├─ __init__.py
│  ├─ get_weather.py
│  └─ get_forecast.py
├─ classes/
│  └─ __init__.py
└─ store.py          # (optional) persistence helper
```

- `agent.py`: Wires the agent together into a `deepagents.SubAgent` spec dictionary. Supports overriding `model`, `tools`, `skills`, `interrupt_on`, `middleware`, and any other `SubAgent` kwargs (e.g. `mode="fork"`, `response_format`).
- `prompt.py`: Holds the system prompt as a single `SYSTEM_PROMPT` string.
- `tools/`: Holds one file per tool.
- `classes/`: Where this agent's Pydantic models go.
- `store.py`: (Optional) workspace-scoped file persistence helper.

## 3. Code the tools

Each tool file starts as a standard LangChain `@tool` function:

```python
from langchain.tools import tool

@tool
def getWeather(city: str) -> str:
    """Return the current weather for a city."""
    return f"It is sunny in {city}."
```

Replace the stub with the real logic. The **docstring matters** — that is what the model reads to decide when to call the tool, so describe it clearly.

> Keep the function name in `camelCase` (e.g. `getWeather`) and the file name in
> `snake_case` (e.g. `get_weather.py`). The scaffolder handles this naming convention automatically.

## 4. Add models or storage (optional)

- Put Pydantic models in `classes/` (e.g. `classes/Report.py`).
- If the agent needs file persistence on disk, use `--with-store` or create `store.py` next to `agent.py`. See [`src/agents/planner/store.py`](file:///Users/shazi/Practice/deep-agent-sb/src/agents/planner/store.py) for a working reference.

The planner stores its shared board at `<AGENT_WORKSPACE>/myclaw/todo.json`. With the default configuration, `<AGENT_WORKSPACE>` is `tmp/`, so the file is `tmp/myclaw/todo.json`. This is intentionally project-scoped rather than thread-scoped, allowing the planner and its renderer to share the same board.

## 5. Wire it into the main agent

In `src/main.py`, import the factory and pass it to `subagents`:

```python
from agents.planner.agent import create_planner_subagent
from agents.weather.agent import create_weather_subagent

agent = create_deep_agent(
    model=model,
    checkpointer=MemorySaver(),
    backend=backend,
    tools=[python_executor],
    subagents=[
        create_planner_subagent(model),
        # Can use default model or override model/tools/skills/etc:
        create_weather_subagent(model),
    ],
)
```

Because `create_<name>_subagent` accepts keyword arguments, you can also customize it per-deployment:
```python
create_weather_subagent(
    model="ollama:qwen2.5:7b",
    skills=["/workspace/skills/meteorology/"],
    interrupt_on={"publishForecast": True},
)
```

## 6. Structure reference

| Component | Convention | Example |
|---|---|---|
| Folder (agent name) | `snake_case` | `weather` |
| Factory | `create_<name>_subagent(model=None, **kwargs) -> SubAgent` | `create_weather_subagent` |
| Prompt | `SYSTEM_PROMPT` in `prompt.py` | |
| Tool function | `camelCase` | `getWeather` |
| Tool file | `snake_case` of the function | `get_weather.py` |
| Model class | `PascalCase.py` in `classes/` | `Todo.py` |
| Store helper | `store.py` | `store.py` |
