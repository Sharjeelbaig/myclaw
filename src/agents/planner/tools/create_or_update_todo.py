from langchain.tools import tool

from agents.planner.classes.Task import Task
from agents.planner.classes.Todo import Todo
from agents.planner.store import load_todos, save_todos


@tool
def createOrUpdateTodo(
    todo_id: str,
    title: str,
    description: str,
    tasks: list[Task],
) -> str:
    """Create a new todo board, or replace an existing one."""
    todos = load_todos()
    todos[todo_id] = Todo(
        todo_id=todo_id,
        title=title,
        description=description,
        tasks=tasks,
    )
    save_todos(todos)
    return f"Saved todo '{todo_id}' with {len(tasks)} task(s)."
