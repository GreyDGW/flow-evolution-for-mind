#!/bin/bash
# ════════════════════════════════════════════════════
#  调音系统测试脚本 - 两极 Portrait 对比测试
#
#  用法:
#    bash test_tuning.sh A    # 设置 Test A: 四维协同(峰值/进攻态)
#    bash test_tuning.sh B    # 设置 Test B: 能量耗尽(低能量/呵护态)
#    bash test_tuning.sh reset # 恢复原始值
#    bash test_tuning.sh show  # 查看当前状态
#
#  测试方法:
#    1. 运行 bash test_tuning.sh A
#    2. 重启 Gateway (openclaw gateway restart)
#    3. 打开任意 Agent 对话，发一条普通消息
#    4. 观察 AI 回复风格是否匹配「四维协同」描述
#    5. 运行 bash test_tuning.sh B
#    6. 重启 Gateway
#    7. 发另一条普通消息
#    8. 观察 AI 回复风格是否完全不同（匹配「能量耗尽」）
# ════════════════════════════════════════════════════

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

if [ ! -f "$DB_PATH" ]; then
    echo -e "${RED}[ERROR] DB not found: $DB_PATH${NC}"
    exit 1
fi

TARGET_AGENT="${2:-secretary}"

echo ""
case "${1}" in
    A|a|peak|alpha)
        echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
        echo -e "${BLUE}║  Test A: 四维协同 (Peak / 攻击态)       ║${NC}"
        echo -e "${BLUE}╚══════════════════════════════════════════╝${NC}"
        echo ""

        STYLE='{"pace":"converge","depth":"deep","tone":"neutral","friction":"socratic","portrait":"四维协同"}'

        echo -e "  ${BOLD}Portrait${NC}:   ${CYAN}四维协同${NC}"
        echo -e "  ${BOLD}Pace${NC}:       converge     (方向盘→给方案, 收敛方向)"
        echo -e "  ${BOLD}Depth${NC}:      deep         (油门踩死, 深度分析)"
        echo -e "  ${BOLD}Tone${NC}:       neutral      (空调温度→中性客观)"
        echo -e "  ${BOLD}Friction${NC}:   socratic     (离合器→以问代答, 苏格拉底)"
        echo ""
        echo -e "  ${YELLOW}预期行为:${NC}"
        echo "    ┌─ 直接切入底层逻辑，高密度推演"
        echo "    ├─ 每个回复以问题收尾，推动自我发现"
        echo "    ├─ 禁止寒暄/解释思考过程/情绪安抚"
        echo "    ├─ 禁止封闭式提问"
        echo "    └─ 推动决策，记录峰值条件"
        echo ""

        sqlite3 "$DB_PATH" "INSERT OR REPLACE INTO kv_store(agent_id,key,value,updated_at) VALUES('$TARGET_AGENT','current_style','$STYLE',datetime('now'));"

        echo -e "  ${GREEN}[DONE]${NC} $TARGET_AGENT → 四维协同 (converge/deep/neutral/socratic)"
        ;;

    B|b|burnout|beta)
        echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
        echo -e "${BLUE}║  Test B: 能量耗尽 (Burnout / 呵护态)    ║${NC}"
        echo -e "${BLUE}╚══════════════════════════════════════════╝${NC}"
        echo ""

        STYLE='{"pace":"hold","depth":"surface","tone":"soft","friction":"direct","portrait":"能量耗尽"}'

        echo -e "  ${BOLD}Portrait${NC}:   ${CYAN}能量耗尽${NC}"
        echo -e "  ${BOLD}Pace${NC}:       hold         (方向盘→不推, 保持现状)"
        echo -e "  ${BOLD}Depth${NC}:      surface      (油门浅踩, 不深入)"
        echo -e "  ${BOLD}Tone${NC}:       soft         (空调温度→温柔)"
        echo -e "  ${BOLD}Friction${NC}:   direct       (离合器→直接给答案)"
        echo ""
        echo -e "  ${YELLOW}预期行为:${NC}"
        echo "    ┌─ 主动包揽全部逻辑推演"
        echo "    ├─ 直接给定论或 A/B 封闭式选项"
        echo "    ├─ 禁止抛出需要用户梳理逻辑的开放式提问"
        echo "    ├─ 禁止要求用户做多选或长文本输入"
        echo "    └─ 极致省脑，零认知负担"
        echo ""

        sqlite3 "$DB_PATH" "INSERT OR REPLACE INTO kv_store(agent_id,key,value,updated_at) VALUES('$TARGET_AGENT','current_style','$STYLE',datetime('now'));"

        echo -e "  ${GREEN}[DONE]${NC} $TARGET_AGENT → 能量耗尽 (hold/surface/soft/direct)"
        ;;

    show|status)
        echo -e "${BLUE}── Current Style States ──${NC}"
        echo ""
        printf "  %-18s %-12s %-10s %-8s %-8s %-10s %s\n" \
            "AGENT" "PORTRAIT" "PACE" "DEPTH" "TONE" "FRICTION" "UPDATED"
        echo "  ──────────────────────────────────────────────────────────────────────────────"
        sqlite3 -separator '|' "$DB_PATH" "
            SELECT 
                agent_id,
                json_extract(value, '$.portrait'),
                json_extract(value, '$.pace'),
                json_extract(value, '$.depth'),
                json_extract(value, '$.tone'),
                json_extract(value, '$.friction'),
                updated_at
            FROM kv_store WHERE key='current_style'
            ORDER BY agent_id;
        " | while IFS='|' read -r aid port pace depth tone fri upd; do
            TAG=""
            if [ "$port" = '"'"'四维协同'"'"' ]; then TAG="${CYAN}[PEAK]${NC}"
            elif [ "$port" = '"'"'能量耗尽'"'"' ]; then TAG="${YELLOW}[BURNOUT]${NC}"
            fi
            printf "  %-18s ${BOLD}%-12s${NC} %-10s %-8s %-8s %-10s %s%s\n" \
                "$aid" "$port" "$pace" "$depth" "$tone" "$fri" "$upd" "$TAG"
        done
        echo ""
        echo -e "  Target test agent: ${BOLD}$TARGET_AGENT${NC}"
        echo -e "  DB path: $DB_PATH"
        ;;

    reset)
        DEFAULT_STYLE='{"pace": "explore", "depth": "surface", "tone": "neutral", "friction": "direct", "portrait": "平稳推进"}'
        sqlite3 "$DB_PATH" "INSERT OR REPLACE INTO kv_store(agent_id,key,value,updated_at) VALUES('$TARGET_AGENT','current_style','$DEFAULT_STYLE',datetime('now'));"
        echo -e "${GREEN}[RESET]${NC} All agents → 平稳推进 (default)"
        ;;

    *)
        echo "Usage:"
        echo "  $0 A [agent_id]   Set Test A: 四维协同 (peak/aggressive)"
        echo "  $0 B [agent_id]   Set Test B: 能量耗尽 (burnout/gentle)"
        echo "  $0 show           Show current style states"
        echo "  $0 reset          Reset all to default (平稳推进)"
        echo ""
        echo "Default agent: secretary"
        echo ""
        echo "Test flow:"
        echo "  1. $0 A && openclaw gateway restart"
        echo "  2. Send a message in any agent chat"
        echo "  3. Check if AI behaves like '四维协同'"
        echo "  4. $0 B && openclaw gateway restart"
        echo "  5. Send another message"
        echo "  6. Check if AI behavior changes dramatically"
        exit 1
        ;;
esac

echo ""
echo -e "  Next step: ${YELLOW}openclaw gateway restart${NC} then send a message in ${BOLD}$TARGET_AGENT${NC}"
