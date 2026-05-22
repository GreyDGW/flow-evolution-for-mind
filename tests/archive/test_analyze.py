import sys, os
sys.path.insert(0, os.getcwd())
import path_setup
from plugin.session_analyzer import SiliconFlowLLMClient, SessionAnalyzer, load_memory_fulltext

client = SiliconFlowLLMClient()
analyzer = SessionAnalyzer(client)

messages = [
    {"role": "user", "content": "我在想思维连续性保护器的 Session 切割逻辑"},
    {"role": "assistant", "content": "建议三层渐进式：硬规则兜底 + 向量层实时计算"},
    {"role": "user", "content": "那 4维判定模型能稳定输出高/中/低吗？"},
    {"role": "assistant", "content": "测试证明可以。关键是 Prompt 固化格式"},
]

print("测试 load_memory_fulltext:")
mem = load_memory_fulltext("MEMORY.md")
print(f"MEMORY.md 内容长度: {len(mem)} 字符")
print(f"前100字符: {mem[:100] if mem else '空'}")

print("\n测试 analyze 方法:")
try:
    result = analyzer.analyze(messages, memory_path="MEMORY.md")
    if result:
        print("解析成功")
        print("目标对齐:", result.goal_alignment)
        print("闭环指数:", result.closure_index)
        print("心流深度:", result.flow_depth)
        print("认知成长:", result.cognition_growth)
    else:
        print("返回 None")
except Exception as e:
    print("异常:", e)
    import traceback
    traceback.print_exc()