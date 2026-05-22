import sys, os
sys.path.insert(0, os.getcwd())
import path_setup
from plugin.session_analyzer import SessionAnalysis
from plugin.state_distiller import StateDistiller

print("=== Phase 1 端到端链路验证 (Mock) ===")
print("="*50)

print("1️⃣ 模拟 SessionAnalyzer 输出...")
analysis = SessionAnalysis(
    goal_alignment='高', goal_evidence='讨论思维连续性保护器的Session切割',
    closure_index='高', closure_evidence='讨论了具体方案',
    flow_depth='中', flow_evidence='聚焦技术细节',
    cognition_growth='中', cognition_evidence='深化理解'
)

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
print(f"   ✅ 洞察: {portrait.rule_insight[:50]}...")

print("\n3️⃣ 更新 MEMORY.md...")
distiller.update_memory(portrait)
print("   ✅ 已写入 FLOW_STYLE 锚点")

print("\n" + "="*50)
print("🎉 Phase 1 端到端链路验证通过！")

print("\n=== 验证 MEMORY.md 内容 ===")
with open("MEMORY.md", "r") as f:
    content = f.read()
    start = content.find("<!-- FLOW_STYLE_START -->")
    end = content.find("<!-- FLOW_STYLE_END -->")
    print(content[start:end+22])