#!/bin/bash
# Flow Ecosystem - 启动后台轮询引擎
# Usage: bash scripts/start_poll.sh

cd "$(dirname "$0")/.."

echo "========================================"
echo "启动 Flow Ecosystem 轮询引擎"
echo "========================================"

# 检查 Python 环境
if ! command -v python3 &>/dev/null; then
    echo "❌ 错误: 未找到 python3"
    exit 1
fi

# 检查增量导入模块
if [ ! -f "importer/incremental.py" ]; then
    echo "❌ 错误: 未找到 importer/incremental.py"
    exit 1
fi

# 创建日志目录
mkdir -p logs

# 检查是否已有轮询进程在运行
PID_FILE="logs/poll.pid"
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "⚠️ 轮询进程已在运行 (PID: $OLD_PID)"
        echo "如需重启，请先执行: bash scripts/stop_all.sh"
        exit 1
    else
        echo "ℹ️ 发现残留 PID 文件，已清理"
        rm -f "$PID_FILE"
    fi
fi

# 启动轮询引擎（后台运行）
python3 -c '
import sys
sys.path.insert(0, ".")
from importer.incremental import run_async_collector
import os

jsonl_dir = os.path.expanduser("~/.openclaw/agents")
db_path = "data/flow_ecosystem.db"

print(f"🚀 启动轮询引擎...")
print(f"   监控目录: {jsonl_dir}")
print(f"   数据库: {db_path}")
print(f"   轮询间隔: 30 秒")
print(f"   日志文件: logs/poll.log")
print("")

try:
    run_async_collector(
        jsonl_dir=jsonl_dir,
        db_path=db_path,
        poll_interval=30,
        batch_size=50,
        state_path=".collect_state.json"
    )
except KeyboardInterrupt:
    print("\n✅ 轮询引擎已停止")
' > logs/poll.log 2>&1 &

PID=$!
echo $PID > "$PID_FILE"

echo ""
echo "✅ 轮询引擎已启动"
echo "   PID: $PID"
echo "   日志: logs/poll.log"
echo ""
echo "查看日志: tail -f logs/poll.log"
echo "停止引擎: bash scripts/stop_all.sh"
echo "========================================"
