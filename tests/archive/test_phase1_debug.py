import sys, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
import path_setup

from plugin.session_analyzer import SessionAnalyzer, SiliconFlowLLMClient
from plugin.state_distiller import StateDistiller

print("=== Phase 1 端到端链路验证 ===")
print("=" * 50)

messages = [
    {'role': 'user', 'content': '我在想这个API的性能优化方案，应该用Redis缓存还是本地内存？'},
    {'role': 'assistant', 'content': 'Redis适合分布式，本地内存适合单机。'},
    {'role': 'user', 'content': '但是Redis的序列化开销会不会成为瓶颈？'},
    {'role': 'assistant', 'content': '可以考虑二进制序列化。'},
    {'role': 'user', 'content': '那如果缓存穿透怎么办？'},
    {'role': 'assistant', 'content': '布隆过滤器适合读多写少。'},
]

client = SiliconFlowLLMClient()
analyzer = SessionAnalyzer(client)

print("1️⃣ SessionAnalyzer 4维判定...")
analysis = analyzer.analyze(messages, memory_path='MEMORY.md')

if analysis is None:
    print("❌ analyze() 返回 None")
    sys.exit(1)

print(f"   ✅ 目标对齐: {analysis.goal_alignment} ({analysis.goal_evidence})")
print(f"   ✅ 闭环指数: {analysis.closure_index} ({analysis.closure_evidence})")
print(f"   ✅ 心流深度: {analysis.flow_depth} ({analysis.flow_evidence})")
print(f"   ✅ 认知成长: {analysis.cognition_growth} ({analysis.cognition_evidence})")

print("\n2️⃣ StateDistiller 规则匹配...")
distiller = StateDistiller(memory_path='MEMORY.md')
portrait = distiller.distill(analysis)

print(f"   ✅ 标签: {portrait.label}")
print(f"   ✅ pace: {portrait.style.pace}, depth: {portrait.style.depth}, tone: {portrait.style.tone}")
print(f"   ✅ 建议: {portrait.suggestion}")

print("\n3️⃣ 更新 MEMORY.md...")
distiller.update_memory(portrait)

print("\n" + "=" * 50)
print("🎉 Phase 1 端到端链路验证通过！")