import json
from pathlib import Path

from config import WORKSPACE_ROOT
from agents.planner.classes.Todo import Todo


def todos_file() -> Path:
    """Return the project-level todo file used by all planner invocations."""
    return WORKSPACE_ROOT / "myclaw" / "todo.json"


def load_todos() -> dict[str, Todo]:
    path = todos_file()
    if not path.exists():
        return {}
    raw = json.loads(path.read_text())
    return {tid: Todo.model_validate(data) for tid, data in raw.items()}


def save_todos(todos: dict[str, Todo]) -> None:
    path = todos_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = {tid: todo.model_dump() for tid, todo in todos.items()}
    path.write_text(json.dumps(raw, indent=2))
