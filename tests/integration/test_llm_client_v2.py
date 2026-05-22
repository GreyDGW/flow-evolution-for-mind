import path_setup
from src.core import MockLLMClient, get_llm_config
from src.session import ClosureAnalyzer


def test_mock_llm_structure():
    llm = MockLLMClient()
    messages = [
        {"role": "user", "content": "我想优化查询性能，计划加索引"},
        {"role": "assistant", "content": "好的"},
        {"role": "user", "content": "加了索引，测试提升30%，文档也写好了"},
    ]
    active_goals = [{"text": "成为架构师", "type": "长期", "status": "推进中"}]

    result = llm.analyze_session(messages, active_goals)

    assert "goal" in result and "pdca" in result
    assert "flow" in result and "cognition" in result
    assert "base_quality" in result["flow"]
    assert "signal_gain" in result["flow"]
    assert "score" in result["flow"]["base_quality"]["logic_depth"]
    assert "evidence" in result["flow"]["base_quality"]["logic_depth"]
    print("✅ MockLLMClient 结构测试通过")


def test_closure_analyzer():
    analyzer = ClosureAnalyzer(MockLLMClient())
    messages = [
        {"role": "user", "content": "我想优化查询，计划加索引"},
        {"role": "assistant", "content": "好的"},
        {"role": "user", "content": "加了索引，测试提升30%，文档写好了"},
    ]
    active_goals = [{"text": "成为架构师", "type": "长期", "status": "推进中"}]

    result = analyzer.analyze_session(messages, active_goals)

    assert "goal_alignment" in result
    assert "ewci" in result
    assert "flow_depth" in result
    assert 0 <= result["flow_depth"] <= 100
    print("✅ ClosureAnalyzer 测试通过")
    print(f"   闭环指数: {result['ewci']:.1f}")
    print(f"   心流深度: {result['flow_depth']:.1f}")


if __name__ == "__main__":
    test_mock_llm_structure()
    test_closure_analyzer()
    print("🎉 全部通过")
