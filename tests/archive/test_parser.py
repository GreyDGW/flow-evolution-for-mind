import sys, os
sys.path.insert(0, os.getcwd())
import path_setup
from plugin.session_analyzer import SiliconFlowLLMClient, SessionAnalyzer

client = SiliconFlowLLMClient()
analyzer = SessionAnalyzer(client)

messages = [
    {"role": "user", "content": "我在想思维连续性保护器的 Session 切割逻辑"},
    {"role": "assistant", "content": "建议三层渐进式：硬规则兜底 + 向量层实时计算"},
    {"role": "user", "content": "那 4维判定模型能稳定输出高/中/低吗？"},
    {"role": "assistant", "content": "测试证明可以。关键是 Prompt 固化格式"},
]

conversation = analyzer._format_conversation(messages)
print("对话内容:")
print(conversation)
print("\n" + "="*50 + "\n")

result = analyzer.analyze(messages, memory_path="MEMORY.md")
if result:
    print("解析成功")
    print("目标对齐:", result.goal_alignment)
else:
    print("解析失败")

raw = client.generate("你是认知分析师。请从4个维度给出判定：\n目标感：高，证据：用户明确目标\n闭环感：中，证据：讨论有结果\n沉浸感：高，证据：深入讨论\n成长感：中，证据：有收获\n只输出这4行")
print("\n原始LLM输出:")
print(raw)
print("\n解析结果:")
parsed = analyzer._parse_llm_output(raw)
print(parsed)