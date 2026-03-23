# Hive CLI

A command-line tool for [BWH Hive](https://github.com/buildwithhussain/bwh_hive) — like `gh` for GitHub, but for your Hive project management instance.

Create tasks, assign them, mark them done, and check your dashboard — all from the terminal. Works with any Hive instance over the Frappe REST API v2.

## Installation

```bash
pip install /path/to/bwh_hive/cli
```

Or install in editable mode for development:

```bash
cd cli
pip install -e .
```

## Setup

**1. Generate API keys** in your Hive instance:

Navigate to **User > Settings > API Access > Generate Keys** and copy the API key and secret.

**2. Login:**

```bash
hive login
```

You'll be prompted for your site URL, API key, and API secret. Credentials are stored in `~/.hive-cli/config.json` (permissions restricted to your user).

## Usage

### Tasks

```bash
# Create a task
hive task create "Fix login redirect bug" -p "PROJ-001" --priority High

# Create with all options
hive task create "Add dark mode" \
  -p "PROJ-001" \
  --priority Medium \
  --status "To Do" \
  --assign dev@example.com \
  --due 2026-04-15 \
  --description "Support system-level dark mode preference"

# List tasks
hive task list                              # all tasks
hive task list --mine                       # my tasks
hive task list -p "PROJ-001"               # by project
hive task list -s "In Progress"            # by status
hive task list -a dev@example.com          # by assignee

# View task details
hive task view TASK-00042

# Assign a task
hive task assign TASK-00042 dev@example.com

# Mark as done
hive task done TASK-00042

# Update fields
hive task update TASK-00042 --status "In Progress" --priority Urgent --due 2026-04-01
```

### Projects

```bash
# List projects
hive project list
hive project list --limit 50
```

### Dashboard

```bash
# Personal dashboard — your tasks grouped by project
hive dashboard
```

### Account

```bash
hive whoami     # show current user and site
hive logout     # clear saved credentials
```

## Command Reference

```
hive
├── login                  Authenticate with your Hive instance
├── logout                 Remove saved credentials
├── whoami                 Show the currently authenticated user
├── dashboard              Personal dashboard — tasks grouped by project
├── project
│   └── list               List projects
└── task
    ├── create TITLE       Create a new task
    ├── list               List tasks with filters
    ├── view TASK_ID       View task details
    ├── assign TASK USER   Assign a task to a user
    ├── done TASK_ID       Mark a task as done
    └── update TASK_ID     Update task fields
```

## Requirements

- Python 3.10+
- A running BWH Hive instance with API access enabled
- API key and secret for your user account

## How It Works

The CLI is a standalone Python package that communicates with your Hive instance over HTTP using the Frappe REST API v2 (`/api/v2/document/`). It does not require Frappe or bench to be installed on your machine.

Credentials are stored locally at `~/.hive-cli/config.json` with restricted file permissions (600).
