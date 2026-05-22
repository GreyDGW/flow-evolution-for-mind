import path_setup
#!/usr/bin/env python3
"""测试 LLM 精判层触发条件"""
from src.session import VectorLayer, CutDecision
from plugin.session.embedding import create_embedder

embedder = create_embedder()

# 测试1: turn_count=12 → 应触发 LLM 调用
print("=== 测试1: turn_count=12 ===")
vl1 = VectorLayer(embedder=embedder)
for i in range(11):
    vl1.add_turn(f"这是第{i}轮对话内容")
decision, reason, metadata = vl1.decide("这是一个新消息内容")
print(f"决策: {decision.value}")
print(f"原因: {reason}")
print(f"触发LLM: {metadata.get('triggered', 'N/A')}")

# 测试2: turn_count=3 + 含"摆烂" → 应触发 LLM（情绪 bypass）
print("\n=== 测试2: turn_count=3 + 含'摆烂' ===")
vl2 = VectorLayer(embedder=embedder)
for i in range(2):
    vl2.add_turn(f"正常对话{i}")
decision, reason, metadata = vl2.decide("摆烂了，不想干了")
print(f"决策: {decision.value}")
print(f"原因: {reason}")
print(f"触发LLM: {metadata.get('triggered', 'N/A')}")

# 测试3: turn_count=3 + 正常内容 → 应返回"未达触发条件"
print("\n=== 测试3: turn_count=3 + 正常内容 ===")
vl3 = VectorLayer(embedder=embedder)
for i in range(2):
    vl3.add_turn(f"正常对话{i}")
decision, reason, metadata = vl3.decide("好的，我继续研究")
print(f"决策: {decision.value}")
print(f"原因: {reason}")
print(f"触发LLM: {metadata.get('triggered', 'N/A')}")

print("\n✅ 测试完成")
