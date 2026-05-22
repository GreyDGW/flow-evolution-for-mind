import sys, os
sys.path.insert(0, os.getcwd())
import path_setup
from plugin.session_analyzer import SessionAnalyzer, SiliconFlowLLMClient
messages = [
    {"role": "user", "content": "我在想思维连续性保护器的 Session 切割逻辑"},
    {"role": "assistant", "content": "建议三层渐进式：硬规则兜底 + 向量层实时计算"},
    {"role": "user", "content": "那 4维判定模型能稳定输出高/中/低吗？"},
    {"role": "assistant", "content": "测试证明可以。关键是 Prompt 固化格式"},
]
client = SiliconFlowLLMClient()
analyzer = SessionAnalyzer(client)
result = analyzer.analyze(messages, memory_path="MEMORY.md")
print("验证3: SessionAnalyzer 测试")
if result:
    print("目标对齐:", result.goal_alignment)
    print("闭环指数:", result.closure_index)
    print("心流深度:", result.flow_depth)
    print("认知成长:", result.cognition_growth)
    if result.goal_alignment == "高":
        print("验证 3 通过：目标对齐功能未受损")
else:
    print("解析失败")