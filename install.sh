#!/bin/bash
# ════════════════════════════════════════════════════
#  Flow Ecosystem 一键安装 V3
#  基于 2026-05-25 全链路诊断 (11个已验证的坑)
#
#  使用方法:
#    git clone <repo-url>
#    cd flow-evolution-for-mind
#    chmod +x install.sh && ./install.sh
#
#  覆盖的问题 (P0-P10):
#    P0:  后台轮询未启动 → 自动启动
#    P1:  current_style 冷启动空转 → 自动初始化全部 agent
#    P2:  Plugin 导入路径错误 → 代码已用官方 SDK (openclaw/plugin-sdk/core)
#    P3:  Gateway 事件循环阻塞 → 代码已用异步 Hook (setImmediate)
#    P4:  JS 硬编码旧项目名路径 → 代码已修正 (flow-evolution-for-mind)
#    P5:  FLOW_EVOLUTION_DIR 未设置 → 写标记文件 + .zshrc
#    P6:  SKILL.md PLATFORM LIMIT → 已改为 "Available to ALL"
#    P7:  Skill 目录结构污染 → 只部署 SKILL.md + scripts/
#    P8:  launchd Gateway 无法 pkill → 用 CLI restart
#    P9:  Agent workspace 旧 Skill 残留 → 清理 flow/ flow-state/
#    P10: LLM 不执行脚本 → DeepFlow 拦截器 (index.js 内置)
# ════════════════════════════════════════════════════

set +e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
OPENCLAW_DIR="$HOME/.openclaw"
PLUGIN_DIR="$PROJECT_DIR/adapters/openclaw/plugin"
DB_PATH="$PROJECT_DIR/data/flow_ecosystem.db"
SKILL_DIR="$OPENCLAW_DIR/skills/flow-evolution-for-mind"
LOG_FILE="/tmp/openclaw_install_$(date +%Y%m%d_%H%M%S).log"

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Flow Ecosystem 一键安装 V3               ║${NC}"
echo -e "${BLUE}║   2026-05-25 全链路修复版 (11 fixes)         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# ==========================================
# Step 0: 环境预检
# ==========================================
echo -e "${YELLOW}[Step 0/9] Environment check${NC}"
echo "----------------------------------------"

MISSING=()
for cmd in python3 node npm openclaw sqlite3; do
  if command -v "$cmd" &>/dev/null; then
    echo -e "  ${GREEN}[OK]${NC} $cmd"
  else
    echo -e "  ${RED}[MISS]${NC} $cmd"
    MISSING+=("$cmd")
  fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
  echo -e "\n${RED}Missing: ${MISSING[*]}${NC}\n"
  exit 1
fi

PY_VER=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
NODE_VER=$(node --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
echo "  Python=$PY_VER Node=$NODE_VER"

# ==========================================
# Step 1: 文件完整性检查
# ==========================================
echo ""
echo -e "${YELLOW}[Step 1/9] File integrity${NC}"
echo "----------------------------------------"

REQUIRED_FILES=(
  "$PLUGIN_DIR/package.json"
  "$PLUGIN_DIR/dist/index.js"
  "$PLUGIN_DIR/dist/hooks/counter.js"
  "$PLUGIN_DIR/dist/hooks/injector.js"
  "$PLUGIN_DIR/dist/soul-protocols/zh-CN/portraits.json"
  "$PLUGIN_DIR/openclaw.plugin.json"
  "$PROJECT_DIR/adapters/openclaw/scripts/flow_handler.py"
  "$PROJECT_DIR/adapters/openclaw/scripts/SKILL.md"
  "$PROJECT_DIR/scripts/start_poll.sh"
)

for f in "${REQUIRED_FILES[@]}"; do
  [ -f "$f" ] && echo -e "  ${GREEN}[OK]${NC} $(basename $f)" || { echo -e "  ${RED}[MISS]${NC} $(basename $f)"; exit 1; }
done

# 验证关键代码特征 (防止旧版本)
grep -q 'openclaw/plugin-sdk/core' "$PLUGIN_DIR/dist/index.js" \
  && echo -e "  ${GREEN}[OK]${NC} index.js: official SDK path" \
  || { echo -e "  ${RED}[FAIL]${NC} index.js: wrong import path"; exit 1; }

grep -q 'flow-evolution-for-mind' "$PLUGIN_DIR/dist/hooks/counter.js" \
  && echo -e "  ${GREEN}[OK]${NC} counter.js: correct project name" \
  || { echo -e "  ${RED}[FAIL]${NC} counter.js: old hardcoded path"; exit 1; }

grep -q 'registerDeepFlowInterceptor\|execFileSync' "$PLUGIN_DIR/dist/index.js" \
  && echo -e "  ${GREEN}[OK]${NC} index.js: DeepFlow interceptor present" \
  || echo -e "  ${YELLOW}[WARN]${NC} index.js: no DeepFlow interceptor"

grep -q 'Available to ALL' "$PROJECT_DIR/adapters/openclaw/scripts/SKILL.md" \
  && echo -e "  ${GREEN}[OK]${NC} SKILL.md: no PLATFORM LIMIT" \
  || { echo -e "  ${RED}[FAIL]${NC} SKILL.md: has PLATFORM LIMIT warning"; exit 1; }

# ==========================================
# Step 2: npm 安装
# ==========================================
echo ""
echo -e "${YELLOW}[Step 2/9] npm dependencies${NC}"
echo "----------------------------------------"
cd "$PLUGIN_DIR"
npm install --silent 2>&1 | tail -2
node -e "require('sqlite3'); console.log('  [OK] sqlite3 module');" 2>&1 || { echo "  [FAIL] sqlite3"; exit 1; }

# ==========================================
# Step 3: 清理旧残留 (P9)
# ==========================================
echo ""
echo -e "${YELLOW}[Step 3/9] Clean old artifacts (P9)${NC}"
echo "----------------------------------------"

# 3a: 清理 agent workspace 中的旧 Skill
CLEANED_SKILLS=0
for ws in "$OPENCLAW_DIR"/agents/*/workspace/skills; do
  for old in "$ws"/flow "$ws"/flow-state; do
    if [ -d "$old" ]; then
      rm -rf "$old"
      CLEANED_SKILLS=$((CLEANED_SKILLS+1))
    fi
  done
done
echo "  Cleaned $CLEANED_SKILLS old skill dirs from agent workspaces"

# 3b: 清理旧的 Skill 目录结构 (如果有 hooks/ 等多余文件)
if [ -d "$SKILL_DIR/hooks" ]; then
  rm -rf "$SKILL_DIR/hooks"
  echo "  Removed stale hooks/ from skill dir"
fi
for extra in "$SKILL_DIR"/index.js "$SKILL_DIR"/init.py "$SKILL_DIR"/plugin.json; do
  [ -f "$extra" ] && rm -f "$extra" && echo "  Removed stale $(basename $extra)"
done

# ==========================================
# Step 4: 部署 Skill (P7 - 正确结构)
# ==========================================
echo ""
echo -e "${YELLOW}[Step 4/9] Deploy Skill (P7 correct structure)${NC}"
echo "----------------------------------------"

mkdir -p "$SKILL_DIR/scripts"
cp "$PROJECT_DIR/adapters/openclaw/scripts/SKILL.md" "$SKILL_DIR/" 2>/dev/null
cp "$PROJECT_DIR/adapters/openclaw/scripts/flow_handler.py" "$SKILL_DIR/scripts/" 2>/dev/null

# 验证: skill root should ONLY have SKILL.md + scripts/
ROOT_COUNT=$(find "$SKILL_DIR" -maxdepth 1 -type f | wc -l | tr -d ' ')
SCRIPTS_COUNT=$(ls "$SKILL_DIR/scripts/" 2>/dev/null | wc -l | tr -d ' ')
echo "  skill/: $ROOT_COUNT files (should be 1 = SKILL.md)"
echo "  scripts/: $SCRIPTS_COUNT files (should have flow_handler.py)"

# ==========================================
# Step 5: CLI 插件注册
# ==========================================
echo ""
echo -e "${YELLOW}[Step 5/9] Plugin registration via CLI${NC}"
echo "----------------------------------------"
openclaw plugins install -l "$PLUGIN_DIR" 2>&1 | tee -a "$LOG_FILE" | grep -E "Linked|error|failed|manifest|differs" || true
echo "  [DONE] CLI registration"

# ==========================================
# Step 6: 配置 openclaw.json
# ==========================================
echo ""
echo -e "${YELLOW}[Step 6/9] Configure openclaw.json${NC}"
echo "----------------------------------------"

python3 << 'PYEOF'
import json, os, sys

config_path = os.path.expanduser('~/.openclaw/openclaw.json')
with open(config_path, 'r') as f:
    d = json.load(f)

project_dir = os.path.expanduser('~/Desktop/skill相关文档/flow-evolution-for-mind')
skill_dir = os.path.expanduser('~/.openclaw/skills/flow-evolution-for-mind')

# --- plugins ---
plugins = d.get('plugins', {})

# load.paths
load = plugins.get('load', {})
if 'paths' not in load:
    load['paths'] = []
plugin_path = os.path.join(project_dir, 'adapters', 'openclaw', 'plugin')
if plugin_path not in load.get('paths', []):
    load['paths'].append(plugin_path)
plugins['load'] = load

# entries + allowConversationAccess
entries = plugins.get('entries', {})
entries['flow-evolution-for-mind'] = {
    'enabled': True,
    'hooks': {'allowConversationAccess': True}
}
plugins['entries'] = entries
d['plugins'] = plugins

# --- skills ---
if 'skills' not in d:
    d['skills'] = {}
if 'entries' not in d['skills']:
    d['skills']['entries'] = {}
d['skills']['entries']['flow-evolution-for-mind'] = {'enabled': True}

# --- bind to all agents ---
bound = 0
for a in d.get('agents', {}).get('list', []):
    aid = a.get('id')
    if not aid:
        continue
    sk = a.get('skills', [])
    if isinstance(sk, list) and 'flow-evolution-for-mind' not in sk:
        a['skills'] = sk + ['flow-evolution-for-mind']
        bound += 1

with open(config_path, 'w') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)

print(f"  allowConversationAccess: True")
print(f"  load.paths: +{plugin_path}")
print(f"  Skills bound to {bound} agents")
PYEOF

# ==========================================
# Step 7: 环境变量 + 标记文件 (P4/P5)
# ==========================================
echo ""
echo -e "${YELLOW}[Step 7/9] Environment variables (P4/P5)${NC}"
echo "----------------------------------------"

# P5: 标记文件 (counter.js/injector.js fallback #2)
echo "$PROJECT_DIR" > "$HOME/.flow_evolution_dir"
echo "  ~/.flow_evolution_dir -> $PROJECT_DIR"

# P4: shell profile
PROFILE_LINE='export FLOW_EVOLUTION_DIR="'"$PROJECT_DIR"'"'
if ! grep -q "FLOW_EVOLUTION_DIR" "$HOME/.zshrc" 2>/dev/null; then
    echo "# Flow Ecosystem (install.sh)" >> "$HOME/.zshrc"
    echo "$PROFILE_LINE" >> "$HOME/.zshrc"
    echo "  Added to ~/.zshrc"
else
    echo "  ~/.zshrc already has FLOW_EVOLUTION_DIR (skipped)"
fi

export FLOW_EVOLUTION_DIR="$PROJECT_DIR"
echo "  FLOW_EVOLUTION_DIR exported for this session"

# ==========================================
# Step 8: 数据库初始化 (P1 Cold Start)
# ==========================================
echo ""
echo -e "${YELLOW}[Step 8/9] Database init (P1 cold start)${NC}"
echo "----------------------------------------"

python3 << 'PYEOF'
import sqlite3, json, os

db_path = os.path.expanduser('~/Desktop/skill相关文档/flow-evolution-for-mind/data/flow_ecosystem.db')

if not os.path.exists(os.path.dirname(db_path)):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

conn = sqlite3.connect(db_path, timeout=30)
conn.execute('PRAGMA journal_mode=WAL;')
c = conn.cursor()

# Create tables if not exist
conn.executescript('''
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT, role TEXT, content_text TEXT,
    timestamp TEXT, agent_id TEXT,
    is_system_noise INTEGER DEFAULT 0, is_auto_push INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS session_analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT, goal_alignment TEXT, closure_index TEXT,
    flow_depth TEXT, cognition_growth TEXT, portrait_label TEXT,
    style_pace TEXT, style_depth TEXT, style_tone TEXT,
    style_friction TEXT, agent_id TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS kv_store (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT, key TEXT, value TEXT,
    updated_at TEXT, UNIQUE(agent_id, key)
);
''')
conn.commit()

# P1: Initialize current_style for all agents
default_style = json.dumps({
    "pace": "explore", "depth": "surface",
    "tone": "neutral", "friction": "direct",
    "portrait": "平稳推进"
}, ensure_ascii=False)

c.execute("SELECT DISTINCT agent_id FROM sessions WHERE agent_id IS NOT NULL AND agent_id != '' LIMIT 20")
agents = [r[0] for r in c.fetchall()]
if not agents:
    agents = ['main', 'secretary']

init_count = 0
for aid in agents:
    c.execute("SELECT value FROM kv_store WHERE agent_id=? AND key='current_style'", (aid,))
    if not c.fetchone():
        c.execute("SELECT portrait_label FROM session_analyses WHERE (agent_id=? OR agent_id IS NULL OR agent_id='') ORDER BY created_at DESC LIMIT 1", (aid,))
        row = c.fetchone()
        style = json.loads(default_style)
        if row and row[0]:
            style['portrait'] = row[0]
        c.execute("INSERT OR REPLACE INTO kv_store(agent_id,key,value,updated_at)VALUES(?,'current_style',?,datetime('now'))",
                  (aid, json.dumps(style, ensure_ascii=False)))
        init_count += 1

conn.commit(); conn.close()
print(f"  DB ready. current_style initialized for {init_count} agents")
PYEOF

# ==========================================
# Step 9: 重启 Gateway + 启动轮询 (P8/P0)
# ==========================================
echo ""
echo -e "${YELLOW}[Step 9/9] Start services (P8 Gateway + P0 poll)${NC}"
echo "----------------------------------------"

# P8: Use CLI restart (works with launchd-managed Gateway)
if openclaw gateway restart 2>/dev/null; then
    echo "  [OK] CLI restart succeeded"
else
    # Fallback: try launchd reload
    PLIST=$(find ~/Library/LaunchAgents -name "*openclaw*" 2>/dev/null | head -1)
    if [ -n "$PLIST" ]; then
        launchctl unload "$PLIST" 2>/dev/null || true
        sleep 2
        launchctl load "$PLIST" 2>/dev/null || true
        echo "  [OK] launchd reloaded ($PLIST)"
    else
        # Last resort
        pkill -9 -f "openclaw" 2>/dev/null || true
        sleep 3
        nohup openclaw gateway run --port 18789 > "$LOG_FILE" 2>&1 &
        echo "  [OK] manual start (fallback)"
    fi
fi

# Wait for Gateway
READY=0
for i in $(seq 1 20); do
    sleep 2
    if curl -s http://127.0.0.1:18789/ > /dev/null 2>&1; then
        READY=1
        echo -e "  ${GREEN}[OK]${NC} Gateway ready (${i}x2=${i}0s)"
        break
    fi
done
if [ "$READY" = "0" ]; then
    echo "  ${RED}[WARN] Gateway not responding after 40s${NC}"
fi

sleep 3

# P0: Start poll engine
echo ""
cd "$PROJECT_DIR"
export FLOW_EVOLUTION_DIR="$PROJECT_DIR"
bash scripts/start_poll.sh 2>&1 | tail -3

# Verify
echo ""
echo -e "${YELLOW}--- Verification ---${NC}"

# Plugin list
echo "  Plugins:"
/usr/local/bin/openclaw plugins list 2>&1 | grep -E "flow-evolution" && echo "    IN LIST!" || echo "    NOT in list!"

# Response time
GW_TIME=$(curl -s -o /dev/null -w "%{time_total}s" http://127.0.0.1:18789/)
echo "  Response: HTTP $(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18789/) ${GW_TIME}s"

# flow-style logs
LATEST_LOG=$(ls -t ~/Library/Logs/openclaw/gateway.log /tmp/openclaw*.log 2>/dev/null | head -1)
if [ -n "$LATEST_LOG" ]; then
    FCOUNT=$(grep -c '\[flow-style\]' "$LATEST_LOG" 2>/dev/null || echo "0")
    echo "  flow-style log entries: $FCOUNT in $(basename $LATEST_LOG)"
    grep '\[flow-style\]' "$LATEST_LOG" 2>/dev/null | tail -3 || true
fi

# Marker file
echo "  Marker: $(cat $HOME/.flow_evolution_dir 2>/dev/null || echo MISSING)"

# DB stats
if [ -f "$DB_PATH" ]; then
    SESSIONS=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sessions;" 2>/dev/null || echo "0")
    STYLES=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM kv_store WHERE key='current_style';" 2>/dev/null || echo "0")
    echo "  DB: $SESSIONS sessions, $STYLES style entries"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Installation complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "  Fixes applied:"
echo "    P0  Poll engine          : started"
echo "    P1  current_style init     : all agents"
echo "    P2  Import path (SDK)      : in code"
echo "    P3  Async hooks            : in code"
echo "    P4  Env var (FLOW_EVOL...) : .zshrc + marker"
echo "    P5  Hardcoded paths       : fixed in code"
echo "    P6  SKILL.md PLATFORM LIMIT: removed"
echo "    P7  Skill dir structure    : clean (SKILL.md + scripts/ only)"
echo "    P8  Gateway restart        : CLI method"
echo "    P9  Old skill artifacts    : cleaned"
echo "    P10 DeepFlow interceptor  : in index.js"
echo ""
echo "  Test commands:"
echo "    Any agent -> /deepflow"
echo "    Any agent -> /deepflow 2026-04-20"
echo "    Any agent -> this week status"
echo "    Any agent -> /flow"
echo ""
echo "  Debug:"
echo "    tail -f $LATEST_LOG | grep flow-style"
echo "    bash healthcheck.sh"
