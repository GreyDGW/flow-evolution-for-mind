import sqlite3

conn = sqlite3.connect("flow_ecosystem.db")
cursor = conn.cursor()

cursor.execute("SELECT id, declared_text FROM goals WHERE status = 'active' LIMIT 30")
goals = cursor.fetchall()

conn.close()

flow_keywords = ["心流", "flow", "认知", "进化", "目标", "对齐", "PDCA", "闭环", "分析报告", "智能体", "agent", "对话", "session"]

print("=== 与Flow Ecosystem不直接相关的对话 ===")
print()

unrelated = []
related = []

for goal_id, text in goals:
    has_flow_keyword = any(kw.lower() in text.lower() for kw in flow_keywords)
    if has_flow_keyword:
        related.append((goal_id, text))
    else:
        unrelated.append((goal_id, text))

print("不相关对话:")
print("-" * 60)
for goal_id, text in unrelated:
    print(f"❌ [{goal_id}] {text}")

print()
print("相关对话:")
print("-" * 60)
for goal_id, text in related:
    print(f"✅ [{goal_id}] {text}")

print()
print(f"统计: 不相关 {len(unrelated)} / 相关 {len(related)}")
print(f"不相关比例: {len(unrelated)/(len(unrelated)+len(related))*100:.1f}%")
