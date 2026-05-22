import sys, os
sys.path.insert(0, os.getcwd())
import path_setup
from plugin.session_analyzer import SessionAnalyzer, SiliconFlowLLMClient

messages = [
    {"role": "user", "content": "我在想思维连续性保护器的 Session 切割逻辑，应该用硬规则还是向量相似度？"},
    {"role": "assistant", "content": "建议三层渐进式：硬规则兜底 + 向量层实时计算 + LLM 层模糊判定。"},
    {"role": "user", "content": "那 4维判定模型能稳定输出高/中/低吗？"},
    {"role": "assistant", "content": "测试证明可以。关键是 Prompt 固化格式，解析器用正则兜底。"},
]

client = SiliconFlowLLMClient()
analyzer = SessionAnalyzer(client)

MEMORY = "/Users/duguowei/Desktop/OpenClaw-Secretary-Backup-20260415-2235/MEMORY.md"
result = analyzer.analyze(messages, memory_path=MEMORY)

print("=" * 50)
print("验证3: SessionAnalyzer 真实 LLM 测试")
print("=" * 50)

if result:
    print("解析成功")
    print("目标对齐:", result.goal_alignment, result.goal_evidence)
    print("闭环指数:", result.closure_index, result.closure_evidence)
    print("心流深度:", result.flow_depth, result.flow_evidence)
    print("认知成长:", result.cognition_growth, result.cognition_evidence)
    if result.goal_alignment == "高":
        print("验证 3 通过：目标对齐功能未受损")
    else:
        print("目标感=", result.goal_alignment)
else:
    print("解析失败")