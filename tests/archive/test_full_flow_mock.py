import sys, os
sys.path.insert(0, os.getcwd())
import path_setup

from plugin.session_analyzer import SessionAnalysis
from plugin.state_distiller import StateDistiller

analysis = SessionAnalysis(
    goal_alignment='高', goal_evidence='持续讨论API性能优化方案',
    closure_index='中', closure_evidence='讨论了多个方案但未落地',
    flow_depth='高', flow_evidence='连续深入讨论技术细节',
    cognition_growth='中', cognition_evidence='了解了新的优化方法'
)

print('=' * 50)
print('【步骤1】SessionAnalyzer 4维判定')
print('=' * 50)
print(f'目标对齐: {analysis.goal_alignment} ({analysis.goal_evidence})')
print(f'闭环指数: {analysis.closure_index} ({analysis.closure_evidence})')
print(f'心流深度: {analysis.flow_depth} ({analysis.flow_evidence})')
print(f'认知成长: {analysis.cognition_growth} ({analysis.cognition_evidence})')

distiller = StateDistiller(memory_path='MEMORY.md')
portrait = distiller.distill(analysis)

print('\n' + '=' * 50)
print('【步骤2】StateDistiller 规则匹配')
print('=' * 50)
print(f'标签: {portrait.label}')
print(f'描述: {portrait.description}')
print(f'洞察: {portrait.rule_insight}')
print(f'建议: {portrait.suggestion}')
print(f'pace: {portrait.style.pace}')
print(f'depth: {portrait.style.depth}')
print(f'tone: {portrait.style.tone}')
print(f'调音文本:\n{portrait.tuning_text}')

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