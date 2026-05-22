#!/usr/bin/env python3
"""会话切割逻辑测试脚本"""

from src.openclaw_flow_plugin.core.session_cutter import SessionCutter, CutDecision
from datetime import datetime, timedelta

def test_hard_rules():
    print("\n" + "="*60)
    print("硬规则层测试")
    print("="*60)

    cutter = SessionCutter()

    tests = [
        {
            "name": "测试1: 短消息豁免",
            "current": "好的",
            "previous_time": timedelta(minutes=2),
            "previous_content": "帮我写一个函数"
        },
        {
            "name": "测试2: 超时切割 (>30分钟)",
            "current": "继续刚才的话题",
            "previous_time": timedelta(minutes=45),
            "previous_content": "..."
        },
        {
            "name": "测试3: 显式切割 (/new)",
            "current": "/new",
            "previous_time": timedelta(minutes=5),
            "previous_content": "之前讨论的内容"
        },
        {
            "name": "测试4: 代码块延续",
            "current": "```python\ndef hello():\n    pass\n```",
            "previous_time": timedelta(minutes=3),
            "previous_content": "```python\nprint(1)\n```"
        },
        {
            "name": "测试5: 普通消息需要向量层判断",
            "current": "我们来讨论一下数据库设计",
            "previous_time": timedelta(minutes=10),
            "previous_content": "我想聊聊微服务架构"
        },
        {
            "name": "测试6: Heartbeat切割 (>2小时)",
            "current": "我回来了",
            "previous_time": timedelta(minutes=150),
            "previous_content": "之前的话题"
        }
    ]

    for test in tests:
        print(f"\n{test['name']}")
        result = cutter.cut_decision(
            current_turn_content=test["current"],
            current_turn_time=datetime.now(),
            previous_turn_time=datetime.now() - test["previous_time"],
            previous_turn_content=test["previous_content"]
        )
        print(f"  决策: {result.decision.value}")
        print(f"  原因: {result.reason}")
        print(f"  层级: {result.layer}")

def test_vector_layer():
    print("\n" + "="*60)
    print("向量判定层测试（需要embedding函数）")
    print("="*60)

    def mock_embedding(text):
        return [1.0, 0.5, 0.3] if "数据库" in text else [0.8, 0.4, 0.6]

    cutter = SessionCutter(embedding_func=mock_embedding)

    print("\n模拟语义相似度判断...")
    print("当相似度 > 0.55: CONTINUE")
    print("当相似度 < 0.25: CUT")
    print("当相似度 0.25-0.55: 需要LLM判断")

def test_llm_arbiter():
    print("\n" + "="*60)
    print("LLM精判层测试")
    print("="*60)

    print("\n触发条件:")
    print("1. 向量层返回模糊地带（0.25-0.55）")
    print("2. 当前Session已累积 ≥ 10 个Turn")
    print("3. 或规则层检测到情绪硬信号")
    print("\n当前未配置LLM客户端，模糊地带默认延续")

if __name__ == "__main__":
    print("会话切割逻辑测试")
    print("基于 Flow Ecosystem PRD V7.4 三层渐进式架构")

    test_hard_rules()
    test_vector_layer()
    test_llm_arbiter()

    print("\n" + "="*60)
    print("测试完成")
    print("="*60)