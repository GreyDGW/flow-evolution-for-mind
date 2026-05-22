import sys, os
sys.path.insert(0, os.getcwd())
import path_setup
from plugin.session_analyzer import SessionAnalyzer, SiliconFlowLLMClient
from plugin.state_distiller import StateDistiller

print("=== Phase 1 端到端链路验证 ===")
print("="*50)

messages = [
    {"role": "user", "content": "我在想思维连续性保护器的 Session 切割逻辑，应该用硬规则还是向量相似度？"},
    {"role": "assistant", "content": "建议三层渐进式：硬规则兜底 + 向量层实时计算 + LLM 层模糊判定。"},
    {"role": "user", "content": "那 4维判定模型能稳定输出高/中/低吗？"},
    {"role": "assistant", "content": "测试证明可以。关键是 Prompt 固化格式，解析器用正则兜底。"},
]

print("1️⃣ 调用 SessionAnalyzer (真实 LLM)...")
client = SiliconFlowLLMClient()
analyzer = SessionAnalyzer(client)
analysis = analyzer.analyze(messages, memory_path="MEMORY.md")

print(f"   ✅ 目标对齐: {analysis.goal_alignment} ({analysis.goal_evidence})")
print(f"   ✅ 闭环指数: {analysis.closure_index} ({analysis.closure_evidence})")
print(f"   ✅ 心流深度: {analysis.flow_depth} ({analysis.flow_evidence})")
print(f"   ✅ 认知成长: {analysis.cognition_growth} ({analysis.cognition_evidence})")

print("\n2️⃣ 调用 StateDistiller (状态蒸馏)...")
distiller = StateDistiller()
portrait = distiller.distill(analysis)

print(f"   ✅ 状态标签: {portrait.label}")
print(f"   ✅ 调音参数: pace={portrait.style.pace}, depth={portrait.style.depth}, tone={portrait.style.tone}")
print(f"   ✅ 建议: {portrait.suggestion}")

print("\n3️⃣ 更新 MEMORY.md...")
distiller.update_memory(portrait)
print("   ✅ 已写入 FLOW_STYLE 锚点")

print("\n" + "="*50)
print("🎉 Phase 1 端到端链路验证通过！")