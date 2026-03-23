# Hive CLI

A command-line tool for [BWH Hive](https://github.com/buildwithhussain/bwh_hive) — like `gh` for GitHub, but for your Hive project management instance.

Create tasks, assign them, mark them done, and check your dashboard — all from the terminal. Works with any Hive instance over the Frappe REST API v2.

## Installation

```bash
pip install git+https://github.com/BuildWithHussain/hive-cli.git
```

Or install in editable mode for development:

```bash
git clone https://github.com/BuildWithHussain/hive-cli.git
cd hive-cli
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

### Smart Name Resolution

You don't need to remember project IDs or task IDs. The CLI resolves names automatically:

- **Projects** — pass a project name, slug, or ID. If ambiguous, you'll be prompted to pick.
- **Tasks** — pass a task title (or part of it) or an ID. If multiple match, you'll pick interactively.

### Tasks

```bash
# Create a task — use the project name, not the ID
hive task create "Fix login redirect bug" -p "Hive" --priority High

# Create with all options
hive task create "Add dark mode" \
  -p "Hive" \
  --priority Medium \
  --status "To Do" \
  --assign dev@example.com \
  --due 2026-04-15 \
  --description "Support system-level dark mode preference"

# List tasks
hive task list                              # all tasks
hive task list --mine                       # my tasks
hive task list -p "Hive"                   # by project name
hive task list -s "In Progress"            # by status
hive task list -a dev@example.com          # by assignee

# View task details + comments — by title or ID
hive task view "Fix login"

# Add a comment to a task
hive task comment "Fix login" "looks good, merging"

# Assign a task — by title
hive task assign "Fix login" dev@example.com

# Mark as done — by title
hive task done "Fix login"

# Update fields — by title
hive task update "Add dark mode" --status "In Progress" --priority Urgent --due 2026-04-01
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

## Interactive Picker

When a name matches multiple results, the CLI shows a numbered list and lets you pick:

```
$ hive task done "login"

Multiple tasks found:
  1. Fix login redirect bug  [In Progress]  HIVE-TASK-00042
  2. Add login page tests    [To Do]        HIVE-TASK-00051

Pick a number: 1
Task HIVE-TASK-00042 marked as Done
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
    ├── create TITLE       Create a new task (-p accepts project name)
    ├── list               List tasks with filters
    ├── view TASK          View full details + comments (accepts title or ID)
    ├── comment TASK MSG   Add a comment to a task (accepts title or ID)
    ├── assign TASK USER   Assign a task (accepts title or ID)
    ├── done TASK          Mark a task as done (accepts title or ID)
    └── update TASK        Update task fields (accepts title or ID)
```

## Requirements

- Python 3.10+
- A running BWH Hive instance with API access enabled
- API key and secret for your user account

## How It Works

The CLI is a standalone Python package that communicates with your Hive instance over HTTP using the Frappe REST API v2 (`/api/v2/document/`). It does not require Frappe or bench to be installed on your machine.

Credentials are stored locally at `~/.hive-cli/config.json` with restricted file permissions (600).
