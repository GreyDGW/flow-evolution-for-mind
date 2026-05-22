import path_setup
#!/usr/bin/env python3
"""
综合端到端测试 - 使用固化后的完整组件
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import time
import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

from src.core import GoalLoader, OpenClawLLMClient, get_llm_config
from src.session import TurnPreprocessor, SemanticSessionCutter, ClosureAnalyzer


def run_scenario(name, messages):
    """跑单场景完整链路"""
    print(f"\n{'='*60}")
    print(f"场景: {name}")
    print(f"原始消息: {len(messages)}轮")

    # 1. Preprocessor 清洗
    pp = TurnPreprocessor()
    cleaned = []
    for m in messages:
        r = pp.preprocess(m.get('content', ''))
        cleaned.append({**m, 'content': r.get('embedding_text', m['content'])})

    # 2. SessionCutter 切分
    cutter = SemanticSessionCutter()
    sessions = cutter.cut_sessions(cleaned, threshold=0.15)
    print(f"切分: {len(sessions)} 个 Session")
    for idx, s in enumerate(sessions):
        print(f"  S{idx+1}: {len(s)}轮 | {s[0]['content'][:22]}...")

    # 3. GoalLoader 读取目标
    loader = GoalLoader()
    goals = loader.load_active_goals()

    # 4. LLM 分析
    client = OpenClawLLMClient(**get_llm_config())
    analyzer = ClosureAnalyzer(client)

    results = []
    for idx, session in enumerate(sessions):
        t0 = time.time()
        r = analyzer.analyze_session(session, goals)
        t1 = time.time()
        results.append(r)
        g = r.get('goal_alignment', {})
        print(f"  S{idx+1}({len(session)}轮): EWCI={r.get('ewci',0):.1f} 心流={r.get('flow_depth',0):.1f} "
              f"推进={g.get('goal_progress',0)} 漂移={g.get('drift_score',0):.2f} ({t1-t0:.1f}s)")

    return results


def simple_aggregate(date, all_results):
    """简化日级聚合（占位版）"""
    valid = [r for r in all_results if r.get('ewci', 0) > 10 or r.get('flow_depth', 0) > 50]
    if not valid:
        return None

    avg_ewci = sum(r.get('ewci', 0) for r in valid) / len(valid)
    avg_flow = sum(r.get('flow_depth', 0) for r in valid) / len(valid)

    quality = avg_flow * (avg_ewci / 100) * 100

    print(f"\n📊 {date} 日级聚合")
    print(f"  有效Session: {len(valid)}")
    print(f"  平均EWCI: {avg_ewci:.1f}")
    print(f"  平均心流: {avg_flow:.1f}")
    print(f"  结构质量分: {quality:.1f}")
    print(f"  认知进化(简化): {quality * 0.8:.1f}")

    return quality


def main():
    print("="*60)
    print("综合端到端测试 - 固化组件完整链路")
    print("="*60)

    scene1 = [
        {'role':'user','content':'我打算重构订单模块，用策略模式替换if-else'},
        {'role':'assistant','content':'策略模式适合多种计价规则，先抽象接口'},
        {'role':'user','content':'我写了PriceStrategy接口，实现了3个子类'},
        {'role':'user','content':'单元测试覆盖率85%，压测QPS从1200提升到1800'},
        {'role':'assistant','content':'性能提升明显，文档呢'},
        {'role':'user','content':'文档更新了，还做了团队分享，总结了最佳实践'},
    ]

    scene2 = [
        {'role':'user','content':'我要优化数据库查询，准备加索引'},
        {'role':'assistant','content':'先分析慢查询日志'},
        {'role':'user','content':'中午吃什么好'},
        {'role':'assistant','content':'楼下有拉面'},
        {'role':'user','content':'我加了联合索引，QPS从200提升到800'},
    ]

    scene3 = [
        {'role':'user','content':'我要做缓存方案，打算用Redis集群'},
        {'role':'assistant','content':'考虑一致性哈希'},
        {'role':'user','content':'周末去哪玩'},
        {'role':'assistant','content':'去爬山吧'},
        {'role':'user','content':'好啊，记得带防晒霜'},
        {'role':'assistant','content':'没问题'},
        {'role':'user','content':'我配好了Redis Cluster，3主3从，压测了failover'},
    ]

    scene4 = [
        {'role':'user','content':'周末有什么电影推荐'},
        {'role':'assistant','content':'哪吒2还在映，特效不错'},
        {'role':'user','content':'那去看哪吒2，看完去吃海底捞'},
        {'role':'assistant','content':'可以，提前排号'},
    ]

    scene5 = [
        {'role':'user','content':'你刚才给的方案有问题，Saga不适合强一致性，应该用TCC'},
        {'role':'assistant','content':'TCC确实更强'},
        {'role':'user','content':'TCC的Cancel不是回滚，是释放预留资源，我之前项目踩过坑'},
        {'role':'assistant','content':'你的总结很到位'},
        {'role':'user','content':'基于这个经验，我要抽象成通用组件，让其他服务复用'},
    ]

    scene6 = [
        {'role':'user','content':'今天北京天气'},
        {'role':'assistant','content':'晴天，25度'},
        {'role':'user','content':'好的谢谢'},
    ]

    scenarios = [
        ("密集工作-完整闭环", scene1),
        ("工作+单句闲聊豁免", scene2),
        ("工作+多轮闲聊+工作", scene3),
        ("纯闲聊-电影美食", scene4),
        ("技术深度-批判AI", scene5),
        ("事务性-查天气", scene6),
    ]

    all_results = []
    for name, msgs in scenarios:
        results = run_scenario(name, msgs)
        all_results.extend(results)
        time.sleep(1)

    print(f"\n{'='*60}")
    simple_aggregate("2026-05-01", all_results)

    print(f"\n{'='*60}")
    print("✅ 综合端到端测试完成")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()