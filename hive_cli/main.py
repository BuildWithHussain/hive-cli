"""BWH Hive CLI - manage tasks from the terminal."""

import click
from rich.console import Console
from rich.table import Table

from hive_cli.config import get_client, get_config, save_config
from hive_cli.resolve import resolve_project, resolve_task

console = Console()


HELP_TEXT = """
Hive CLI - manage your projects and tasks from the terminal.

\b
Quick Start:
  hive login                                  Authenticate with your Hive instance
  hive task create "Fix bug" -p "My Project"  Create a task (use project name)
  hive task assign "Fix bug" user@mail.com    Assign by task title
  hive task done "Fix bug"                    Mark done by task title

\b
Common Workflows:
  hive task list --mine                       Show my open tasks
  hive task list -p "My Project" -s "To Do"   Filter by project name & status
  hive task view "Fix bug"                    View full details + comments
  hive task comment "Fix bug" "looks good"    Add a comment to a task
  hive task update "Fix bug" --priority High
  hive dashboard                              Personal dashboard overview
  hive project list                           List all projects

\b
Name Resolution:
  Projects accept: name, slug, or ID (fuzzy matched)
  Tasks accept: title search or ID (picks interactively if ambiguous)

\b
Authentication:
  Generate API keys from your Frappe user settings:
  User > API Access > Generate Keys
  Then run `hive login` to save your credentials.
"""


@click.group(help=HELP_TEXT)
@click.version_option(package_name="hive-cli")
def cli():
    pass


# ── Auth ──────────────────────────────────────────────────────────────


@cli.command()
@click.option("--url", prompt="Hive URL (e.g. https://pms.example.com)", help="Site URL")
@click.option("--api-key", prompt="API Key", help="Frappe API key")
@click.option("--api-secret", prompt="API Secret", hide_input=True, help="Frappe API secret")
def login(url: str, api_key: str, api_secret: str):
    """Authenticate with your Hive instance."""
    from hive_cli.client import HiveClient

    client = HiveClient(url=url, api_key=api_key, api_secret=api_secret)
    try:
        user = client.call_method("frappe.auth.get_logged_user")
        save_config({"url": url.rstrip("/"), "api_key": api_key, "api_secret": api_secret})
        console.print(f"Logged in as [bold green]{user}[/]")
    except SystemExit:
        console.print("[red]Login failed. Check your URL and credentials.[/]")


@cli.command()
def whoami():
    """Show the currently authenticated user."""
    client = get_client()
    user = client.call_method("frappe.auth.get_logged_user")
    config = get_config()
    console.print(f"[bold]{user}[/] on {config['url']}")


@cli.command()
def logout():
    """Remove saved credentials."""
    save_config({})
    console.print("Logged out.")


# ── Projects ──────────────────────────────────────────────────────────


@cli.group()
def project():
    """Manage projects."""
    pass


@project.command("list")
@click.option("--limit", "-l", default=20, help="Number of projects to show")
def project_list(limit: int):
    """List your projects."""
    client = get_client()
    projects = client.get_list(
        "Hive Project",
        fields=["name", "title", "slug", "status"],
        filters={"is_archived": 0},
        order_by="modified desc",
        limit=limit,
    )

    if not projects:
        console.print("No projects found.")
        return

    table = Table(title="Projects")
    table.add_column("Slug", style="cyan")
    table.add_column("Title", style="bold")
    table.add_column("Status")
    for p in projects:
        table.add_row(p.get("slug", p["name"]), p["title"], p.get("status", ""))
    console.print(table)


# ── Tasks ─────────────────────────────────────────────────────────────


@cli.group()
def task():
    """Manage tasks."""
    pass


@task.command("create")
@click.argument("title")
@click.option("--project", "-p", required=True, help="Project name, slug, or ID")
@click.option(
    "--priority",
    type=click.Choice(["Low", "Medium", "High", "Urgent"], case_sensitive=False),
    default="Medium",
)
@click.option(
    "--status",
    type=click.Choice(["Backlog", "To Do", "In Progress"], case_sensitive=False),
    default="To Do",
)
@click.option("--assign", "-a", help="Email of user to assign")
@click.option("--due", "-d", help="Due date (YYYY-MM-DD)")
@click.option("--description", help="Task description")
def task_create(title: str, project: str, priority: str, status: str, assign: str, due: str, description: str):
    """Create a new task. PROJECT can be a name, slug, or ID."""
    client = get_client()
    project_id = resolve_project(client, project)

    data = {"title": title, "project": project_id, "priority": priority, "status": status}
    if assign:
        data["assigned_to"] = assign
    if due:
        data["due_date"] = due
    if description:
        data["description"] = description

    result = client.create_doc("Hive Task", data)
    name = result.get("name", result) if isinstance(result, dict) else result
    console.print(f"Task created: [bold green]{name}[/] - {title}")


@task.command("list")
@click.option("--project", "-p", help="Filter by project (name, slug, or ID)")
@click.option("--status", "-s", type=click.Choice(["Backlog", "To Do", "In Progress", "Done", "Blocked"], case_sensitive=False))
@click.option("--assigned", "-a", help="Filter by assigned user email")
@click.option("--mine", "-m", is_flag=True, help="Show only my tasks")
@click.option("--limit", "-l", default=20, help="Number of tasks to show")
def task_list(project: str, status: str, assigned: str, mine: bool, limit: int):
    """List tasks with optional filters."""
    client = get_client()

    filters: dict = {"is_archived": 0}
    if project:
        filters["project"] = resolve_project(client, project)
    if status:
        filters["status"] = status
    if assigned:
        filters["_assign"] = ["like", f"%{assigned}%"]
    if mine:
        user = client.call_method("frappe.auth.get_logged_user")
        filters["_assign"] = ["like", f"%{user}%"]

    tasks = client.get_list(
        "Hive Task",
        fields=["name", "title", "status", "priority", "assigned_to", "project", "due_date"],
        filters=filters,
        order_by="modified desc",
        limit=limit,
    )

    if not tasks:
        console.print("No tasks found.")
        return

    table = Table(title="Tasks")
    table.add_column("ID", style="dim")
    table.add_column("Title", style="bold")
    table.add_column("Status")
    table.add_column("Priority")
    table.add_column("Assigned To")
    table.add_column("Due Date")
    for t in tasks:
        status_style = {
            "Done": "green",
            "In Progress": "yellow",
            "Blocked": "red",
            "Backlog": "dim",
            "To Do": "cyan",
        }.get(t.get("status", ""), "")
        table.add_row(
            t["name"],
            t["title"],
            f"[{status_style}]{t.get('status', '')}[/]",
            t.get("priority", ""),
            t.get("assigned_to", ""),
            str(t.get("due_date", "") or ""),
        )
    console.print(table)


@task.command("view")
@click.argument("task_id")
def task_view(task_id: str):
    """View a task's details. TASK_ID can be an ID or title search."""
    client = get_client()
    task_id = resolve_task(client, task_id)
    t = client.get_doc("Hive Task", task_id)

    status_style = {
        "Done": "green", "In Progress": "yellow", "Blocked": "red",
        "Backlog": "dim", "To Do": "cyan",
    }.get(t.get("status", ""), "")
    priority_style = {
        "Urgent": "bold red", "High": "red", "Medium": "yellow", "Low": "dim",
    }.get(t.get("priority", ""), "")

    console.print(f"\n[bold]{t['title']}[/]  [dim]{t['name']}[/]")
    console.print()
    console.print(f"  Status:       [{status_style}]{t.get('status', '-')}[/]")
    console.print(f"  Priority:     [{priority_style}]{t.get('priority', '-')}[/]")
    console.print(f"  Project:      {t.get('project', '-')}")
    console.print(f"  Assigned To:  {t.get('assigned_to') or '-'}")
    console.print(f"  Size:         {t.get('size') or '-'}")
    console.print(f"  Start Date:   {t.get('start_date') or '-'}")
    console.print(f"  Due Date:     {t.get('due_date') or '-'}")
    console.print(f"  Completed On: {t.get('completed_on') or '-'}")
    console.print(f"  Milestone:    {t.get('milestone') or '-'}")
    console.print(f"  Depends On:   {t.get('depends_on') or '-'}")
    console.print(f"  PR Link:      {t.get('pr_link') or '-'}")
    console.print(f"  UAT Status:   {t.get('uat_status') or '-'}")
    if t.get("uat_approved_by"):
        console.print(f"  UAT By:       {t['uat_approved_by']} ({t.get('uat_date', '')})")
    console.print(f"  Created By:   {t.get('owner', '-')}")
    console.print(f"  Created:      {t.get('creation', '-')}")
    console.print(f"  Modified:     {t.get('modified', '-')}")
    if t.get("description"):
        console.print(f"\n  [bold]Description:[/]")
        console.print(f"  [dim]{t['description']}[/]")

    # Fetch comments
    comments = client.get_list(
        "Hive Task Comment",
        fields=["content", "posted_by", "creation"],
        filters={"task": task_id, "is_archived": 0},
        order_by="creation asc",
        limit=50,
    )
    if comments:
        console.print(f"\n  [bold]Comments ({len(comments)}):[/]")
        for comment in comments:
            console.print(f"\n  [cyan]{comment.get('posted_by', '')}[/]  [dim]{comment.get('creation', '')}[/]")
            console.print(f"  {comment.get('content', '')}")

    console.print()


@task.command("comment")
@click.argument("task_id")
@click.argument("content")
def task_comment(task_id: str, content: str):
    """Add a comment to a task. TASK_ID can be an ID or title search."""
    client = get_client()
    task_id = resolve_task(client, task_id)
    user = client.call_method("frappe.auth.get_logged_user")
    result = client.create_doc("Hive Task Comment", {
        "task": task_id,
        "content": content,
        "posted_by": user,
    })
    name = result.get("name", result) if isinstance(result, dict) else result
    console.print(f"Comment [bold green]{name}[/] added to {task_id}")


@task.command("assign")
@click.argument("task_id")
@click.argument("user_email")
def task_assign(task_id: str, user_email: str):
    """Assign a task to a user. TASK_ID can be an ID or title search."""
    client = get_client()
    task_id = resolve_task(client, task_id)
    client.update_doc("Hive Task", task_id, {"assigned_to": user_email})
    console.print(f"Task [bold]{task_id}[/] assigned to [green]{user_email}[/]")


@task.command("done")
@click.argument("task_id")
def task_done(task_id: str):
    """Mark a task as done. TASK_ID can be an ID or title search."""
    client = get_client()
    task_id = resolve_task(client, task_id)
    client.update_doc("Hive Task", task_id, {"status": "Done"})
    console.print(f"Task [bold]{task_id}[/] marked as [green]Done[/]")


@task.command("update")
@click.argument("task_id")
@click.option("--title", help="New title")
@click.option("--status", type=click.Choice(["Backlog", "To Do", "In Progress", "Done", "Blocked"], case_sensitive=False))
@click.option("--priority", type=click.Choice(["Low", "Medium", "High", "Urgent"], case_sensitive=False))
@click.option("--due", help="Due date (YYYY-MM-DD)")
@click.option("--assign", help="Assign to user email")
def task_update(task_id: str, title: str, status: str, priority: str, due: str, assign: str):
    """Update a task's fields. TASK_ID can be an ID or title search."""
    data = {}
    if title:
        data["title"] = title
    if status:
        data["status"] = status
    if priority:
        data["priority"] = priority
    if due:
        data["due_date"] = due
    if assign:
        data["assigned_to"] = assign

    if not data:
        console.print("[yellow]Nothing to update. Pass at least one option.[/]")
        return

    client = get_client()
    task_id = resolve_task(client, task_id)
    client.update_doc("Hive Task", task_id, data)
    console.print(f"Task [bold]{task_id}[/] updated.")


# ── Dashboard ─────────────────────────────────────────────────────────


@cli.command()
def dashboard():
    """Show your personal dashboard - tasks grouped by project."""
    client = get_client()
    data = client.call_method("bwh_hive.bwh_hive.api.get_my_dashboard")

    if not data:
        console.print("No data.")
        return

    grouped = data.get("tasks_by_project", [])
    if not grouped:
        console.print("No active tasks assigned to you.")
        return

    for group in grouped:
        console.print(f"\n[bold cyan]{group.get('project_title', group.get('project'))}[/]")
        for t in group.get("tasks", []):
            status = t.get("status", "")
            style = {"In Progress": "yellow", "To Do": "cyan", "Blocked": "red", "Backlog": "dim"}.get(status, "")
            due = f" (due {t['due_date']})" if t.get("due_date") else ""
            console.print(f"  [{style}]{status:<12}[/] {t['title']}{due}  [dim]{t['name']}[/]")

    console.print()


if __name__ == "__main__":
    cli()
