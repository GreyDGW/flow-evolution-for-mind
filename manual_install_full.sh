#!/bin/bash
echo "=== 安装完整版 Plugin ==="
cp ~/Desktop/skill相关文档/flow-evolution-for-mind/adapters/openclaw/plugin/dist/index.js ~/.openclaw/extensions/flow-style-plugin/dist/index.js
echo "✅ 已复制完整版 index.js"
echo "重启 Gateway..."
pkill -f "openclaw.*gateway"
sleep 2
openclaw gateway run --port 18789 &
sleep 5
echo ""
echo "=== 验证 ==="
/usr/local/bin/openclaw plugins list 2>&1 | grep -A2 "flow-evolution"
