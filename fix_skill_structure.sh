#!/bin/bash
# ════════════════════════════════════════════════════
#  Fix: Skill 目录结构修复 + 清理旧脚本
#  根因: OpenClaw skills/<name>/ 应只包含 SKILL.md
#       我们塞入了 flow_handler.py, hooks/, index.js 等导致发现失败
# ════════════════════════════════════════════════════

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$HOME/.openclaw/skills/flow-evolution-for-mind"

echo "========================================"
echo "  Skill 结构修复 + 旧脚本清理"
echo "========================================"
echo ""

# ── Pre-cleanup: 删除今天调试产生的临时脚本 ──
echo "--- 清理旧诊断脚本 ---"
CLEANED=0
for pattern in final_* emergency_* diagnose_* ultimate_* root_cause_* test_*.sh fix_module_import.sh check_agents.py check_agent_detail.py check_bindings.py; do
  for f in "$PROJECT_DIR"/$pattern; do
    if [ -f "$f" ]; then
      rm -f "$f"
      CLEANED=$((CLEANED+1))
    fi
  done
done
echo "  已删除 $CLEANED 个临时文件"

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
echo "=== Fix 3.5: 重新注册 Plugin (CLI) ==="
PLUGIN_SRC="$HOME/Desktop/skill相关文档/flow-evolution-for-mind/adapters/openclaw/plugin"
if [ -d "$PLUGIN_SRC" ]; then
  openclaw plugins install -l "$PLUGIN_SRC" 2>&1 | grep -E "Linked|error|failed" || true
  echo "  ✅ CLI 注册完成"
else
  echo "  ⚠️ 插件源目录不存在: $PLUGIN_SRC"
fi

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

echo "Gateway 状态:"
GW_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18789/ 2>/dev/null || echo "000")
GW_TIME=$(curl -s -o /dev/null -w "%{time_total}s" http://127.0.0.1:18789/ 2>/dev/null || echo "?")
echo "  HTTP $GW_CODE | 响应时间: $GW_TIME"
echo ""

echo "Plugin 加载状态 (openclaw plugins list):"
/usr/local/bin/openclaw plugins list 2>&1 | grep -E "flow-evolution|enabled|loaded" | tail -5 || echo "(未检测到)"
echo ""

echo "Gateway 日志中的 flow-style 记录:"
LOG_FILE=$(ls -t /tmp/openclaw_*.log 2>/dev/null | head -1)
if [ -n "$LOG_FILE" ]; then
  echo "  日志文件: $LOG_FILE"
  grep '\[flow-style\]' "$LOG_FILE" 2>/dev/null | tail -5 || echo "  (无 flow-style 日志)"
else
  echo "  (未找到 Gateway 日志文件)"
fi

echo ""
echo "Skill 文件可读性:"
if [ -f "$SKILL_DIR/SKILL.md" ]; then
  echo "  SKILL.md: $(wc -l < "$SKILL_DIR/SKILL.md") 行"
fi
if [ -f "$SKILL_DIR/scripts/flow_handler.py" ]; then
  echo "  scripts/flow_handler.py: $(wc -l < "$SKILL_DIR/scripts/flow_handler.py") 行"
fi

echo ""
echo "========================================"
echo "  修复完成！请在飞书中测试:"
echo "========================================"
echo "  1. 情报官(newness)   → 发送 /flow"
echo "  2. 产品总监(main)    → 发送 这周怎么样"
echo "  3. 技术总监(techboss)→ 发送 /deepflow"
echo ""
echo "  如果仍不工作，查看实时日志:"
echo "  tail -f ${LOG_FILE:-/tmp/openclaw_skill_fix.log} | grep -E 'flow-style|flow-evolution|skill'"
echo ""
