#!/bin/bash
# ════════════════════════════════════════════════════
#  补充: 重新注册 Plugin + 验证全链路
#  用途: fix_skill_structure.sh 之后执行，恢复插件注册
# ════════════════════════════════════════════════════

set -e

PLUGIN_DIR="$HOME/Desktop/skill相关文档/flow-evolution-for-mind/adapters/openclaw/plugin"

echo "========================================"
echo "  补充: 重新注册 Plugin"
echo "========================================"
echo ""

echo "--- Step 1: CLI 注册 ---"
openclaw plugins install -l "$PLUGIN_DIR" 2>&1 | grep -E "Linked|error|failed|manifest" || true

echo ""
echo "--- Step 2: 重启 Gateway ---"
pkill -9 -f "openclaw gateway" 2>/dev/null || true
sleep 2
nohup openclaw gateway run --port 18789 > /tmp/openclaw_plugin_rereg.log 2>&1 &
echo "PID: $!"

for i in $(seq 1 15); do
  sleep 2
  if curl -s http://127.0.0.1:18789/ > /dev/null 2>&1; then
    echo "✅ Gateway 就绪 ($((i*2))s)"
    break
  fi
done

sleep 3
echo ""

echo "--- Step 3: 验证插件加载 ---"
echo "插件列表中是否有 flow-evolution-for-mind:"
/usr/local/bin/openclaw plugins list 2>&1 | grep -E "flow-evolution" && echo "✅ 插件在列表中!" || echo "❌ 插件不在列表!"

echo ""
echo "[flow-style] 日志:"
grep '\[flow-style\]' /tmp/openclaw_plugin_rereg.log | tail -5 || echo "(无)"

echo ""
echo "--- Step 4: 响应时间 ---"
time curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" http://127.0.0.1:18789/

echo ""
echo "--- Step 5: SKILL.md 确认 ---"
head -1 "$HOME/.openclaw/skills/flow-evolution-for-mind/SKILL.md"

echo ""
echo "========================================"
echo "  完成！请在飞书测试:"
echo "========================================"
echo "  情报官 → /flow"
echo "  产品总监 → 这周怎么样"
echo "  技术总监 → /deepflow"
