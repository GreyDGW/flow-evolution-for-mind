#!/usr/bin/env python3
"""测试真实Phi-2模型集成"""

from src.openclaw_flow_plugin.core.llm_manager import LLMManager
from src.openclaw_flow_plugin.core.goal_manager import GoalManager

def test_real_phi2():
    print("=" * 70)
    print("🧠 真实Phi-2模型测试")
    print("=" * 70)
    
    # 测试LLM管理器
    print("\n1️⃣ 测试LLM管理器")
    llm = LLMManager()
    print(f"✅ LLM管理器初始化成功")
    print(f"   - 模型: {llm.model_name}")
    print(f"   - 使用模拟模式: {llm.use_mock}")
    
    # 测试目标提取
    print("\n2️⃣ 测试目标提取")
    test_texts = [
        "我想学习Python编程，这周完成基础语法",
        "帮我修改flow ecosystem的技能",
        "这个功能怎么做？",
        "翻译这个单词"
    ]
    
    for text in test_texts:
        result = llm.extract_goals(text)
        print(f"\n用户消息: {text}")
        print(f"提取结果: {result}")
    
    # 测试闭环分析
    print("\n3️⃣ 测试闭环分析")
    conversation = """
    用户：我计划今天完成API文档。
    用户：文档已经写完了，正在检查。
    用户：发现了几个错误，已经修正了。
    """
    result = llm.analyze_closure(conversation)
    print(f"对话分析结果: {result}")
    
    # 测试目标管理器
    print("\n4️⃣ 测试目标管理器（使用真实LLM）")
    gm = GoalManager('flow_ecosystem.db', use_llm=True)
    goals = gm.extract_goals_from_text("我想创建一个个人进化系统", None)
    print(f"从文本提取的目标: {goals}")
    
    # 添加目标到数据库
    if goals:
        goal = gm.add_goal(goals[0]['declared_text'])
        print(f"✅ 添加目标成功，ID: {goal.id}")
    
    # 获取活跃目标
    active_goals = gm.get_active_goals()
    print(f"活跃目标数量: {len(active_goals)}")
    
    gm.close()
    
    print("\n✅ 测试完成！")

if __name__ == '__main__':
    test_real_phi2()