from src.openclaw_flow_plugin.core.llm_manager import LLMManager
import sqlite3

print("=== 使用云端MiniMax LLM进行目标验证 ===")
print()

# 使用MiniMax LLM
llm = LLMManager(provider="minimax")

conn = sqlite3.connect('flow_ecosystem.db')
cursor = conn.cursor()
cursor.execute('SELECT id, declared_text FROM goals WHERE status = "active" LIMIT 10')
goals = cursor.fetchall()
conn.close()

print("测试MiniMax LLM目标验证:")
print("-" * 60)

valid_count = 0
for goal_id, text in goals:
    result = llm.is_valid_goal(text)
    if result:
        valid_count += 1
        status = "✅"
    else:
        status = "❌"
    print(f"{status} [{goal_id}] {text[:40]}...")

print()
print(f"验证结果: {valid_count}/{len(goals)} 有效")
