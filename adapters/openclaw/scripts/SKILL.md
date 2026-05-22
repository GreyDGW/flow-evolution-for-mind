> **[PLATFORM LIMIT]** OpenClaw's system Agent (e.g., "secretary") may have a built-in `/flow` shortcut that overrides external Skills. If `/flow` returns a short summary instead of the full report, use **`/deepflow`** or **`/cognitive-report`** instead.

---
name: "flow-evolution-for-mind"
description: "Generate cognitive mirror reports and flow state analysis. Trigger when user asks about work review, cognitive state, flow report, or inputs /flow."
---

## 【输出约束 - 绝对遵守】

当调用 `flow_handler.py` 并收到其返回的 Markdown 报告时：
- **必须直接原样输出**，禁止调用 LLM 重新生成、摘要、压缩
- **禁止省略任何章节**：包括 Agent 详情、Session 案例、维度详细解读、证据原文
- **禁止修改格式**：保留所有 Markdown 表格、标题层级、代码块
- 如果报告长度超过单条消息限制，**分多条消息发送**，而非压缩内容

## When to use this skill

Use this skill when:
- User inputs `/flow`
- User asks "这周怎么样"、"最近状态如何"、"帮我复盘"
- User asks "查看工作复盘"、"生成认知镜像"
- User asks "4月19日报告"、"昨天的情况"
- User asks "推荐个工具"、"我卡住了"、"破局"

Do not use this skill for general chat or non-flow technical questions.

## How to use this skill

1. Extract intent and time range from user message:
   - intent_type: mirror / tool_recommend / unblock
   - time_keyword: today / yesterday / week / date / last_N
   - date_value: when time_keyword=date (e.g. 2026-04-19)
   - limit: when time_keyword=last_N (e.g. 5)

2. Run the report script from the OpenClaw workspace:

```bash
python3 {baseDir}/scripts/flow_handler.py \
  --intent-type mirror \
  --time-keyword week \
  --date-value 2026-04-19 \
  --limit 5
```

Adjust parameters based on extracted intent/time.

If no time specified, default to `--time-keyword today`.

The script will return a Markdown report. Display it directly to the user.

If the script fails, show: "报告生成失败，请稍后重试或检查核心层安装"

## Command examples

**user:** 这周怎么样
**You:** Run from the OpenClaw workspace:
```bash
python3 {baseDir}/scripts/flow_handler.py --time-keyword week
```

**user:** /flow
**You:** Run from the OpenClaw workspace:
```bash
python3 {baseDir}/scripts/flow_handler.py --time-keyword today
```

**user:** 4月19日的认知镜像
**You:** Run from the OpenClaw workspace:
```bash
python3 {baseDir}/scripts/flow_handler.py --time-keyword date --date-value 2026-04-19
```

**user:** 最近5个session
**You:** Run from the OpenClaw workspace:
```bash
python3 {baseDir}/scripts/flow_handler.py --time-keyword last_N --limit 5
```

## Tips

- `{baseDir}` is the skill directory: `~/.openclaw/skills/flow-evolution-for-mind`
- The script uses stderr for progress messages, stdout for the final Markdown report
- If the core layer is not installed, the script will show installation instructions
