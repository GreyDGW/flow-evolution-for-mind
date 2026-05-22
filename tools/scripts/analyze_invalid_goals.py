goals = [
    "帮我打开我的记忆文档",
    "帮我打开我前几天的记忆文档",
    "帮我继续走Memory Wiki 的路线",
    "memory-core 的 artifacts是指什么，需要我做什么吗",
    "帮我执行，如果能修好，我就用bridge",
    "帮我切换成bridge模式",
    "做到根据最新记忆实时对话的",
    "现在全球的AI大神都是怎么做的",
    "帮我把所有的 session 的thinkingLevel 都调整成high",
    "分析我今天所有给其他包括你的所有智能体提过的问题原文，来分析我的心流程度"
]

print("=== 无效目标分析 ===")
print()

for i, goal in enumerate(goals, 1):
    print(f"{i}. {goal}")
    
    if "打开" in goal:
        reason = "操作类请求 - 只是打开文档，不是需要追踪的长期目标"
    elif "什么" in goal or "怎么做" in goal:
        reason = "追问式问题 - 缺少明确的任务意图，需要进一步澄清"
    elif "执行" in goal or "切换" in goal or "调整" in goal:
        reason = "即时操作指令 - 一次性操作，不需要长期追踪"
    elif len(goal) < 15:
        reason = "目标太简短 - 不够明确，缺少具体内容"
    else:
        reason = "需要进一步分析 - 可能是描述不完整"
    
    print(f"   → {reason}")
    print()

print("=== 总结 ===")
print("当前LLM验证逻辑判定为无效的原因主要有：")
print("1. 操作类请求（打开、执行、切换、调整）")
print("2. 追问式问题（什么、怎么）")
print("3. 目标描述不完整或太简短")
