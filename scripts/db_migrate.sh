#!/bin/bash
# Database migration helper script
# Usage: ./scripts/db_migrate.sh [command]
#   stamp     - Mark current DB as up-to-date (for existing databases)
#   upgrade   - Run pending migrations
#   history   - Show migration history
#   current   - Show current revision

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Load .env if exists
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)
fi

if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL not set"
    echo "Set it in .env or export DATABASE_URL=postgresql://user@host/db"
    exit 1
fi

cd "$PROJECT_DIR/backend"

case "${1:-upgrade}" in
    stamp)
        echo "Stamping database as current..."
        alembic stamp head
        echo "Done. Database marked as up-to-date."
        ;;
    upgrade)
        echo "Running pending migrations..."
        alembic upgrade head
        echo "Done."
        ;;
    history)
        alembic history --verbose
        ;;
    current)
        alembic current
        ;;
    *)
        echo "Usage: $0 {stamp|upgrade|history|current}"
        exit 1
        ;;
esac
