import path_setup
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from plugin.session.closure_analyzer import ClosureAnalyzer
from core.llm_client import MockLLMClient


def test_closure_analyzer_basic():
    llm = MockLLMClient()
    analyzer = ClosureAnalyzer(llm)
    
    messages = [
        {"role": "user", "content": "我想优化API性能"},
        {"role": "assistant", "content": "好的，可以从数据库优化入手"}
    ]
    
    result = analyzer.analyze_session(messages)
    
    assert "goal_alignment" in result
    assert "pdca" in result
    assert "flow_depth" in result
    print("✅ ClosureAnalyzer 基本测试通过")


if __name__ == "__main__":
    test_closure_analyzer_basic()