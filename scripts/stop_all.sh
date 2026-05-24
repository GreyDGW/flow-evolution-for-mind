#!/bin/bash
# Flow Ecosystem - Kill background processes & clean DB locks
# Usage: bash scripts/stop_all.sh

echo "Stopping all Flow Ecosystem background processes..."

pkill -9 -f "flow_handler.py" 2>/dev/null && echo "✅ flow_handler stopped" || echo "ℹ️ no flow_handler running"

DB_DIR="${FLOW_DB_DIR:-$(dirname "$0")/../data}"
rm -f "$DB_DIR"/flow_ecosystem.db-wal "$DB_DIR"/flow_ecosystem.db-shm 2>/dev/null
echo "✅ SQLite lock files cleaned"

echo ""
echo "You can now safely run reports without 'database is locked' errors."
