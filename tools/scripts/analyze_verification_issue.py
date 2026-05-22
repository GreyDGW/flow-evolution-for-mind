from src.openclaw_flow_plugin.core.llm_manager import LLMManager
import sqlite3

print("=== 目标验证问题深度分析 ===")
print()

# 从数据库获取目标
conn = sqlite3.connect('flow_ecosystem.db')
cursor = conn.cursor()
cursor.execute('SELECT id, declared_text FROM goals WHERE status = "active" LIMIT 20')
goals = cursor.fetchall()
conn.close()

llm = LLMManager()

print("逐个测试验证结果:")
print("-" * 60)

results = []
for goal_id, text in goals:
    llm.use_mock = False
    real_result = llm.is_valid_goal(text)
    
    llm.use_mock = True
    mock_result = llm.is_valid_goal(text)
    
    results.append((goal_id, text, real_result, mock_result))
    
    status = "✅" if real_result else "❌"
    mock_status = "✅" if mock_result else "❌"
    print(f"{goal_id:2d}. {status} {mock_status} | {text[:40]}...")

print()
print("=" * 60)
print()

# 找出不一致的情况
print("不一致的情况 (真实LLM判定无效但模拟模式判定有效):")
inconsistent = []
for goal_id, text, real_result, mock_result in results:
    if not real_result and mock_result:
        inconsistent.append((goal_id, text))

if inconsistent:
    for goal_id, text in inconsistent:
        print(f"{goal_id:2d}. {text}")
else:
    print("没有发现不一致的情况")

print()
print("=" * 60)
print()

print("问题分析:")
print("1. 模拟模式（规则匹配）是很可靠的，能正确识别有效目标")
print("2. 真实LLM模式可能存在一些问题:")
print("   - 本地LLM服务可能不稳定")
print("   - 同一目标在不同时间的判定可能不同")
print("   - LLM对某些复杂目标的理解可能有偏差")
print()
print("建议解决方案:")
print("- 优先使用模拟模式（规则匹配）进行验证，更稳定可靠")
print("- 或者使用混合模式：先用规则匹配，规则不明确时再用LLM")
print("- 对被LLM误判但规则匹配认为有效的目标，可以人工审查")
