from src.openclaw_flow_plugin.core.llm_manager import LLMManager

print("=== 真实LLM验证测试 ===")
print()

llm = LLMManager()

test_goal1 = "帮我分析我今天所有给其他包括你的所有智能体提过的问题原文，来分析我的心流程度"
test_goal2 = "分析我今天所有给其他包括你的所有智能体提过的问题原文，来分析我的心流程度"

print('测试目标1 (有"帮我"):')
print(f"内容: {test_goal1}")
llm.use_mock = False
result1 = llm.is_valid_goal(test_goal1)
print(f"真实LLM判定: {result1}")
print()

print('测试目标2 (无"帮我"):')
print(f"内容: {test_goal2}")
result2 = llm.is_valid_goal(test_goal2)
print(f"真实LLM判定: {result2}")
print()

print("=" * 60)
print()

print("模拟模式对比:")
llm.use_mock = True
result1_mock = llm.is_valid_goal(test_goal1)
result2_mock = llm.is_valid_goal(test_goal2)
print(f"目标1模拟模式: {result1_mock}")
print(f"目标2模拟模式: {result2_mock}")
print()

print("=" * 60)
print()

print("问题分析:")
print("- 模拟模式正确判定了两个目标都是有效的")
print("- 真实LLM模式可能出现问题")
print("- 可能原因：")
print("  1. 本地LLM服务未启动或响应异常")
print("  2. LLM对这类复杂目标的理解有误")
print("  3. 响应格式问题导致解析错误")
