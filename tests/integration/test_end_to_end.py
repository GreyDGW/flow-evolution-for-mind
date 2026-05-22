import path_setup
#!/usr/bin/env python3
"""
端到端集成测试（简化版，跳过不可用的组件）
验证：Preprocessor → LLM → ClosureAnalyzer
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.session import TurnPreprocessor, ClosureAnalyzer
from src.core import OpenClawLLMClient, get_llm_config


def test_end_to_end():
    raw_messages = [
        {"role": "user", "content": "我打算把单体应用拆成微服务，计划先拆用户服务和订单服务，用 DDD 划分边界"},
        {"role": "assistant", "content": "好的，建议先画领域图，确定聚合根"},
        {"role": "user", "content": "我画完了领域图，拆出了4个服务，代码也改了，把用户表拆到 user-service 里了"},
        {"role": "assistant", "content": "拆分后数据一致性怎么处理？"},
        {"role": "user", "content": "我测试了分布式事务，用 Saga 模式跑了100次压测，成功率99.8%，文档也写好了"},
    ]

    print("=" * 60)
    print("端到端集成测试（简化版）")
    print("=" * 60)
    print(f"原始消息数: {len(raw_messages)}")

    # [1] Preprocessor 清洗
    print("\n[1/3] Preprocessor 清洗...")
    preprocessor = TurnPreprocessor()
    cleaned = []
    for msg in raw_messages:
        result = preprocessor.preprocess(msg.get('content', ''))
        cleaned.append({
            'role': msg.get('role', 'user'),
            'content': result.get('embedding_text', msg.get('content', '')),
        })
    print(f"  清洗后消息数: {len(cleaned)}")

    # [2] LLM + ClosureAnalyzer 分析
    print("\n[2/3] LLM 分析...")
    config = get_llm_config()
    client = OpenClawLLMClient(config["api_key"], config["base_url"], config["model"])
    analyzer = ClosureAnalyzer(client)

    active_goals = [
        {"text": "完成微服务拆分方案", "type": "中期", "status": "推进中"},
    ]

    print(f"  分析 {len(cleaned)} 条消息...")
    result = analyzer.analyze_session(cleaned, active_goals)

    print(f"\n  ✅ EWCI: {result.get('ewci', 0):.1f}")
    print(f"  ✅ 心流深度: {result.get('flow_depth', 0):.1f}")
    print(f"  ✅ 完整度: {result.get('completeness', 0):.1f}")
    print(f"  ✅ 质量: {result.get('quality', 0):.1f}")
    print(f"  ✅ 目标推进: {result.get('goal_alignment', {}).get('goal_progress', 0)}")
    print(f"  ✅ 漂移: {result.get('goal_alignment', {}).get('drift_score', 0):.2f}")

    pdca = result.get('pdca', {})
    for stage in ['plan', 'do', 'check', 'adjust']:
        info = pdca.get(stage, {})
        print(f"  - {stage}: detected={info.get('detected')}, completeness={info.get('completeness')}")

    if result.get('_error'):
        print(f"\n  ⚠️ 警告: {result['_error'][:80]}")

    print("\n" + "=" * 60)
    print("端到端测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_end_to_end()