#!/bin/bash
set +e

echo "========================================"
echo "  FINAL FIX: 全链路彻底修复"
echo "========================================"

PROJECT="$HOME/Desktop/skill相关文档/flow-evolution-for-mind"

# ==========================================
# Phase 1: 清理旧 Skill 残留
# ==========================================
echo ""
echo "[Phase 1] 清理 Agent workspace 中的旧 Skill..."
CLEANED=0
for agent_dir in $HOME/.openclaw/agents/*/workspace/skills; do
  for old_skill in "$agent_dir"/flow "$agent_dir"/flow-state; do
    if [ -d "$old_skill" ]; then
      agent_name=$(echo "$agent_dir" | cut -d'/' -f7)
      echo "  删除: $agent_name/skills/$(basename $old_skill)"
      rm -rf "$old_skill"
      CLEANED=$((CLEANED+1))
    fi
  done
done
echo "  已清理 $CLEANED 个旧 Skill 目录"

# ==========================================
# Phase 2: 环境变量 + 标记文件
# ==========================================
echo ""
echo "[Phase 2] 环境变量配置..."
echo "$PROJECT" > "$HOME/.flow_evolution_dir"
export FLOW_EVOLUTION_DIR="$PROJECT"
echo "  ~/.flow_evolution_dir = $PROJECT"

# ==========================================
# Phase 3: 同步最新代码到部署目录
# ==========================================
echo ""
echo "[Phase 3] 同步最新代码..."
cp -f "$PROJECT/adapters/openclaw/scripts/SKILL.md" \
   "$HOME/.openclaw/skills/flow-evolution-for-mind/SKILL.md" 2>/dev/null
echo "  SKILL.md synced (Available to ALL agents)"

# ==========================================
# Phase 4: 通过 OpenClaw CLI 重启 Gateway
# ==========================================
echo ""
echo "[Phase 4] 重启 Gateway..."

# 方法1: 使用 openclaw CLI 重启 (如果支持)
if openclaw gateway restart 2>/dev/null; then
  echo "  CLI restart 成功"
else
  # 方法2: kill + 等待 launchd 自动重启
  echo "  尝试 pkill + launchd 自动重启..."
  
  # 先尝试找到并停止 launchd 服务
  LAUNCHD_PLIST=$(find ~/Library/LaunchAgents -name "*openclaw*" 2>/dev/null | head -1)
  if [ -n "$LAUNCHD_PLIST" ]; then
    launchctl unload "$LAUNCHD_PLIST" 2>/dev/null || true
    sleep 2
    launchctl load "$LAUNCHD_PLIST" 2>/dev/null || true
    echo "  launchd reload: done ($LAUNCHD_PLIST)"
  else
    # 方法3: 强制杀掉所有 openclaw 进程让 launchd 重启
    pkill -9 -f "openclaw" 2>/dev/null || true
    echo "  已 kill 所有 openclaw 进程，等待 launchd 重启..."
  fi
fi

# 等待 Gateway 就绪 (最长 60 秒)
READY=0
for i in $(seq 1 30); do
  sleep 2
  if curl -s http://127.0.0.1:18789/ > /dev/null 2>&1; then
    READY=1
    echo "  Gateway 就绪 (${i}x2=${i}0s)"
    break
  fi
done

if [ "$READY" = "0" ]; then
  echo "  ⚠️  Gateway 未自动启动，手动启动..."
  nohup openclaw gateway run --port 18789 > /tmp/openclaw_final_fix.log 2>&1 &
  sleep 20
fi

# ==========================================
# Phase 5: 重新注册插件 (Gateway 重启后)
# ==========================================
echo ""
echo "[Phase 5] 注册插件..."
sleep 3
openclaw plugins install -l "$PROJECT/adapters/openclaw/plugin" 2>&1 | grep -E "Linked|error|failed|manifest" || true

# ==========================================
# Phase 6: 重启轮询引擎
# ==========================================
echo ""
echo "[Phase 6] 轮询引擎..."
pkill -f "incremental\|run_async_collector" 2>/dev/null || true
sleep 1
cd "$PROJECT"
bash scripts/start_poll.sh 2>&1 | tail -3

# ==========================================
# Phase 7: 最终验证
# ==========================================
sleep 5
echo ""
echo "[Phase 7] 验证"
echo "----------------------------------------"

echo "1. 标记文件:"
cat "$HOME/.flow_evolution_dir"

echo ""
echo "2. 插件列表:"
/usr/local/bin/openclaw plugins list 2>&1 | grep -E "flow-evolution" && echo "  IN LIST!" || echo "  NOT IN LIST!"

echo ""
echo "3. 最新 Gateway 日志中的 flow-style:"
# 检查最新的 gateway 日志
LATEST_LOG=$(ls -t ~/Library/Logs/openclaw/gateway.log /tmp/openclaw_*.log 2>/dev/null | head -1)
if [ -n "$LATEST_LOG" ]; then
  echo "  日志文件: $LATEST_LOG"
  grep "\[flow-style\]" "$LATEST_LOG" | tail -5 || echo "  (无 flow-style 日志)"
else
  echo "  (未找到日志文件)"
fi

echo ""
echo "4. 响应时间:"
curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" http://127.0.0.1:18789/

echo ""
echo "5. 旧 Skill 残留检查:"
REMAINING=$(find $HOME/.openclaw/agents/*/workspace/skills/flow -maxdepth 0 -type d 2>/dev/null | wc -l)
if [ "$REMAINING" -gt 0 ]; then
  echo "  ⚠️  还有 $REMAINING 个旧 flow skill 目录!"
  find $HOME/.openclaw/agents/*/workspace/skills/flow -maxdepth 0 -type d 2>/dev/null
else
  echo "  ✅ 全部清理完毕"
fi

echo ""
echo "========================================"
echo "  FINAL FIX 完成"
echo "========================================"
echo ""
echo "  请在飞书测试 (这次应该是全新的 Gateway):"
echo "    情报官   -> /flow"
echo "    产品总监 -> 这周怎么样"
echo "    技术总监 -> /deepflow"
echo "    术语学习 -> /flow"
echo ""
echo "  如果仍不工作，查看实时日志:"
echo "    tail -f $LATEST_LOG | grep flow-style"
