#!/bin/bash 
set -e 

echo "🦞 Flow Ecosystem 一键安装" 
echo "==========================" 

# ========================================== 
# 1. 路径定义 
# ========================================== 
OPENCLAW_DIR="$HOME/.openclaw" 
EXT_DIR="$OPENCLAW_DIR/extensions/flow-style-plugin" 
SKILL_DIR="$OPENCLAW_DIR/skills/flow-evolution-for-mind" 
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)" 

echo "" 
echo "【1/6】备份当前 OpenClaw 配置" 
echo "========================================" 
if [ -f "$OPENCLAW_DIR/openclaw.json" ]; then 
    cp "$OPENCLAW_DIR/openclaw.json" "$OPENCLAW_DIR/openclaw.json.flow.bak.$(date +%s)" 
    echo "✅ 配置已备份" 
else 
    echo "⚠️ 未找到现有配置，跳过备份" 
fi 

echo "" 
echo "【2/6】同步 Plugin 到 extensions" 
echo "========================================" 
mkdir -p "$EXT_DIR" 
cp -r "$PROJECT_DIR/adapters/openclaw/plugin/dist/"* "$EXT_DIR/" 2>/dev/null || true 
cp "$PROJECT_DIR/adapters/openclaw/plugin/openclaw.plugin.json" "$EXT_DIR/" 
echo "✅ Plugin 文件已同步" 

echo "" 
echo "【3/6】安装 Plugin 依赖 (sqlite3)" 
echo "========================================" 
cd "$EXT_DIR" 
npm install sqlite3 --silent 
echo "✅ sqlite3 已安装" 

echo "" 
echo "【4/6】同步 Skill 到 OpenClaw skills 目录" 
echo "========================================" 
mkdir -p "$SKILL_DIR/scripts" 
cp "$PROJECT_DIR/adapters/openclaw/scripts/flow_handler.py" "$SKILL_DIR/scripts/" 
cp "$PROJECT_DIR/adapters/openclaw/scripts/init.py" "$SKILL_DIR/scripts/" 
cp "$PROJECT_DIR/adapters/openclaw/scripts/SKILL.md" "$SKILL_DIR/" 2>/dev/null || echo "⚠️ 项目目录无 SKILL.md，使用现有" 
echo "✅ Skill 已同步" 

echo "" 
echo "【5/6】自动绑定 Skill 到所有 Agent" 
echo "========================================" 
python3 << 'PYEOF' 
import json, os, sys 
 
p = os.path.expanduser('~/.openclaw/openclaw.json') 
if not os.path.exists(p): 
    print("❌ 未找到 openclaw.json，请先安装并启动 OpenClaw") 
    sys.exit(1) 
 
with open(p, 'r') as f: 
    d = json.load(f) 
 
# 确保 skills.entries 里有 flow-evolution-for-mind 
if 'skills' not in d: 
    d['skills'] = {} 
if 'entries' not in d['skills']: 
    d['skills']['entries'] = {} 
 
d['skills']['entries']['flow-evolution-for-mind'] = {'enabled': True} 
 
# 给每个 Agent 绑定 Skill 
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
        print(f"  ✅ {aid} 已绑定") 
    elif not isinstance(current_skills, list): 
        a['skills'] = ['flow-evolution-for-mind'] 
        bound += 1 
        print(f"  ✅ {aid} 已绑定 (覆盖旧格式)") 
 
print(f"\n✅ 共 {bound} 个 Agent 已绑定 flow-evolution-for-mind") 
 
with open(p, 'w') as f: 
    json.dump(d, f, indent=2, ensure_ascii=False) 
 
PYEOF 
 
echo ""
echo "【5.5/6】清理遗留的 importer 进程（防止旧代码缓存）"
echo "========================================"
# 查找并终止所有 importer.watcher 进程
WATCHER_PIDS=$(ps aux | grep "importer.watcher" | grep -v grep | awk '{print $2}')
if [ -n "$WATCHER_PIDS" ]; then
    echo "发现遗留 watcher 进程: $WATCHER_PIDS"
    kill $WATCHER_PIDS 2>/dev/null
    sleep 2
    echo "✅ 已清理旧 watcher 进程"
else
    echo "✅ 无遗留 watcher 进程"
fi

echo ""
echo "【6/6】重启 Gateway"
echo "========================================" 
openclaw gateway restart 
sleep 8 
 
echo "" 
echo "==========================" 
echo "🎉 安装完成！" 
echo "" 
echo "验证方式：" 
echo "  1. 在飞书对任意 Agent 发 /flow" 
echo "  2. 或执行: openclaw gateway status | grep Runtime" 
echo "" 
echo "如果 /flow 无响应，检查日志:" 
echo "  tail -f /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log | grep -i flow" 
echo "=========================="