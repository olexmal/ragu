# Task Tracking Guide

This repository uses GitHub Issues and Projects for task management.

## Quick Start

### Option 1: Using GitHub Web Interface

1. **Create a Task Issue:**
   - Go to: https://github.com/olexmal/ragu/issues/new
   - Select "Task" template
   - Fill in the details
   - Submit

2. **Create a Project Board:**
   - Go to: https://github.com/olexmal/ragu/projects
   - Click "New project"
   - Choose a template (Kanban, Table, etc.)
   - Add issues to the project

### Option 2: Using GitHub CLI (Recommended)

First, install and authenticate:

```bash
# Install GitHub CLI
sudo apt install gh

# Authenticate
gh auth login

# Verify
gh auth status
```

Then use these commands:

```bash
# Create a new task
gh issue create --title "[TASK] Your task title" --body "Task description" --label task

# List all open tasks
gh issue list --label task

# View a specific task
gh issue view <number>

# Close a task
gh issue close <number>

# Add task to project
gh project item-add <project-number> --owner olexmal --repo ragu --url <issue-url>
```

## Issue Templates

We have three issue templates:

1. **Task** (`.github/ISSUE_TEMPLATE/task.md`) - For development tasks
2. **Bug Report** (`.github/ISSUE_TEMPLATE/bug.md`) - For bug tracking
3. **Feature Request** (`.github/ISSUE_TEMPLATE/feature.md`) - For new features

## Labels

Recommended labels for organizing tasks:

- `task` - General development task
- `bug` - Bug fix
- `enhancement` - Feature enhancement
- `documentation` - Documentation updates
- `ui/ux` - Frontend changes
- `backend` - Backend changes
- `priority:high` - High priority
- `priority:medium` - Medium priority
- `priority:low` - Low priority
- `in-progress` - Currently being worked on
- `blocked` - Blocked by another issue

## Project Boards

Create a Kanban board to visualize task progress:

1. Go to Projects tab
2. Create new project
3. Add columns: Backlog, To Do, In Progress, Review, Done
4. Add issues to the board

## Best Practices

1. **Create issues for all tasks** - Even small tasks should be tracked
2. **Use clear titles** - Start with [TASK], [BUG], or [FEATURE]
3. **Add acceptance criteria** - Define what "done" means
4. **Link related issues** - Use "Related Issues" section
5. **Update status** - Move issues through project board columns
6. **Close when done** - Don't leave completed tasks open

## Example Workflow

```bash
# 1. Create a task
gh issue create --title "[TASK] Add user authentication" \
  --body "Implement JWT-based authentication for the API" \
  --label task,backend,priority:high

# 2. Start working (add to project board manually or via web)
# 3. Update issue with progress
gh issue comment <number> --body "Started implementation, working on JWT middleware"

# 4. Close when done
gh issue close <number> --comment "Completed and tested"
```

## Integration with Commits

Link commits to issues in your commit messages:

```bash
git commit -m "feat: Add user authentication

Closes #123
Implements JWT-based auth as requested in #123"
```

GitHub will automatically link the commit to the issue.

