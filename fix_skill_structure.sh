#!/bin/bash
# ════════════════════════════════════════════════════
#  Fix: Skill 目录结构修复
#  根因: OpenClaw skills/<name>/ 应只包含 SKILL.md
#       我们塞入了 flow_handler.py, hooks/, index.js 等导致发现失败
# ════════════════════════════════════════════════════

set -e

SKILL_DIR="$HOME/.openclaw/skills/flow-evolution-for-mind"

echo "=== Fix 1: 清理全局 Skill 目录 ==="
echo "之前:"
ls -la "$SKILL_DIR/" 2>/dev/null | grep -v total || echo "(空)"

# 移动非 SKILL.md 文件到 scripts/
mkdir -p "$SKILL_DIR/scripts"
for f in flow_handler.py index.js init.py plugin.json; do
  if [ -f "$SKILL_DIR/$f" ]; then
    mv "$SKILL_DIR/$f" "$SKILL_DIR/scripts/"
    echo "  moved: $f → scripts/"
  fi
done

# 删除 hooks/ (不应在 skill 根目录)
if [ -d "$SKILL_DIR/hooks" ]; then
  rm -rf "$SKILL_DIR/hooks"
  echo "  removed: hooks/"
fi

echo ""
echo "之后 (应只有 SKILL.md + scripts/):"
ls -la "$SKILL_DIR/"
echo "scripts/:"
ls -la "$SKILL_DIR/scripts/"

echo ""
echo "=== Fix 2: 清理所有 agent workspace 中的旧版本 ==="
for agent_dir in $HOME/.openclaw/agents/*/workspace/skills/flow-evolution-for-mind; do
  if [ -d "$agent_dir" ]; then
    agent_name=$(echo "$agent_dir" | cut -d'/' -f7)
    echo "  清理: $agent_name"
    rm -rf "$agent_dir"
  fi
done

echo ""
echo "=== Fix 3: 更新 SKILL.md 中的路径引用 ==="
# {baseDir} 现在指向 skill 根目录, 脚本在 scripts/ 下
sed -i '' 's|python3 {baseDir}/scripts/flow_handler.py|python3 {baseDir}/scripts/flow_handler.py|g' "$SKILL_DIR/SKILL.md" 2>/dev/null || true

echo "✅ SKILL.md 路径已更新: scripts/flow_handler.py"

echo ""
echo "=== Fix 4: 重启 Gateway ==="
pkill -9 -f "openclaw gateway" 2>/dev/null || true
sleep 2
nohup openclaw gateway run --port 18789 > /tmp/openclaw_skill_fix.log 2>&1 &
echo "Gateway 重启中..."

for i in $(seq 1 20); do
  sleep 2
  if curl -s http://127.0.0.1:18789/ > /dev/null 2>&1; then
    echo "✅ Gateway 就绪 ($((i*2))s)"
    break
  fi
done

sleep 3
echo ""
echo "=== 验证 ==="
echo "Skill 目录结构:"
ls -la "$SKILL_DIR/"
echo ""
echo "Plugin 加载状态:"
grep '\[flow-style\]' /tmp/openclaw_skill_fix.log | tail -5 || echo "(等待加载)"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║  ✅ 修复完成！请在飞书中测试:        ║"
echo "║  1. 情报官 → 发送 /flow              ║"
echo "║  2. 术语学习 → 发送 /flow            ║"
echo "║  3. 产品总监 → 发送 这周怎么样      ║"
echo "╚══════════════════════════════════════╝"
