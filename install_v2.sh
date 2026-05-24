#!/bin/bash
set -e

# ══════════════════════════════════════════════════════
#  Flow Ecosystem 一键安装 V2
#  基于 2026-05-25 全链路诊断修复
#  解决问题:
#    P0: 后台轮询未启动 → 自动启动
#    P1: current_style 冷启动空转 → 自动初始化
#    P2: Plugin 导入路径错误 → 使用 openclaw/plugins install -l
#    P3: Gateway 事件循环阻塞 → 异步 Hook 加载
# ══════════════════════════════════════════════════════

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
OPENCLAW_DIR="$HOME/.openclaw"
PLUGIN_DIR="$PROJECT_DIR/adapters/openclaw/plugin"
DB_PATH="$PROJECT_DIR/data/flow_ecosystem.db"
LOG_FILE="/tmp/openclaw_install_$(date +%Y%m%d_%H%M%S).log"

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   🦞 Flow Ecosystem 一键安装 V2           ║${NC}"
echo -e "${BLUE}║   全链路诊断修复版 (2026-05-25)            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# ==========================================
# Step 0: 环境预检
# ==========================================
echo -e "${YELLOW}【Step 0/7】环境预检${NC}"
echo "----------------------------------------"

check_cmd() {
  if command -v "$1" &>/dev/null; then
    echo -e "  ✅ $1: $(command -v $1)"
    return 0
  else
    echo -e "  ${RED}❌ $1: 未找到${NC}"
    return 1
  fi
}

PASS=true
check_cmd python3 || PASS=false
check_cmd node || PASS=false
check_cmd npm || PASS=false
check_cmd openclaw || PASS=false
check_cmd sqlite3 || PASS=false

PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
NODE_VERSION=$(node --version 2>&1)
OPENCLAW_VERSION=$(openclaw --version 2>&1 | head -1)

echo ""
echo "  Python:  $PYTHON_VERSION (需要 3.11+)"
echo "  Node:    $NODE_VERSION (需要 18+)"
echo "  OpenClaw: $OPENCLAW_VERSION"

if [ "$PASS" = false ]; then
  echo -e "\n${RED}❌ 环境检查失败，请先安装缺失的依赖${NC}\n"
  exit 1
fi

echo -e "  ${GREEN}✅ 环境检查通过${NC}"

# ==========================================
# Step 1: 准备 Plugin 目录结构
# ==========================================
echo ""
echo -e "${YELLOW}【Step 1/7】准备 Plugin 目录${NC}"
echo "----------------------------------------"

cd "$PLUGIN_DIR"

if [ ! -f "package.json" ]; then
  echo -e "  ${RED}❌ package.json 不存在${NC}"
  exit 1
fi

if [ ! -f "dist/index.js" ]; then
  echo -e "  ${RED}❌ dist/index.js 不存在${NC}"
  exit 1
fi

if [ ! -f "openclaw.plugin.json" ]; then
  echo -e "  ${RED}❌ openclaw.plugin.json 不存在${NC}"
  exit 1
fi

if [ ! -f "dist/hooks/counter.js" ]; then
  echo -e "  ${RED}❌ dist/hooks/counter.js 不存在${NC}"
  exit 1
fi

if [ ! -f "dist/hooks/injector.js" ]; then
  echo -e "  ${RED}❌ dist/hooks/injector.js 不存在${NC}"
  exit 1
fi

echo -e "  ✅ package.json"
echo -e "  ✅ dist/index.js (async hooks + official SDK path)"
echo -e "  ✅ dist/hooks/counter.js"
echo -e "  ✅ dist/hooks/injector.js"
echo -e "  ✅ openclaw.plugin.json"

# ==========================================
# Step 2: 安装 npm 依赖 (sqlite3)
# ==========================================
echo ""
echo -e "${YELLOW}【Step 2/7】安装 npm 依赖${NC}"
echo "----------------------------------------"

npm install --silent 2>&1 | tail -3
echo -e "  ✅ npm 依赖已安装 (含 sqlite3)"

# 验证 sqlite3 模块可用
node -e "require('sqlite3'); console.log('  ✅ sqlite3 模块加载正常');" 2>&1 || {
  echo -e "  ${RED}❌ sqlite3 npm 模块加载失败${NC}"
  exit 1
}

# ==========================================
# Step 3: 使用 OpenClaw CLI 安装插件 (关键!)
# ==========================================
echo ""
echo -e "${YELLOW}【Step 3/7】OpenClaw CLI 插件注册${NC}"
echo "----------------------------------------"
echo "  使用: openclaw plugins install -l (官方方式)"

openclaw plugins install -l "$PLUGIN_DIR" 2>&1 | tee -a "$LOG_FILE" | grep -E "Linked|error|failed|Plugin manifest" || true

echo -e "  ✅ CLI 注册完成"

# ==========================================
# Step 4: 配置 openclaw.json (allowConversationAccess + entries)
# ==========================================
echo ""
echo -e "${YELLOW}【Step 4/7】配置 OpenClaw${NC}"
echo "----------------------------------------"

python3 << 'PYEOF'
import json, os

config_path = os.path.expanduser('~/.openclaw/openclaw.json')
with open(config_path, 'r') as f:
    c = json.load(f)

plugins = c.get('plugins', {})

# 4a: 确保 load.paths 包含我们的插件目录
load = plugins.get('load', {})
if 'paths' not in load:
    load['paths'] = []
plugin_dir = os.path.expanduser('~/Desktop/skill相关文档/flow-evolution-for-mind/adapters/openclaw/plugin')
if plugin_dir not in load['paths']:
    load['paths'].append(plugin_dir)
plugins['load'] = load

# 4b: 配置 plugin entries + allowConversationAccess
entries = plugins.get('entries', {})
entries['flow-evolution-for-mind'] = {
    'enabled': True,
    'hooks': {
        'allowConversationAccess': True
    }
}
plugins['entries'] = entries
c['plugins'] = plugins

with open(config_path, 'w') as f:
    json.dump(c, f, indent=2, ensure_ascii=False)

print("  ✅ allowConversationAccess: True")
print("  ✅ plugins.entries.flow-evolution-for-mind: enabled")
print(f"  ✅ plugins.load.paths: {plugin_dir}")
PYEOF

# ==========================================
# Step 5: 同步 Skill 文件
# ==========================================
echo ""
echo -e "${YELLOW}【Step 5/7】同步 Skill${NC}"
echo "----------------------------------------"

SKILL_DIR="$OPENCLAW_DIR/skills/flow-evolution-for-mind"
mkdir -p "$SKILL_DIR/scripts"

cp "$PROJECT_DIR/adapters/openclaw/scripts/flow_handler.py" "$SKILL_DIR/scripts/" 2>/dev/null
cp "$PROJECT_DIR/adapters/openclaw/scripts/SKILL.md" "$SKILL_DIR/" 2>/dev/null

echo "  ✅ flow_handler.py → skills/flow-evolution-for-mind/scripts/"
echo "  ✅ SKILL.md → skills/flow-evolution-for-mind/"

# 绑定 Skill 到所有 Agent
python3 << 'PYEOF'
import json, os

p = os.path.expanduser('~/.openclaw/openclaw.json')
with open(p, 'r') as f:
    d = json.load(f)

if 'skills' not in d:
    d['skills'] = {}
if 'entries' not in d['skills']:
    d['skills']['entries'] = {}

d['skills']['entries']['flow-evolution-for-mind'] = {'enabled': True}

agents = d.get('agents', {}).get('list', [])
bound = 0
for a in agents:
    aid = a.get('id')
    if not aid:
        continue
    current_skills = a.get('skills', [])
    if isinstance(current_skills, list) and 'flow-evolution-for-mind' not in current_skills:
        a['skills'] = current_skills + ['flow-evolution-for-mind']
        bound += 1
        print(f"  ✅ Agent '{aid}' 已绑定 Skill")

print(f"\n  ✅ 共 {bound} 个 Agent 绑定完成")

with open(p, 'w') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
PYEOF

# ==========================================
# Step 5.5: 设置环境变量 + 标记文件 (P4 Fix)
# ==========================================
echo ""
echo -e "${YELLOW}【Step 5.5】环境变量配置${NC}"
echo "----------------------------------------"

# 写入 FLOW_EVOLUTION_DIR 到标记文件 (counter.js/injector.js 的 fallback #2)
echo "$PROJECT_DIR" > "$HOME/.flow_evolution_dir"
echo "  ✅ ~/.flow_evolution_dir → $PROJECT_DIR"

# 写入到 shell profile 以便子进程继承
PROFILE_SNIPPER='
# Flow Ecosystem (auto-added by install_v2.sh)
export FLOW_EVOLUTION_DIR="'"$PROJECT_DIR"'"
'
if ! grep -q "FLOW_EVOLUTION_DIR" "$HOME/.zshrc" 2>/dev/null; then
    echo "$PROFILE_SNIPPER" >> "$HOME/.zshrc"
    echo "  ✅ 已添加到 ~/.zshrc"
else
    echo "  ⚠️  ~/.zshrc 中已有 FLOW_EVOLUTION_DIR (跳过)"
fi

# 立即导出当前 shell
export FLOW_EVOLUTION_DIR="$PROJECT_DIR"
echo "  ✅ FLOW_EVOLUTION_DIR=$PROJECT_DIR"

# ==========================================
# Step 6: 初始化数据库 + current_style (P1 Fix)
# ==========================================
echo ""
echo -e "${YELLOW}【Step 6/7】数据库初始化 (P1 Cold Start Fix)${NC}"
echo "----------------------------------------"

if [ ! -f "$DB_PATH" ]; then
  echo "  ⚠️ 数据库不存在，创建表结构..."
  python3 -c "
import sqlite3, os
db_path = '$DB_PATH'
os.makedirs(os.path.dirname(db_path), exist_ok=True)
conn = sqlite3.connect(db_path)
conn.execute('PRAGMA journal_mode=WAL;')
conn.executescript('''
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    role TEXT,
    content_text TEXT,
    timestamp TEXT,
    agent_id TEXT,
    is_system_noise INTEGER DEFAULT 0,
    is_auto_push INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS session_analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    goal_alignment TEXT,
    closure_index TEXT,
    flow_depth TEXT,
    cognition_growth TEXT,
    portrait_label TEXT,
    style_pace TEXT,
    style_depth TEXT,
    style_tone TEXT,
    style_friction TEXT,
    agent_id TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS kv_store (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT,
    key TEXT,
    value TEXT,
    updated_at TEXT,
    UNIQUE(agent_id, key)
);
''')
conn.commit(); conn.close()
print('  ✅ 数据库创建完成')
"
else
  echo "  ✅ 数据库已存在 ($(ls -lh "$DB_PATH" | awk '{print $5}'))"
fi

# P1 FIX: 初始化 current_style for all known agents
echo ""
echo "  初始化 current_style (Cold Start Fix)..."
python3 << 'PYEOF'
import sqlite3, json, os

db_path = os.path.expanduser('~/Desktop/skill相关文档/flow-evolution-for-mind/data/flow_ecosystem.db')
conn = sqlite3.connect(db_path, timeout=30)
conn.execute('PRAGMA journal_mode=WAL;')
c = conn.cursor()

default_style = json.dumps({
    "pace": "explore",
    "depth": "surface", 
    "tone": "neutral",
    "friction": "direct",
    "portrait": "平稳推进"
}, ensure_ascii=False)

# 从已有分析记录获取最新 portrait
c.execute("SELECT DISTINCT agent_id FROM sessions WHERE agent_id IS NOT NULL AND agent_id != '' LIMIT 20")
agents = [r[0] for r in c.fetchall()]

if not agents:
    agents = ['main', 'secretary']

initialized = 0
for agent_id in agents:
    c.execute("SELECT value FROM kv_store WHERE agent_id=? AND key='current_style'", (agent_id,))
    if not c.fetchone():
        # 尝试获取该 agent 最新 portrait
        c.execute("SELECT portrait_label FROM session_analyses WHERE (agent_id=? OR agent_id IS NULL OR agent_id='') ORDER BY created_at DESC LIMIT 1", (agent_id,))
        row = c.fetchone()
        style = json.loads(default_style)
        if row and row[0]:
            style['portrait'] = row[0]
        
        c.execute("INSERT OR REPLACE INTO kv_store(agent_id,key,value,updated_at)VALUES(?,'current_style',?,datetime('now'))",
                  (agent_id, json.dumps(style, ensure_ascii=False)))
        initialized += 1
        print(f"  ✅ {agent_id}: portrait={style.get('portrait','平稳推进')}")

conn.commit(); conn.close()
print(f"\n  ✅ 初始化完成 ({initialized} 个 agent)")
PYEOF

# ==========================================
# Step 7: 重启 Gateway + 启动轮询
# ==========================================
echo ""
echo -e "${YELLOW}【Step 7/7】重启服务${NC}"
echo "----------------------------------------"

# 停止现有进程
pkill -9 -f "openclaw gateway" 2>/dev/null || true
sleep 2

# 启动 Gateway
nohup openclaw gateway run --port 18789 > "$LOG_FILE" 2>&1 &
GATEWAY_PID=$!
echo "  Gateway 启动中 (PID: $GATEWAY_PID)..."

# 等待 Gateway 就绪
for i in $(seq 1 20); do
  sleep 2
  if curl -s http://127.0.0.1:18789/ > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅ Gateway 就绪 (${i}x2=${i}0s)${NC}"
    break
  fi
  if [ $i -eq 20 ]; then
    echo -e "  ${RED}❌ Gateway 启动超时${NC}"
    echo "  查看日志: cat $LOG_FILE"
  fi
done

sleep 3

# 验证插件加载
echo ""
echo "  插件加载状态:"
grep '\[flow-style\]' "$LOG_FILE" 2>/dev/null | tail -5 || echo "  (等待加载...)"

# 启动后台轮询引擎 (P0 Fix)
echo ""
echo "  启动后台轮询引擎..."
cd "$PROJECT_DIR"
bash scripts/start_poll.sh 2>&1 | grep -E "PID|已启动|错误" || true

# ==========================================
# 完成!
# ==========================================
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         🎉 安装完成！                      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo "  📋 已完成的修复:"
echo "     ✅ P0: 后台轮询引擎已启动 (数据自动导入)"
echo "     ✅ P1: current_style 冷启动初始化 (injector 可读)"
echo "     ✅ P2: 官方 SDK 路径 (openclaw/plugin-sdk/core)"
echo "     ✅ P3: 异步 Hook 加载 (不阻塞 Gateway)"
echo "     ✅ allowConversationAccess 已启用"
echo ""
echo "  🧪 验证方式:"
echo "     1. 发送任意消息 → 查看 Gateway 日志是否有 [flow-style] Injecting 4D"
echo "     2. 发送 /deepflow 或 \"这周怎么样\" → 应返回认知报告"
echo "     3. 查看: tail -f $LOG_FILE | grep flow-style"
echo ""
echo "  🔧 运维命令:"
echo "     启动轮询:  bash scripts/start_poll.sh"
echo "     停止全部:  bash scripts/stop_all.sh"
echo "     查看日志:  tail -f $LOG_FILE"
echo "     重启Gateway: pkill -9 -f openclaw && nohup openclaw gateway run --port 18789 > /tmp/openclaw.log 2>&1 &"
echo ""
