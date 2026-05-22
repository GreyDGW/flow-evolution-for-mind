import sys, os
sys.path.insert(0, os.getcwd())
import path_setup
from plugin.state_distiller import StateDistiller, StyleParams, StatePortrait
from plugin.session_analyzer import SessionAnalysis

print("=== 测试 MEMORY.md 锚点写入 ===")

analysis = SessionAnalysis(
    goal_alignment='高', goal_evidence='方向明确',
    closure_index='低', closure_evidence='无产出',
    flow_depth='中', flow_evidence='有讨论',
    cognition_growth='中', cognition_evidence='未突破'
)

distiller = StateDistiller()
portrait = distiller.distill(analysis)

print(f"状态标签: {portrait.label}")
print(f"pace: {portrait.style.pace}")
print(f"tuning_text:\n{portrait.tuning_text}")

distiller.update_memory(portrait)
print("\n✅ update_memory 执行完成")

print("\n=== 检查 MEMORY.md 内容 ===")
with open('MEMORY.md', 'r') as f:
    content = f.read()
    print(content)