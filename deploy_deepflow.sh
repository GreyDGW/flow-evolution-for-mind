#!/bin/bash
set +e

echo "========================================"
echo "  DeepFlow 拦截器部署"
echo "========================================"

PROJECT="$HOME/Desktop/skill相关文档/flow-evolution-for-mind"

# 同步最新的 index.js (含 DeepFlow 拦截器)
echo ""
echo "[1/3] 同步 index.js..."
cp -f "$PROJECT/adapters/openclaw/plugin/dist/index.js" \
   "$PROJECT/adapters/openclaw/plugin/dist/index.js"
echo "  OK"

# 验证 DeepFlow 拦截器代码存在
echo ""
echo "[2/3] 验证拦截器..."
grep -c "registerDeepFlowInterceptor" "$PROJECT/adapters/openclaw/plugin/dist/index.js" && echo "  DeepFlow interceptor: PRESENT" || echo "  MISSING!"
grep -c "execFileSync" "$PROJECT/adapters/openclaw/plugin/dist/index.js" && echo "  execFileSync: PRESENT" || echo "  MISSING!"

# 重启 Gateway
echo ""
echo "[3/3] 重启 Gateway..."
openclaw gateway restart 2>/dev/null || {
  pkill -9 -f "openclaw gateway" 2>/dev/null || true
  sleep 2
  nohup openclaw gateway run --port 18789 > /tmp/openclaw_deepflow.log 2>&1 &
}
sleep 15
curl -s http://127.0.0.1:18789/ > /dev/null 2>&1 && echo "  Gateway ready" || echo "  Gateway not responding"

# 验证
echo ""
echo "=== 验证 ==="
grep '\[flow-style\]' /tmp/openclaw_deepflow.log 2>/dev/null | tail -5 || grep '\[flow-style\]' ~/Library/Logs/openclaw/gateway.log | tail -5 || echo "(checking...)"

echo ""
echo "========================================"
echo "  DONE - 请测试:"
echo "========================================"
echo "  任意 Agent -> /deepflow"
echo "  任意 Agent -> /deepflow 4月20日"
echo "  任意 Agent -> 这周怎么样"
