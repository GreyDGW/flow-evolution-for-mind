from src.openclaw_flow_plugin.core.llm_manager import LLMManager
import sqlite3

print("=== 测试目标对齐度验证 ===")
print()

llm = LLMManager(provider="minimax")

conn = sqlite3.connect('flow_ecosystem.db')
cursor = conn.cursor()
cursor.execute('SELECT id, declared_text FROM goals WHERE status = "active" LIMIT 15')
goals = cursor.fetchall()
conn.close()

print("测试结果:")
print("-" * 80)

aligned_count = 0
for goal_id, text in goals:
    # 判断是否有效目标
    is_valid = llm.is_valid_goal(text)
    # 判断是否对齐Flow Ecosystem
    is_aligned = llm.is_goal_aligned(text)

    if is_aligned:
        aligned_count += 1
        valid_mark = "✅"
        align_mark = "✅"
    else:
        valid_mark = "✅" if is_valid else "❌"
        align_mark = "❌"

    print(f"{align_mark} [{goal_id}] {valid_mark} | {text[:50]}...")

print()
print(f"对齐Flow Ecosystem: {aligned_count}/{len(goals)}")
