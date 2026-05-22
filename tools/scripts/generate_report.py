import json
from collections import Counter

with open('/tmp/llm_analysis_results.json', 'r') as f:
    results = json.load(f)

print('='*80)
print('Flow Ecosystem 会话分析报告 - MiniMax-M2.7 云端LLM分析')
print('='*80)
print()

pdca_stats = {'plan': 0, 'do': 0, 'check': 0, 'adjust': 0}
pdca_total = 0

flow_qualities = {'high': 0, 'medium': 0, 'low': 0}
focus_indicators = []

evolution_types = {}
evolution_total = 0

goal_types = {}
goal_total = 0

for r in results:
    llm = r.get('llm_analysis', {})
    if 'error' in llm:
        continue

    pdca = llm.get('pdca_analysis', {})
    if pdca.get('has_plan'):
        pdca_stats['plan'] += 1
    if pdca.get('has_do'):
        pdca_stats['do'] += 1
    if pdca.get('has_check'):
        pdca_stats['check'] += 1
    if pdca.get('has_adjust'):
        pdca_stats['adjust'] += 1
    pdca_total += 1

    flow = llm.get('flow_state', {})
    quality = flow.get('flow_quality', 'low')
    if quality in flow_qualities:
        flow_qualities[quality] += 1
    focus = flow.get('focus_indicator', '')
    if focus:
        focus_indicators.append(focus)

    cog = llm.get('cognitive_evolution', {})
    if cog.get('has_evolution', False):
        evolution_total += 1
        etype = cog.get('evolution_type', 'unknown')
        evolution_types[etype] = evolution_types.get(etype, 0) + 1

    goals = llm.get('goal_extraction', {})
    if goals.get('has_goals', False):
        for gt in goals.get('goal_types', []):
            goal_types[gt] = goal_types.get(gt, 0) + 1
        goal_total += 1

print('【1. 目标提取分析】')
print('-'*60)
print(f'包含明确目标的会话: {goal_total}/{len(results)} ({goal_total/len(results)*100:.1f}%)')
print()
print('目标类型分布:')
for gt, count in sorted(goal_types.items(), key=lambda x: -x[1]):
    print(f'  {gt}: {count}')

print()
print('【2. PDCA闭环分析】')
print('-'*60)
print(f'具有完整PDCA闭环的会话: {pdca_stats["adjust"]}/{pdca_total} ({pdca_stats["adjust"]/pdca_total*100:.1f}%)')
print()
print('PDCA各阶段统计:')
print(f'  Plan(计划): {pdca_stats["plan"]}/{pdca_total} ({pdca_stats["plan"]/pdca_total*100:.1f}%)')
print(f'  Do(执行): {pdca_stats["do"]}/{pdca_total} ({pdca_stats["do"]/pdca_total*100:.1f}%)')
print(f'  Check(检查): {pdca_stats["check"]}/{pdca_total} ({pdca_stats["check"]/pdca_total*100:.1f}%)')
print(f'  Adjust(调整): {pdca_stats["adjust"]}/{pdca_total} ({pdca_stats["adjust"]/pdca_total*100:.1f}%)')

print()
print('【3. 心流状态分析】')
print('-'*60)
print('心流质量分布:')
for quality, count in sorted(flow_qualities.items(), key=lambda x: -x[1]):
    print(f'  {quality}: {count} ({count/len(results)*100:.1f}%)')
print()
print('专注指示器 (Top 5):')
focus_counter = Counter(focus_indicators)
for focus, count in focus_counter.most_common(5):
    print(f'  {focus}: {count}')

print()
print('【4. 认知进化分析】')
print('-'*60)
print(f'显示认知进化的会话: {evolution_total}/{len(results)} ({evolution_total/len(results)*100:.1f}%)')
print()
print('进化类型分布:')
for etype, count in sorted(evolution_types.items(), key=lambda x: -x[1]):
    print(f'  {etype}: {count}')

print()
print('='*80)
print('分析完成 - 使用MiniMax-M2.7云端模型')
print('='*80)