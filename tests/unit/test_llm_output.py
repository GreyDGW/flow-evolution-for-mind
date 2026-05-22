import path_setup
#!/usr/bin/env python3
from src.core import OpenClawLLMClient, get_llm_config
import json

config = get_llm_config()
client = OpenClawLLMClient(**config)

messages = [
    {'role': 'user', 'content': '我打算重构订单模块，用策略模式替换if-else'},
    {'role': 'assistant', 'content': '策略模式适合多种计价规则'},
    {'role': 'user', 'content': '我写了PriceStrategy接口，实现了3个子类，单元测试覆盖率85%'},
    {'role': 'assistant', 'content': '性能提升明显'},
    {'role': 'user', 'content': '文档更新了，总结了最佳实践'},
]

goals = [{'text': '成为架构师', 'type': '长期', 'status': '推进中'}]

print("=== 输入 ===")
for m in messages:
    print(f"  {m['role']}: {m['content'][:40]}...")
print("\n=== 调用LLM ===")

result = client.analyze_session(messages, goals)

print("\n=== LLM输出 ===")
print(json.dumps(result, ensure_ascii=False, indent=2))
