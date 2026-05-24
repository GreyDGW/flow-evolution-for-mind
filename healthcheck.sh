#!/bin/bash
# ════════════════════════════════════════════════════
#  Flow Ecosystem 全链路健康检查
#  一键诊断: 数据采集 → 切割 → 分析 → 调音 → 报告
# ════════════════════════════════════════════════════

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
DB_PATH="$PROJECT_DIR/data/flow_ecosystem.db"
OPENCLAW_DIR="$HOME/.openclaw"
PASS=0
WARN=0
FAIL=0

check() {
  local label="$1" status="$2" detail="$3"
  if [ "$status" = "PASS" ]; then
    echo -e "  ${GREEN}✅ $label${NC} $detail"
    PASS=$((PASS+1))
  elif [ "$status" = "WARN" ]; then
    echo -e "  ${YELLOW}⚠️  $label${NC} $detail"
    WARN=$((WARN+1))
  else
    echo -e "  ${RED}❌ $label${NC} $detail"
    FAIL=$((FAIL+1))
  fi
}

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   🏥 Flow Ecosystem 全链路健康检查         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""
echo "  检查时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# ==========================================
# Layer 0: 环境
# ==========================================
echo -e "${YELLOW}[Layer 0] 环境依赖${NC}"
echo "----------------------------------------"

PYTHON_VER=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
NODE_VER=$(node --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
OPENCLAW_VER=$(openclaw --version 2>&1 | head -1 || echo "未安装")

check "Python 3.11+" "$([ "$(echo "$PYTHON_VER >= 3.11" | bc -l 2>/dev/null || echo "0")" = "1" ] && echo PASS || echo WARN)" "v$PYTHON_VER"
check "Node.js 18+" "$([ "$(echo "$NODE_VER >= 18" | bc -l 2>/dev/null || echo "0")" = "1" ] && echo PASS || echo WARN)" "v$NODE_VER"
check "OpenClaw CLI" "$(command -v openclaw &>/dev/null && echo PASS || echo FAIL)" "$OPENCLAW_VER"
check "sqlite3 命令" "$(command -v sqlite3 &>/dev/null && echo PASS || echo FAIL)" ""
check "sqlite3 npm 模块" "$(cd "$PROJECT_DIR/adapters/openclaw/plugin" && node -e "require('sqlite3')" 2>/dev/null && echo PASS || echo FAIL)" ""

# ==========================================
# Layer 1: 文件完整性
# ==========================================
echo ""
echo -e "${YELLOW}[Layer 1] 文件完整性${NC}"
echo "----------------------------------------"

PLUGIN_DIR="$PROJECT_DIR/adapters/openclaw/plugin"

for f in \
  "$PLUGIN_DIR/package.json" \
  "$PLUGIN_DIR/dist/index.js" \
  "$PLUGIN_DIR/dist/hooks/counter.js" \
  "$PLUGIN_DIR/dist/hooks/injector.js" \
  "$PLUGIN_DIR/openclaw.plugin.json" \
  "$PLUGIN_DIR/dist/soul-protocols/zh-CN/portraits.json" \
  "$PROJECT_DIR/adapters/openclaw/scripts/flow_handler.py" \
  "$PROJECT_DIR/adapters/openclaw/scripts/SKILL.md" \
  "$PROJECT_DIR/plugin/session_analyzer.py" \
  "$PROJECT_DIR/plugin/state_distiller.py" \
  "$PROJECT_DIR/plugin/llm_client.py" \
  "$PROJECT_DIR/importer/incremental.py" \
  "$PROJECT_DIR/scripts/start_poll.sh" \
  "$PROJECT_DIR/scripts/stop_all.sh" \
  "$PROJECT_DIR/install_v2.sh"; do
  name="$(basename "$f")"
  check "$name" "$([ -f "$f" ] && echo PASS || echo FAIL)" ""
done

# ==========================================
# Layer 2: 数据库状态
# ==========================================
echo ""
echo -e "${YELLOW}[Layer 2] 数据库${NC}"
echo "----------------------------------------"

if [ -f "$DB_PATH" ]; then
  DB_SIZE=$(ls -lh "$DB_PATH" | awk '{print $5}')
  check "数据库存在" "PASS" "($DB_SIZE)"

  TOTAL=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sessions;" 2>/dev/null || echo "0")
  LATEST=$(sqlite3 "$DB_PATH" "SELECT MAX(timestamp) FROM sessions;" 2>/dev/null || echo "无数据")
  TODAY=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sessions WHERE timestamp > datetime('now','-1 day');" 2>/dev/null || echo "0")

  check "sessions 表" "PASS" "$TOTAL 条 (最新: ${LATEST:-无})"
  check "今日新数据" "$([ "$TODAY" -gt "0" ] && echo PASS || echo WARN)" "$TODAY 条"

  ANALYSES=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM session_analyses;" 2>/dev/null || echo "0")
  PORTRAITS=$(sqlite3 "$DB_PATH" "SELECT COUNT(DISTINCT portrait_label) FROM session_analyses;" 2>/dev/null || echo "0")
  LAST_ANALYSIS=$(sqlite3 "$DB_PATH" "SELECT MAX(created_at) FROM session_analyses;" 2>/dev/null || echo "无")

  check "session_analyses" "PASS" "$ANALYSES 条 ($PORTRAITS 种 Portrait, 最新: ${LAST_ANALYSIS:-无})"

  # kv_store 关键检查
  STYLE_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM kv_store WHERE key='current_style';" 2>/dev/null || echo "0")
  COUNTER_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM kv_store WHERE key='msg_counter';" 2>/dev/null || echo "0")

  check "current_style (injector 用)" "$([ "$STYLE_COUNT" -gt "0" ] && echo PASS || echo FAIL)" "$STYLE_COUNT 个 agent"
  check "msg_counter (counter 用)" "$([ "$COUNTER_COUNT" -gt "0" ] && echo PASS || echo WARN)" "$COUNTER_COUNT 个 agent"
else
  check "数据库" "FAIL" "不存在！请先运行 install_v2.sh 或 python3 init.py"
fi

# ==========================================
# Layer 3: Gateway + Plugin
# ==========================================
echo ""
echo -e "${YELLOW}[Layer 3] Gateway + Plugin${NC}"
echo "----------------------------------------"

GW_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18789/ 2>/dev/null || echo "000")
GW_TIME=$(curl -s -o /dev/null -w "%{time_total}" http://127.0.0.1:18789/ 2>/dev/null || echo "999")

check "Gateway HTTP" "$([ "$GW_CODE" = "200" ] && echo PASS || echo FAIL)" "HTTP $GW_CODE (${GW_TIME}s)"

if [ "$GW_CODE" = "200" ]; then
  # 检查插件列表
  PLUGIN_LIST=$(/usr/local/bin/openclaw plugins list 2>&1 || echo "")
  if echo "$PLUGIN_LIST" | grep -q "flow-evolution-for-mind"; then
    check "插件注册" "PASS" "在 Gateway 插件列表中"
  else
    check "插件注册" "WARN" "未在列表中（可能需要重启 Gateway）"
  fi

  # 检查加载日志
  LOG_FILE=$(ls -t /tmp/openclaw*.log 2>/dev/null | head -1)
  if [ -n "$LOG_FILE" ]; then
    LOADED=$(grep -c '\[flow-style\].*Plugin loaded' "$LOG_FILE" 2>/dev/null || echo "0")
    HOOK_READY=$(grep -c '\[flow-style\].*All hooks ready' "$LOG_FILE" 2>/dev/null || echo "0")
    INJECTING=$(grep -c '\[flow-style\].*Injecting 4D' "$LOG_FILE" 2>/dev/null || echo "0")

    check "Plugin 加载" "$([ "$LOADED" -gt "0" ] && echo PASS || echo WARN)" "$LOADED 次"
    check "Hook 就绪" "$([ "$HOOK_READY" -gt "0" ] && echo PASS || echo WARN)" "$HOOK_READY 次"
    check "调音注入触发" "$([ "$INJECTING" -gt "0" ] && echo PASS || echo WARN)" "$INJECTING 次 (需要真实对话触发)"
  else
    check "Plugin 日志" "WARN" "未找到 Gateway 日志文件"
  fi
else
  check "Gateway 运行" "FAIL" "未响应，请启动: nohup openclaw gateway run --port 18789"
fi

# ==========================================
# Layer 4: 后台进程
# ==========================================
echo ""
echo -e "${YELLOW}[Layer 4] 后台进程${NC}"
echo "----------------------------------------"

POLL_PID=""
if [ -f "$PROJECT_DIR/logs/poll.pid" ]; then
  POLL_PID=$(cat "$PROJECT_DIR/logs/poll.pid" 2>/dev/null)
fi

if [ -n "$POLL_PID" ] && ps -p "$POLL_PID" > /dev/null 2>&1; then
  check "轮询引擎" "PASS" "PID=$POLL_PID 运行中"
else
  # 尝试按进程名查找
  POLL_PS=$(ps aux | grep "incremental\|run_async_collector" | grep -v grep | awk '{print $2}' | head -1)
  if [ -n "$POLL_PS" ]; then
    check "轮询引擎" "PASS" "PID=$POLL_PS (非 PID 文件方式)"
  else
    check "轮询引擎" "FAIL" "未运行！执行: bash scripts/start_poll.sh"
  fi
fi

# ==========================================
# Layer 5: 报告生成能力
# ==========================================
echo ""
echo -e "${YELLOW}[Layer 5] 报告生成${NC}"
echo "----------------------------------------"

if [ -f "$DB_PATH" ]; then
  REPORT_TEST=$(cd "$PROJECT_DIR" && timeout 30 python3 adapters/openclaw/scripts/flow_handler.py --time-keyword week 2>&1 | head -5 || echo "TIMEOUT")

  if echo "$REPORT_TEST" | grep -q "认知分析报告"; then
    check "flow_handler.py" "PASS" "可正常输出报告"
  elif echo "$REPORT_TEST" | grep -q "TIMEOUT"; then
    check "flow_handler.py" "WARN" "超时(>30s)，可能 LLM API 不可达"
  else
    check "flow_handler.py" "WARN" "返回异常，查看输出"
  fi

  # Scanner 测试
  SCANNER_OUT=$(cd "$PROJECT_DIR" && timeout 15 python3 adapters/openclaw/scripts/flow_handler.py --update-style --agent main --turn-count 1 2>&1 || echo "TIMEOUT")
  if echo "$SCANNER_OUT" | grep -q "Initialized\|KEEP\|Updated"; then
    check "Style Scanner" "PASS" "可正常执行"
  else
    check "Style Scanner" "WARN" "可能 LLM API 不可达"
  fi
else
  check "报告生成" "SKIP" "数据库不存在"
fi

# ==========================================
# Summary
# ==========================================
echo ""
echo -e "${BLUE}════════════════════════════════════════════${NC}"
TOTAL=$((PASS + WARN + FAIL))
echo -e "  ${GREEN}✅ 通过: $PASS${NC}  ${YELLOW}⚠️  警告: $WARN${NC}  ${RED}❌ 失败: $FAIL${NC}  总计: $TOTAL"
echo -e "${BLUE}════════════════════════════════════════════${NC}"

if [ "$FAIL" -gt 0 ]; then
  echo ""
  echo -e "  ${RED}🔴 存在 $FAIL 个失败项，请修复后重试${NC}"
  echo -e "  建议: bash install_v2.sh"
  exit 1
elif [ "$WARN" -gt 0 ]; then
  echo ""
  echo -e "  ${YELLOW}🟡 存在 $WARN 个警告项，功能可能受限${NC}"
  exit 0
else
  echo ""
  echo -e "  ${GREEN}🎉 全链路健康！所有检查通过${NC}"
  exit 0
fi
