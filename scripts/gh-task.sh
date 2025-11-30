#!/bin/bash
# GitHub Task Management Helper Script
# Usage: ./scripts/gh-task.sh [command] [options]

REPO="olexmal/ragu"

case "$1" in
  create)
    TITLE="$2"
    BODY="$3"
    if [ -z "$TITLE" ]; then
      echo "Usage: $0 create \"[TASK] Title\" \"Description\""
      exit 1
    fi
    gh issue create --repo "$REPO" --title "$TITLE" --body "${BODY:-No description}" --label task 2>/dev/null || \
    gh issue create --repo "$REPO" --title "$TITLE" --body "${BODY:-No description}"
    ;;
  list)
    echo "All tasks/issues:"
    gh issue list --repo "$REPO" --state all
    ;;
  view)
    if [ -z "$2" ]; then
      echo "Usage: $0 view <issue-number>"
      exit 1
    fi
    gh issue view "$2" --repo "$REPO"
    ;;
  close)
    if [ -z "$2" ]; then
      echo "Usage: $0 close <issue-number>"
      exit 1
    fi
    gh issue close "$2" --repo "$REPO"
    ;;
  open)
    echo "Open tasks/issues:"
    gh issue list --repo "$REPO" --state open
    ;;
  *)
    echo "GitHub Task Management Helper"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  create \"[TASK] Title\" \"Description\"  - Create a new task"
    echo "  list                                    - List all tasks"
    echo "  open                                    - List open tasks"
    echo "  view <number>                           - View a specific task"
    echo "  close <number>                          - Close a task"
    echo ""
    echo "Examples:"
    echo "  $0 create \"[TASK] Add feature X\" \"Implement feature X with Y and Z\""
    echo "  $0 list"
    echo "  $0 view 123"
    echo "  $0 close 123"
    exit 1
    ;;
esac

