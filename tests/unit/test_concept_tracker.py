import path_setup
#!/usr/bin/env python3
import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

from src.core import ConceptTracker, DailyAggregator, OpenClawLLMClient, get_llm_config
from src.session import SemanticSessionCutter, ClosureAnalyzer, TurnPreprocessor
import time

# 1. 准备昨日概念（模拟历史数据）
tracker = ConceptTracker()
tracker.store_daily_concepts('2026-05-01', {
    '微服务拆分', 'DDD领域图', '熔断机制', 'Saga模式',
    '用户服务', '订单服务', '分布式事务'
})
print('昨日概念:', tracker.get_concepts('2026-05-01'))

# 2. 今日真实对话（工作 Session）
msgs = [
    {'role':'user','content':'我打算重构订单模块，用策略模式替换if-else'},
    {'role':'assistant','content':'策略模式适合多种计价规则，先抽象接口'},
    {'role':'user','content':'我写了PriceStrategy接口，实现了3个子类'},
    {'role':'user','content':'单元测试覆盖率85%，压测QPS从1200提升到1800'},
    {'role':'assistant','content':'性能提升明显，文档呢'},
    {'role':'user','content':'文档更新了，还做了团队分享，总结了最佳实践'},
]

# 3. Preprocessor + SessionCutter
pp = TurnPreprocessor()
cleaned = []
for m in msgs:
    r = pp.preprocess(m.get('content', ''))
    cleaned.append({**m, 'content': r.get('embedding_text', m['content'])})

cutter = SemanticSessionCutter()
sessions = cutter.cut_sessions(cleaned, threshold=0.15)
print(f'\n切分: {len(sessions)} 个 Session')

# 4. LLM 分析
client = OpenClawLLMClient(**get_llm_config())
analyzer = ClosureAnalyzer(client)
goals = [{'text': '成为架构师', 'type': '长期', 'status': '推进中'}]

results = []
for idx, session in enumerate(sessions):
    t0 = time.time()
    r = analyzer.analyze_session(session, goals)
    t1 = time.time()
    results.append(r)
    g = r.get('goal_alignment', {})
    print(f"S{idx+1}({len(session)}轮): EWCI={r.get('ewci',0):.1f} 心流={r.get('flow_depth',0):.1f} 推进={g.get('goal_progress',0)} ({t1-t0:.1f}s)")

# 5. 提取今日概念
today_concepts = tracker.extract_concepts(results)
tracker.store_daily_concepts('2026-05-02', today_concepts)
print(f'\n今日概念: {today_concepts}')

# 6. 计算 Hub 稳定性
hub_stability = tracker.calculate_hub_stability('2026-05-02')
print(f'Hub 稳定性(Jaccard): {hub_stability}')

# 7. 日级聚合
agg = DailyAggregator()
metrics = agg.aggregate('2026-05-02', results)
print('\n' + agg.generate_report('2026-05-02'))