"""
Task Tracker MCP Server

An MCP server that provides tools to manage tasks in the Task Tracker app.
Tasks have: id, title, description, status (todo | in_progress | done), and optional dueDate.
"""

import json
import uuid
from datetime import datetime
from typing import Any

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Task Tracker")

# In-memory task store
tasks: dict[str, dict[str, Any]] = {}


@mcp.tool()
def list_tasks(status: str | None = None) -> str:
    """
    List all tasks, optionally filtered by status.

    Args:
        status: Optional filter – one of 'todo', 'in_progress', or 'done'.
                When omitted all tasks are returned.

    Returns:
        JSON array of task objects sorted by dueDate (tasks without a dueDate
        appear last).
    """
    result = list(tasks.values())

    if status is not None:
        valid = {"todo", "in_progress", "done"}
        if status not in valid:
            return json.dumps({"error": f"Invalid status '{status}'. Must be one of: {', '.join(sorted(valid))}"})
        result = [t for t in result if t["status"] == status]

    # Sort by dueDate; tasks without one come last
    def sort_key(t: dict[str, Any]) -> tuple:
        due = t.get("dueDate")
        return (1, "") if due is None else (0, due)

    result.sort(key=sort_key)
    return json.dumps(result, indent=2)


@mcp.tool()
def create_task(
    title: str,
    description: str = "",
    status: str = "todo",
    due_date: str | None = None,
) -> str:
    """
    Create a new task.

    Args:
        title:       Short title for the task (required).
        description: Longer description of the task (optional).
        status:      Initial status – 'todo', 'in_progress', or 'done' (default: 'todo').
        due_date:    Optional due date in ISO 8601 format (YYYY-MM-DD).

    Returns:
        JSON object representing the newly created task.
    """
    valid_statuses = {"todo", "in_progress", "done"}
    if status not in valid_statuses:
        return json.dumps({"error": f"Invalid status '{status}'. Must be one of: {', '.join(sorted(valid_statuses))}"})

    if due_date is not None:
        try:
            datetime.fromisoformat(due_date)  # validate format only; store the raw string
        except ValueError:
            return json.dumps({"error": f"Invalid due_date '{due_date}'. Use ISO 8601 format (YYYY-MM-DD)."})

    task_id = str(uuid.uuid4())
    task: dict[str, Any] = {
        "id": task_id,
        "title": title.strip(),
        "description": description.strip(),
        "status": status,
        "dueDate": due_date,
    }
    tasks[task_id] = task
    return json.dumps(task.copy(), indent=2)


@mcp.tool()
def update_task(
    task_id: str,
    title: str | None = None,
    description: str | None = None,
    status: str | None = None,
    due_date: str | None = None,
) -> str:
    """
    Update an existing task.  Only the fields you provide will be changed.

    Args:
        task_id:     ID of the task to update (required).
        title:       New title (optional).
        description: New description (optional).
        status:      New status – 'todo', 'in_progress', or 'done' (optional).
        due_date:    New due date in ISO 8601 format, or empty string to clear it (optional).

    Returns:
        JSON object representing the updated task, or an error message.
    """
    if task_id not in tasks:
        return json.dumps({"error": f"Task '{task_id}' not found."})

    task = tasks[task_id]

    if title is not None:
        task["title"] = title.strip()

    if description is not None:
        task["description"] = description.strip()

    if status is not None:
        valid_statuses = {"todo", "in_progress", "done"}
        if status not in valid_statuses:
            return json.dumps({"error": f"Invalid status '{status}'. Must be one of: {', '.join(sorted(valid_statuses))}"})
        task["status"] = status

    if due_date is not None:
        if due_date == "":
            task["dueDate"] = None
        else:
            try:
                datetime.fromisoformat(due_date)  # validate format only; store the raw string
            except ValueError:
                return json.dumps({"error": f"Invalid due_date '{due_date}'. Use ISO 8601 format (YYYY-MM-DD)."})
            task["dueDate"] = due_date

    return json.dumps(task.copy(), indent=2)


@mcp.tool()
def delete_task(task_id: str) -> str:
    """
    Delete a task by its ID.

    Args:
        task_id: ID of the task to delete (required).

    Returns:
        Confirmation message, or an error if the task was not found.
    """
    if task_id not in tasks:
        return json.dumps({"error": f"Task '{task_id}' not found."})

    removed = tasks.pop(task_id)
    return json.dumps({"message": f"Task '{removed['title']}' (id: {task_id}) deleted successfully."})


if __name__ == "__main__":
    mcp.run()
