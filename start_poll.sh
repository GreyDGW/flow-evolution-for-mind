#!/bin/bash
cd "$(dirname "$0")"
python3 -c '
import sys
sys.path.insert(0, ".")
from importer.incremental import run_async_collector
run_async_collector("~/.openclaw/agents", "data/flow_ecosystem.db", 30)
' > logs/poll.log 2>&1 &
echo "轮询已启动，PID: $!"
