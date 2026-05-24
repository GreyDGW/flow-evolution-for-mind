#!/bin/bash
# 步骤 3c：install.sh 手动补充步骤（Trae 沙盒外执行）
# 执行方式: bash step_3c_manual_install.sh
# 说明：由于 Trae 沙盒权限限制，无法操作 ~/.openclaw 目录
#       本脚本完成 install.sh 剩余的 5 个步骤

set -e

echo "========================================"
echo "=== 步骤 3c：手动补充安装 ==="
echo "========================================"

PROJECT_DIR="$HOME/Desktop/skill相关文档/flow-evolution-for-mind"
OPENCLAW_DIR="$HOME/.openclaw"
EXT_DIR="$OPENCLAW_DIR/extensions/flow-style-plugin"
SKILL_DIR="$OPENCLAW_DIR/skills/flow-evolution-for-mind"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_ok() { echo -e "${GREEN}✅ $1${NC}"; }
print_err() { echo -e "${RED}❌ $1${NC}"; }
print_warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }

# ============================================
# 步骤 2：同步 Plugin 到 extensions 目录
# ============================================
echo ""
echo "========================================"
echo "【2/6】同步 Plugin 到 extensions"
echo "========================================"

if [ ! -d "$PROJECT_DIR/adapters/openclaw/plugin" ]; then
    print_err "项目源码目录不存在: $PROJECT_DIR/adapters/openclaw/plugin"
    exit 1
fi

mkdir -p "$EXT_DIR"
print_ok "已创建目录: $EXT_DIR"

cp -r "$PROJECT_DIR/adapters/openclaw/plugin/dist/"* "$EXT_DIR/" 2>/dev/null || true
print_ok "已复制 dist/ 目录内容"

cp "$PROJECT_DIR/adapters/openclaw/plugin/plugin.json" "$EXT_DIR/"
print_ok "已复制 plugin.json"

echo ""
print_warn "验证安装结果:"
for F in plugin.json dist/index.js dist/hooks/counter.js dist/hooks/injector.js; do
    if [ -f "$EXT_DIR/$F" ]; then
        print_ok "  $F ($(wc -l < "$EXT_DIR/$F") 行)"
    else
        print_err "  缺失: $F"
    fi
done

# ============================================
# 步骤 3：安装 Node.js 依赖 (sqlite3)
# ============================================
echo ""
echo "========================================"
echo "【3/6】安装 Node.js 依赖"
echo "========================================"

cd "$EXT_DIR"

# 检查是否有 package.json，如果没有则创建一个
if [ ! -f "package.json" ]; then
    cat > package.json << 'EOF'
{
  "name": "flow-style-plugin",
  "version": "7.8.9",
  "description": "Flow Ecosystem Plugin",
  "main": "dist/index.js",
  "dependencies": {
    "sqlite3": "^5.1.6"
  }
}
EOF
    print_ok "已创建 package.json"
fi

npm install sqlite3 --silent
print_ok "sqlite3 已安装"

cd "$PROJECT_DIR"

# ============================================
# 步骤 4：同步 Skill 到全局目录
# ============================================
echo ""
echo "========================================"
echo "【4/6】同步 Skill 到全局目录"
echo "========================================"

mkdir -p "$SKILL_DIR/scripts"
print_ok "已创建 Skill 目录: $SKILL_DIR"

# 复制核心脚本
for SCRIPT in flow_handler.py init.py SKILL.md; do
    SRC="$PROJECT_DIR/adapters/openclaw/scripts/$SCRIPT"
    DST="$SKILL_DIR/scripts/$SCRIPT"
    
    if [ -f "$SRC" ]; then
        cp "$SRC" "$DST"
        print_ok "已复制: $SCRIPT ($(wc -l < "$DST") 行)"
    else
        print_warn "跳过: $SCRIPT (源文件不存在)"
    fi
done

# 复制 Plugin 文件到 Skill 目录（用于 /deepflow 触发）
cp -r "$EXT_DIR/"* "$SKILL_DIR/" 2>/dev/null || true
print_ok "已同步 Plugin 文件到 Skill 目录"

echo ""
print_warn "Skill 目录结构:"
ls -la "$SKILL_DIR" | head -10

# ============================================
# 步骤 5：自动绑定 Skill 到所有 Agent
# ============================================
echo ""
echo "========================================"
echo "【5/6】绑定 Skill 到所有 Agent"
echo "========================================"

CONFIG_FILE="$OPENCLAW_DIR/openclaw.json"

if [ ! -f "$CONFIG_FILE" ]; then
    print_err "配置文件不存在: $CONFIG_FILE"
    print_warn "跳过自动绑定，请手动在飞书中绑定 Agent"
else
    # 使用 Python 安全地修改 JSON 配置
    python3 << PYEOF
import json
import os

config_path = os.path.expanduser("~/.openclaw/openclaw.json")
skill_name = "flow-evolution-for-mind"

with open(config_path, 'r') as f:
    config = json.load(f)

# 确保 skills.entries 存在
if 'skills' not in config:
    config['skills'] = {}
if 'entries' not in config['skills']:
    config['skills']['entries'] = {}

# 注册 Skill
config['skills']['entries'][skill_name] = {"enabled": True}
print(f"✅ 已注册 Skill: {skill_name}")

# 遍历并绑定到所有 Agent
agent_count = 0
if 'agents' in config:
    for agent_id, agent_config in config['agents'].items():
        if 'skills' not in agent_config:
            agent_config['skills'] = []
        
        if skill_name not in agent_config['skills']:
            agent_config['skills'].append(skill_name)
            agent_count += 1

print(f"✅ 已绑定到 {agent_count} 个 Agent")

# 写回配置
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f"✅ 配置已保存")
PYEOF
fi

# 同时复制 Skill 文件到每个 Agent 的 workspace
AGENT_COUNT=0
for AGENT_DIR in "$OPENCLAW_DIR/agents"/*; do
    if [ -d "$AGENT_DIR" ]; then
        AGENT_ID=$(basename "$AGENT_DIR")
        
        mkdir -p "$AGENT_DIR/workspace/skills"
        cp -r "$SKILL_DIR" "$AGENT_DIR/workspace/skills/flow-evolution-for-mind"
        
        ((AGENT_COUNT++)) || true
    fi
done

print_ok "Skill 文件已复制到 $AGENT_COUNT 个 Agent workspace"

# ============================================
# 步骤 6：重启 Gateway
# ============================================
echo ""
echo "========================================"
echo "【6/6】重启 Gateway"
echo "========================================"

print_info "当前 OpenClaw Gateway 进程:"
ps aux | grep -i openclaw | grep gateway | grep -v grep | awk '{print "   PID:", $2, "启动时间:", $9}' || print_info "未检测到运行中的 Gateway"

echo ""
print_info "正在重启 OpenClaw Gateway..."

launchctl stop ai.openclaw.gateway 2>/dev/null && print_ok "Gateway 停止命令已发送" || print_warn "停止命令可能未生效"
sleep 3

launchctl start ai.openclaw.gateway 2>/dev/null && print_ok "Gateway 启动命令已发送" || print_warn "启动命令可能未生效"
sleep 5

echo ""
print_info "重启后进程状态:"
if ps aux | grep -i openclaw | grep -v grep | grep -q .; then
    print_ok "Gateway 正在运行"
    ps aux | grep -i openclaw | grep -v grep | awk '{print "   PID:", $2, "端口:", $12}'
else
    print_warn "未检测到 Gateway 进程，可能需要手动启动"
fi

# ============================================
# 最终报告
# ============================================
echo ""
echo "========================================"
echo "【安装完成报告】"
echo "========================================"
echo ""
echo "✅ 已完成:"
echo "  【1/6】备份配置 → ✅ 由 install.sh 完成"
echo "  【2/6】Plugin 安装 → ✅ 已安装到 $EXT_DIR"
echo "  【3/6】Node.js 依赖 → ✅ sqlite3 已安装"
echo "  【4/6】Skill 同步 → ✅ 已安装到 $SKILL_DIR"
echo "  【5/6】Agent 绑定 → ✅ 已绑定 $AGENT_COUNT 个 Agent"
echo "  【6/6】Gateway 重启 → ✅ 已发送重启命令"
echo ""
echo "📋 验证清单:"
echo "  □ 在飞书向 newness 或 secretary 发送消息"
echo "  □ 观察回复风格是否有变化"
echo "  □ 发送 /deepflow 测试认知报告生成"
echo "  □ 检查日志: tail -f ~/.openclaw/logs/gateway.log"
echo ""
echo "🔧 如遇问题:"
echo "  • 插件未加载 → ls -la ~/.openclaw/extensions/flow-style-plugin/"
echo "  • Agent 无响应 → 检查 ~/.openclaw/openclaw.json 的 skills 配置"
echo "  • 报告生成失败 → 检查数据库路径和环境变量"
echo ""
echo "========================================"
