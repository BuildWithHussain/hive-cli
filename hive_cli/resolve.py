"""Resolve human-friendly names to Frappe document IDs."""

import click
from rich.console import Console

console = Console()


def resolve_project(client, project_input: str) -> str:
    """Resolve a project name, slug, or ID to its document name.

    Tries in order:
    1. Exact match on name (ID)
    2. Exact match on slug
    3. Exact match on title (case-insensitive)
    4. Fuzzy match on title (LIKE search)
    5. If multiple matches, prompt user to pick one
    """
    # 1. Try exact ID match
    projects = client.get_list(
        "Hive Project",
        fields=["name", "title", "slug"],
        filters={"name": project_input, "is_archived": 0},
        limit=1,
    )
    if projects:
        return projects[0]["name"]

    # 2. Try exact slug match
    projects = client.get_list(
        "Hive Project",
        fields=["name", "title", "slug"],
        filters={"slug": project_input, "is_archived": 0},
        limit=1,
    )
    if projects:
        return projects[0]["name"]

    # 3. Try exact title match
    projects = client.get_list(
        "Hive Project",
        fields=["name", "title", "slug"],
        filters={"title": project_input, "is_archived": 0},
        limit=5,
    )
    if len(projects) == 1:
        return projects[0]["name"]
    if projects:
        return pick_project(projects)

    # 4. Fuzzy title search
    projects = client.get_list(
        "Hive Project",
        fields=["name", "title", "slug"],
        filters={"title": ["like", f"%{project_input}%"], "is_archived": 0},
        limit=10,
    )
    if len(projects) == 1:
        return projects[0]["name"]
    if projects:
        return pick_project(projects)

    console.print(f"[red]No project found matching '{project_input}'[/]")
    console.print("Run [bold]hive project list[/] to see available projects.")
    raise SystemExit(1)


def pick_project(projects: list[dict]) -> str:
    """Prompt the user to pick from multiple matching projects."""
    console.print("\nMultiple projects found:")
    for i, project in enumerate(projects, 1):
        slug = project.get("slug", "")
        console.print(f"  [bold]{i}[/]. {project['title']}  [dim]({slug})[/]")

    choice = click.prompt("\nPick a number", type=int)
    if 1 <= choice <= len(projects):
        return projects[choice - 1]["name"]

    console.print("[red]Invalid choice.[/]")
    raise SystemExit(1)


def resolve_task(client, task_input: str, project: str | None = None) -> str:
    """Resolve a task ID or title search to a task document name.

    Tries in order:
    1. Exact match on name (ID) — e.g. "HIVE-TASK-00042"
    2. Title search (LIKE) within optional project scope
    3. If multiple matches, prompt user to pick one
    """
    # 1. Try exact ID match
    tasks = client.get_list(
        "Hive Task",
        fields=["name", "title", "status", "project"],
        filters={"name": task_input, "is_archived": 0},
        limit=1,
    )
    if tasks:
        return tasks[0]["name"]

    # 2. Search by title
    filters: dict = {"title": ["like", f"%{task_input}%"], "is_archived": 0}
    if project:
        resolved_project = resolve_project(client, project)
        filters["project"] = resolved_project

    tasks = client.get_list(
        "Hive Task",
        fields=["name", "title", "status", "project"],
        filters=filters,
        order_by="modified desc",
        limit=10,
    )
    if len(tasks) == 1:
        return tasks[0]["name"]
    if tasks:
        return pick_task(tasks)

    console.print(f"[red]No task found matching '{task_input}'[/]")
    raise SystemExit(1)


def pick_task(tasks: list[dict]) -> str:
    """Prompt the user to pick from multiple matching tasks."""
    console.print("\nMultiple tasks found:")
    for i, task in enumerate(tasks, 1):
        status = task.get("status", "")
        console.print(f"  [bold]{i}[/]. {task['title']}  [{status}]  [dim]{task['name']}[/]")

    choice = click.prompt("\nPick a number", type=int)
    if 1 <= choice <= len(tasks):
        return tasks[choice - 1]["name"]

    console.print("[red]Invalid choice.[/]")
    raise SystemExit(1)
