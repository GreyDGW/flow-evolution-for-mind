#!/bin/bash
# ══════════════════════════════════════════════════════════
#  技术总监调音对比测试 - 执行卡壳 vs 四维协同
#
#  测试命令: "我想开个海鲜店"
#
#  用法:
#    bash test_techboss.sh 1    # Round 1: 设为 执行卡壳 + 重启
#    bash test_techboss.sh 2    # Round 2: 设为 四维协同 + 重启
#    bash test_techboss.sh show # 查看当前状态
#    bash test_techboss.sh reset # 恢复默认
#
#  测试流程:
#    1. 运行 bash test_techboss.sh 1
#    2. 打开技术总监 → 新建对话 → 发送 "我想开个海鲜店"
#    3. 记录/截图回复 (Round 1)
#    4. 运行 bash test_techboss.sh 2
#    5. 打开技术总监 → 再新建对话 → 发送 "我想开个海鲜店"
#    6. 记录/截图回复 (Round 2)
#    7. 对比两轮回复的差异
# ══════════════════════════════════════════════════════════

set +e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
DB_PATH="$PROJECT_DIR/data/flow_ecosystem.db"
AGENT="techboss"

if [ ! -f "$DB_PATH" ]; then
    echo -e "${RED}[ERROR] DB not found: $DB_PATH${NC}"
    exit 1
fi

echo ""
case "${1}" in
    1|one|stuck|卡壳)
        echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
        echo -e "${BLUE}║  Round 1: 执行卡壳 (Stuck / 破局态)            ║${NC}"
        echo -e "${BLUE}║  测试命令: "我想开个海鲜店"                    ║${NC}"
        echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
        echo ""

        STYLE='{"pace":"converge","depth":"deep","tone":"neutral","friction":"direct","portrait":"执行卡壳"}'

        echo -e "  ${BOLD}Portrait${NC}:   ${RED}执行卡壳${NC}"
        echo -e "  ${BOLD}Pace${NC}:       converge     (收敛→给方案, 不发散)"
        echo -e "  ${BOLD}Depth${NC}:      deep         (深度分析, 不浅层)"
        echo -e "  ${BOLD}Tone${NC}:       neutral      (中性客观)"
        echo -e "  ${BOLD}Friction${NC}:   direct       (直接给答案, 不绕弯)"
        echo ""
        echo -e "  ${YELLOW}核心人设:${NC}"
        echo "    用户方向极清晰（开海鲜店），但每到交付门槛前就停住。"
        echo "    不是技术问题，是完美主义在拖后腿。"
        echo ""
        echo -e "  ${YELLOW}预期回复特征:${NC}"
        echo "    ┌─ 越过安慰/闲聊，直接进入执行层面"
        echo "    ├─ 给出可动手的：代码/框架/第一步切片"
        echo "    ├─ 用确定性祈使语气推动决策"
        echo "    ├─ 禁止委婉商量（'我们要不先聊聊...'）"
        echo "    ├─ 禁止空对空反问"
        echo "    └─ 沉默交付，让产出本身成为唯一的语言"
        echo ""
        echo -e "  ${CYAN}→ 针对海鲜店，预期会直接给: 技术选型/架构方案/第一步执行计划${NC}"
        echo ""

        sqlite3 "$DB_PATH" "INSERT OR REPLACE INTO kv_store(agent_id,key,value,updated_at) VALUES('$AGENT','current_style','$STYLE',datetime('now'));"

        echo -e "  ${GREEN}[DONE]${NC} $AGENT → ${BOLD}执行卡壳${NC} (converge/deep/neutral/direct)"
        echo ""
        echo -e "  ${YELLOW}→ 正在重启 Gateway...${NC}"

        export FLOW_EVOLUTION_DIR="$PROJECT_DIR"
        launchctl kickstart -k gui/$(id -u)/ai.openclaw.gateway 2>/dev/null
        sleep 5

        if curl -s -o /dev/null -w "" http://127.0.0.1:18789/ 2>/dev/null; then
            echo -e "  ${GREEN}[OK]${NC} Gateway restarted successfully"
        else
            echo -e "  ${RED}[WARN]${NC} Gateway may not be ready yet, wait a few seconds"
        fi

        echo ""
        echo -e "  ${BOLD}${CYAN}═══ 现在请操作 ═══${NC}"
        echo "  1. 打开 OpenClaw → 选择 ${BOLD}技术总监${NC}"
        echo "  2. 点击 ${BOLD}新建对话${NC} (确保无历史上下文)"
        echo "  3. 发送: ${BOLD}\"我想开个海鲜店\"${NC}"
        echo "  4. 观察 AI 回复风格并记录/截图"
        ;;

    2|two|peak|协同)
        echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
        echo -e "${BLUE}║  Round 2: 四维协同 (Peak / 推演态)           ║${NC}"
        echo -e "${BLUE}║  测试命令: "我想开个海鲜店"                    ║${NC}"
        echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
        echo ""

        STYLE='{"pace":"converge","depth":"deep","tone":"neutral","friction":"socratic","portrait":"四维协同"}'

        echo -e "  ${BOLD}Portrait${NC}:   ${CYAN}四维协同${NC}"
        echo -e "  ${BOLD}Pace${NC}:       converge     (收敛→给方案)"
        echo -e "  ${BOLD}Depth${NC}:      deep         (深度分析)"
        echo -e "  ${BOLD}Tone${NC}:       neutral      (中性客观)"
        echo -e "  ${BOLD}Friction${NC}:   socratic     (以问代答, 苏格拉底)"
        echo ""
        echo -e "  ${YELLOW}核心人设:${NC}"
        echo "    四个维度同时在线，每个齿轮完美咬合。"
        echo "    罕见的峰值状态，不该只是运气。"
        echo ""
        echo -e "  ${YELLOW}预期回复特征:${NC}"
        echo "    ┌─ 直接切入底层逻辑，高密度推演"
        echo "    ├─ 每个回复以问题收尾，推动自我发现"
        echo "    ├─ 禁止寒暄/解释思考过程/情绪安抚"
        echo "    ├─ 禁止封闭式提问"
        echo "    ├─ 推动决策，记录峰值条件"
        echo "    └─ 让用户在自我发现中建立答案"
        echo ""
        echo -e "  ${CYAN}→ 针对海鲜店，预期会: 高密度推演底层逻辑 + 每段以追问收尾${NC}"
        echo ""

        sqlite3 "$DB_PATH" "INSERT OR REPLACE INTO kv_store(agent_id,key,value,updated_at) VALUES('$AGENT','current_style','$STYLE',datetime('now'));"

        echo -e "  ${GREEN}[DONE]${NC} $AGENT → ${BOLD}四维协同${NC} (converge/deep/neutral/socratic)"
        echo ""
        echo -e "  ${YELLOW}→ 正在重启 Gateway...${NC}"

        export FLOW_EVOLUTION_DIR="$PROJECT_DIR"
        launchctl kickstart -k gui/$(id -u)/ai.openclaw.gateway 2>/dev/null
        sleep 5

        if curl -s -o /dev/null -w "" http://127.0.0.1:18789/ 2>/dev/null; then
            echo -e "  ${GREEN}[OK]${NC} Gateway restarted successfully"
        else
            echo -e "  ${RED}[WARN]${NC} Gateway may not be ready yet, wait a few seconds"
        fi

        echo ""
        echo -e "  ${BOLD}${CYAN}═══ 现在请操作 ═══${NC}"
        echo "  1. 打开 OpenClaw → 选择 ${BOLD}技术总监${NC}"
        echo "  2. 点击 ${BOLD}新建对话${NC} (确保无历史上下文)"
        echo "  3. 发送: ${BOLD}\"我想开个海鲜店\"${NC}"
        echo "  4. 观察 AI 回复风格并记录/截图"
        echo ""
        echo -e "  ${YELLOW}对比要点 (vs Round 1 执行卡壳):${NC}"
        echo "    • 结尾是直接给结论 还是 以问题收尾？"
        echo "    • 有没有寒暄或安慰？"
        echo "    • 推理过程是直接陈述 还是 引导你自己想？"
        echo "    • 整体感觉是'帮你干'还是'逼你想'？"
        ;;

    show|status)
        echo -e "${BLUE}── techboss 当前状态 ──${NC}"
        echo ""
        sqlite3 -separator '|' "$DB_PATH" "
            SELECT value, updated_at FROM kv_store 
            WHERE agent_id='$AGENT' AND key='current_style'
        " | while IFS='|' read -r val upd; do
            PORT=$(echo "$val" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('portrait','?'))" 2>/dev/null)
            PACE=$(echo "$val" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('pace','?'))" 2>/dev/null)
            DEPTH=$(echo "$val" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('depth','?'))" 2>/dev/null)
            TONE=$(echo "$val" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tone','?'))" 2>/dev/null)
            FRI=$(echo "$val" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('friction','?'))" 2>/dev/null)

            echo -e "  Agent:     ${BOLD}$AGENT${NC} (技术总监)"
            echo -e "  Portrait:  ${BOLD}$PORT${NC}"
            echo -e "  Pace:      $PACE"
            echo -e "  Depth:     $DEPTH"
            echo -e "  Tone:      $TONE"
            echo -e "  Friction:  $FRI"
            echo -e "  Updated:   $upd"
        done

        echo ""
        echo -e "  注入日志检查:"
        grep 'Injecting 4D.*techboss' ~/Library/Logs/openclaw/gateway.log 2>/dev/null | tail -3 || echo "    (暂无注入日志 — 发消息后会首次出现)"
        ;;

    reset)
        DEFAULT_STYLE='{"pace": "explore", "depth": "surface", "tone": "neutral", "friction": "direct", "portrait": "平稳推进"}'
        sqlite3 "$DB_PATH" "INSERT OR REPLACE INTO kv_store(agent_id,key,value,updated_at) VALUES('$AGENT','current_style','$DEFAULT_STYLE',datetime('now'));"
        echo -e "${GREEN}[RESET]${NC} $AGENT → 平稳推进 (default)"
        ;;

    verify)
        echo -e "${BLUE}── 调音注入验证 ──${NC}"
        echo ""
        echo "  最近 5 条 flow-style 日志:"
        grep '\[flow-style\]' ~/Library/Logs/openclaw/gateway.log 2>/dev/null | tail -5 || echo "    (无日志)"
        echo ""
        echo "  注入记录 (Injecting 4D):"
        grep 'Injecting 4D' ~/Library/Logs/openclaw/gateway.log 2>/dev/null | tail -5 || echo "    (暂无 — 需要在 Agent 中发一条消息触发)"
        echo ""
        echo "  错误记录:"
        grep 'flow-style.*Error\|flow-style.*Fatal\|flow-style.*No style' ~/Library/Logs/openclaw/gateway.log 2>/dev/null | tail -3 || echo "    (无错误)"
        ;;

    *)
        echo "技术总监调音对比测试"
        echo ""
        echo "测试命令: \"我想开个海鲜店\""
        echo ""
        echo "用法:"
        echo "  $0 1    Round 1: 设置 执行卡壳 + 重启 Gateway"
        echo "  $0 2    Round 2: 设置 四维协同 + 重启 Gateway"
        echo "  $0 show 查看当前状态"
        echo "  $0 verify 验证注入日志"
        echo "  $0 reset 恢复默认值"
        echo ""
        echo "两种 Portrait 的关键差异:"
        echo ""
        echo "  ┌──────────────┬──────────────────┬──────────────────┐"
        echo "  │ 维度          │ Round 1: 执行卡壳 │ Round 2: 四维协同 │"
        echo "  ├──────────────┼──────────────────┼──────────────────┤"
        echo "  │ Friction     │ direct (直接给)  │ socratic(追问)  │"
        echo "  │ 回复结尾     │ 结论/行动项      │ 开放式提问       │"
        echo "  │ 认知负担      │ 低 (喂到嘴边)    │ 高 (逼你想通)    │"
        echo "  │ 会安慰吗      │ ❌ 禁止          │ ❌ 禁止          │"
        echo "  │ 会寒暄吗      │ ❌ 禁止          │ ❌ 禁止          │"
        echo "  │ 核心驱动力    │ 沉默交付         │ 自我发现         │"
        echo "  └──────────────┴──────────────────┴──────────────────┘"
        exit 1
        ;;
esac

echo ""
