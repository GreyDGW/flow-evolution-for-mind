import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import path_setup

from plugin.session_analyzer import SessionAnalyzer, SiliconFlowLLMClient
from plugin.state_distiller import StateDistiller

# 1. 构造测试对话（执行卡壳场景）
messages = [
    {'role': 'user', 'content': '我在想这个API的性能优化方案，应该用Redis缓存还是本地内存？'},
    {'role': 'assistant', 'content': 'Redis适合分布式，本地内存适合单机。你的场景是微服务架构，建议Redis。'},
    {'role': 'user', 'content': '但是Redis的序列化开销会不会成为瓶颈？'},
    {'role': 'assistant', 'content': '可以考虑二进制序列化，比如MessagePack，比JSON快3-5倍。'},
    {'role': 'user', 'content': '那如果缓存穿透怎么办？布隆过滤器还是互斥锁？'},
    {'role': 'assistant', 'content': '布隆过滤器适合读多写少，互斥锁适合一致性要求高。'},
]

# 2. SessionAnalyzer 4维判定
print('=' * 50)
print('【步骤1】SessionAnalyzer 4维判定')
print('=' * 50)

client = SiliconFlowLLMClient()
analyzer = SessionAnalyzer(client)
analysis = analyzer.analyze(messages, memory_path='MEMORY.md')

print(f'目标对齐: {analysis.goal_alignment} ({analysis.goal_evidence})')
print(f'闭环指数: {analysis.closure_index} ({analysis.closure_evidence})')
print(f'心流深度: {analysis.flow_depth} ({analysis.flow_evidence})')
print(f'认知成长: {analysis.cognition_growth} ({analysis.cognition_evidence})')

# 3. StateDistiller 规则匹配
print('\n' + '=' * 50)
print('【步骤2】StateDistiller 规则匹配')
print('=' * 50)

distiller = StateDistiller(memory_path='MEMORY.md')
portrait = distiller.distill(analysis)

print(f'标签: {portrait.label}')
print(f'描述: {portrait.description}')
print(f'洞察: {portrait.rule_insight}')
print(f'建议: {portrait.suggestion}')
print(f'pace: {portrait.style.pace}')
print(f'depth: {portrait.style.depth}')
print(f'tone: {portrait.style.tone}')
print(f'调音文本:\n{portrait.tuning_text}')

# 4. 写入 MEMORY.md
distiller.update_memory(portrait)

print('\n' + '=' * 50)
print('【步骤3】MEMORY.md 更新验证')
print('=' * 50)

with open('MEMORY.md', 'r') as f:
    content = f.read()
    if 'FLOW_STYLE_START' in content:
        import re
        m = re.search(r'<!-- FLOW_STYLE_START -->(.*?)<!-- FLOW_STYLE_END -->', content, re.DOTALL)
        if m:
            print(f'锚点内容:\n{m.group(1).strip()}')
            print('\n✅ Phase 1 端到端链路验证通过！')
        else:
            print('❌ 锚点格式异常')
    else:
        print('❌ FLOW_STYLE 锚点不存在')
