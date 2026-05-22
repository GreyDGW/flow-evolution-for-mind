from src.openclaw_flow_plugin.core.llm_session_analyzer import LLMDrivenSessionAnalyzer
import json

analyzer = LLMDrivenSessionAnalyzer()

print('='*70)
print('LLM驱动的会话分析 - 完整分析报告')
print('='*70)
print()

sessions = analyzer.get_sessions(limit=37)
print(f'总计会话数: {len(sessions)}')
print()

results = []
for i, session in enumerate(sessions, 1):
    session_id = session['session_id']
    print(f'正在分析会话 {i}/{len(sessions)}...')
    analysis = analyzer.analyze_with_llm(session_id)
    results.append(analysis)

print()
print('='*70)
print('汇总统计')
print('='*70)

total = len(results)
flow_related = 0
goal_aligned = 0
total_goals = []
avg_completion = 0
avg_alignment = 0
avg_flow_depth = 0
avg_evolution = 0
strategic_counts = {'🎯 卓越': 0, '✅ 达成': 0, '⚠️ 偏离': 0, '❌ 失效': 0}

for analysis in results:
    if 'error' in analysis.get('llm_analysis', {}):
        continue

    llm = analysis.get('llm_analysis', {})
    prd_idx = analyzer.calculate_prd_index(analysis)

    if llm.get('flow_ecosystem_related', {}).get('is_related', False):
        flow_related += 1

    if llm.get('goal_extraction', {}).get('has_goals', False):
        goal_aligned += 1
        total_goals.extend(llm.get('goal_extraction', {}).get('main_goals', []))

    avg_completion += prd_idx['completion_score']
    avg_alignment += prd_idx['goal_alignment_percent']
    avg_flow_depth += llm.get('flow_state', {}).get('flow_depth', 0)
    avg_evolution += llm.get('cognitive_evolution', {}).get('evolution_score', 0)
    strategic_counts[prd_idx['strategic_status']] += 1

print(f'Flow Ecosystem相关会话: {flow_related}/{total} ({flow_related/total*100:.1f}%)')
print(f'包含目标会话: {goal_aligned}/{total} ({goal_aligned/total*100:.1f}%)')
print(f'提取的目标数: {len(total_goals)}')
print()
print(f'平均完成度: {avg_completion/total:.1%}')
print(f'平均目标对齐度: {avg_alignment/total:.1f}%')
print(f'平均心流深度: {avg_flow_depth/total:.1%}')
print(f'平均认知进化: {avg_evolution/total:.1%}')
print()
print('战略状态分布:')
for status, count in strategic_counts.items():
    print(f'  {status}: {count} ({count/total*100:.1f}%)')

print()
print('='*70)
print('目标列表')
print('='*70)
for i, goal in enumerate(total_goals[:20], 1):
    print(f'{i}. {goal}')
if len(total_goals) > 20:
    print(f'... 还有 {len(total_goals) - 20} 个目标')

with open('/tmp/llm_analysis_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print()
print('详细结果已保存到 /tmp/llm_analysis_results.json')