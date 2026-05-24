#!/bin/bash
# Flow Ecosystem Plugin - 完整卸载重装脚本
# 执行方式: bash reinstall_plugin.sh

set -e  # 遇到错误立即退出

echo "========================================"
echo "=== Flow Ecosystem Plugin 重装工具 ==="
echo "========================================"
echo ""

PROJECT_DIR="$HOME/Desktop/skill相关文档/flow-evolution-for-mind"
OPENCLAW_DIR="$HOME/.openclaw"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# ============================================
# 第 1 步：彻底卸载所有残留
# ============================================
echo ""
echo "========================================"
echo "=== 第 1 步：彻底卸载所有残留 ==="
echo "========================================"

# 1.1 删除全局 plugins 目录下的旧备份
if [ -d "$OPENCLAW_DIR/plugins/flow-style-plugin.bak" ]; then
    rm -rf "$OPENCLAW_DIR/plugins/flow-style-plugin.bak"
    print_status "已删除旧备份: flow-style-plugin.bak"
else
    print_info "无旧备份需要清理"
fi

# 1.2 删除全局 skills 目录下的当前 Skill
if [ -d "$OPENCLAW_DIR/skills/flow-evolution-for-mind" ]; then
    rm -rf "$OPENCLAW_DIR/skills/flow-evolution-for-mind"
    print_status "已删除全局 Skill: flow-evolution-for-mind"
else
    print_info "全局 Skills 目录干净"
fi

# 1.3 删除所有 Agent workspace 中的旧挂载
AGENT_COUNT=0
for AGENT_DIR in "$OPENCLAW_DIR/agents"/*; do
    if [ -d "$AGENT_DIR" ]; then
        AGENT_ID=$(basename "$AGENT_DIR")
        CLEANED=false
        
        # 删除各种可能的残留目录
        for DIR_NAME in flow-evolution-for-mind flow flow-state flowguard-for-cron; do
            if [ -d "$AGENT_DIR/workspace/skills/$DIR_NAME" ]; then
                rm -rf "$AGENT_DIR/workspace/skills/$DIR_NAME"
                print_status "$AGENT_ID: 已删除 $DIR_NAME"
                CLEANED=true
            fi
        done
        
        # 清理 workspace/plugins 残留
        if [ -d "$AGENT_DIR/workspace/plugins" ]; then
            rm -rf "$AGENT_DIR/workspace/plugins/flow-evolution-for-mind" 2>/dev/null || true
            rm -rf "$AGENT_DIR/workspace/plugins/flow-style-plugin" 2>/dev/null || true
            if [ $? -eq 0 ]; then
                print_status "$AGENT_ID: 已清理 workspace/plugins"
                CLEANED=true
            fi
        fi
        
        if [ "$CLEANED" = true ]; then
            ((AGENT_COUNT++)) || true
        fi
    fi
done

if [ $AGENT_COUNT -gt 0 ]; then
    print_status "共清理了 $AGENT_COUNT 个 Agent 的残留"
else
    print_info "所有 Agent workspace 已是干净状态"
fi

# ============================================
# 第 2 步：验证项目源码完整性
# ============================================
echo ""
echo "========================================"
echo "=== 第 2 步：验证项目源码完整性 ==="
echo "========================================"

PLUGIN_SRC="$PROJECT_DIR/adapters/openclaw/plugin"
REQUIRED_FILES=(
    "plugin.json"
    "dist/index.js"
    "dist/hooks/counter.js"
    "dist/hooks/injector.js"
    "dist/soul-protocols/zh-CN/portraits.json"
)

MISSING_FILES=()
for FILE in "${REQUIRED_FILES[@]}"; do
    FULL_PATH="$PLUGIN_SRC/$FILE"
    if [ -f "$FULL_PATH" ]; then
        LINES=$(wc -l < "$FULL_PATH" 2>/dev/null || echo 0)
        if [ "$LINES" -gt 0 ]; then
            print_status "$FILE ($LINES 行)"
        else
            print_warning "$FILE 存在但为空文件"
            MISSING_FILES+=("$FILE")
        fi
    else
        print_error "缺失: $FILE"
        MISSING_FILES+=("$FILE")
    fi
done

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    print_error "发现 ${#MISSING_FILES[@]} 个缺失/空文件，请先在项目中补全！"
    exit 1
fi

# ============================================
# 第 3 步：重新安装 Plugin 到全局目录
# ============================================
echo ""
echo "========================================"
echo "=== 第 3 步：重新安装 Plugin ==="
echo "========================================"

PLUGIN_TARGET="$OPENCLAW_DIR/plugins/flow-evolution-for-mind"

# 创建目标目录
mkdir -p "$PLUGIN_TARGET"

# 复制插件文件
cp -r "$PLUGIN_SRC/"* "$PLUGIN_TARGET/"
print_status "Plugin 已安装到: $PLUGIN_TARGET"

# 验证安装结果
echo ""
echo "--- 安装结果验证 ---"
INSTALL_OK=true
for FILE in "${REQUIRED_FILES[@]}"; do
    if [ -f "$PLUGIN_TARGET/$FILE" ]; then
        LINES=$(wc -l < "$PLUGIN_TARGET/$FILE" 2>/dev/null || echo "?")
        print_status "$FILE ($LINES 行)"
    else
        print_error "安装失败: $FILE"
        INSTALL_OK=false
    fi
done

if [ "$INSTALL_OK" = false ]; then
    print_error "Plugin 安装不完整！"
    exit 1
fi

# ============================================
# 第 4 步：绑定到所有 Agent
# ============================================
echo ""
echo "========================================"
echo "=== 第 4 步：绑定到所有 Agent ==="
echo "========================================"

BOUND_AGENTS=0
for AGENT_DIR in "$OPENCLAW_DIR/agents"/*; do
    if [ -d "$AGENT_DIR" ]; then
        AGENT_ID=$(basename "$AGENT_DIR")
        
        # 创建 skills 目录（如果不存在）
        mkdir -p "$AGENT_DIR/workspace/skills"
        
        # 复制 Skill 到 Agent
        cp -r "$PLUGIN_TARGET" "$AGENT_DIR/workspace/skills/flow-evolution-for-mind"
        print_status "$AGENT_ID: Skill 已挂载"
        ((BOUND_AGENTS++)) || true
    fi
done

print_status "已绑定到 $BOUND_AGENTS 个 Agent"

# ============================================
# 第 5 步：重启 Gateway 加载新插件
# ============================================
echo ""
echo "========================================"
echo "=== 第 5 步：重启 Gateway ==="
echo "========================================"

print_info "当前 OpenClaw Gateway 进程:"
ps aux | grep -i openclaw | grep gateway | grep -v grep | awk '{print "   PID:", $2, "启动时间:", $9}' || print_info "未检测到运行中的 Gateway"

echo ""
print_info "正在重启 OpenClaw Gateway..."

# 尝试停止 Gateway
if launchctl stop ai.openclaw.gateway 2>/dev/null; then
    print_status "Gateway 停止命令已发送"
else
    print_warning "停止命令可能未生效（可能服务名不同）"
fi

# 等待进程完全退出
sleep 3

# 尝试启动 Gateway
if launchctl start ai.openclaw.gateway 2>/dev/null; then
    print_status "Gateway 启动命令已发送"
else
    print_warning "启动命令可能未生效（可能服务名不同）"
fi

# 等待启动完成
sleep 5

# 验证重启结果
echo ""
print_info "重启后进程状态:"
if ps aux | grep -i openclaw | grep -v grep | grep -q .; then
    print_status "Gateway 正在运行"
    ps aux | grep -i openclaw | grep -v grep | awk '{print "   PID:", $2, "端口:", $12}'
else
    print_warning "未检测到 Gateway 进程，可能需要手动启动"
fi

# ============================================
# 最终报告
# ============================================
echo ""
echo "========================================"
echo "【重装完成报告】"
echo "========================================"
echo ""
echo "✅ 已完成:"
echo "  1. 彻底清理所有旧版本残留"
echo "  2. 验证项目源码完整性（5个核心文件）"
echo "  3. 安装 Plugin 到全局目录"
echo "  4. 绑定到 $BOUND_AGENTS 个 Agent"
echo "  5. 重启 Gateway 加载新插件"
echo ""
echo "📋 验证清单:"
echo "  □ 在飞书向 newness 或 secretary 发送消息"
echo "  □ 观察回复风格是否有变化（应该更符合 Portrait 定义）"
echo "  □ 发送 /deepflow 测试认知报告生成"
echo "  □ 检查日志: tail -f ~/.openclaw/logs/gateway.log"
echo ""
echo "🔧 如遇问题:"
echo "  • 插件未加载 → 检查 plugin.json 格式是否正确"
echo "  • Agent 无响应 → 确认 Agent 的 SKILL.md 是否正确引用"
echo "  • 报告生成失败 → 检查数据库路径和环境变量配置"
echo ""
echo "========================================"
