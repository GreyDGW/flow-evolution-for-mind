#!/usr/bin/env python3
"""测试集成LLM的目标管理模块"""

from datetime import datetime
import sys
sys.path.insert(0, '/Users/duguowei/Desktop/skill相关文档/openclaw_flow_plugin/src')

from openclaw_flow_plugin.core.goal_manager import GoalManager

def test_goal_manager_with_llm():
    print("=" * 70)
    print("🎯 目标管理模块集成LLM测试")
    print("=" * 70)
    
    print("\n1️⃣ 创建目标管理器（使用LLM）")
    gm = GoalManager('flow_ecosystem.db', use_llm=True)
    
    print("\n2️⃣ 测试LLM目标提取")
    user_message = "我想学习Python编程，这周完成基础语法学习"
    goals = gm.extract_goals_from_text(user_message, datetime.now())
    
    print(f"用户消息: {user_message}")
    print(f"提取的目标:")
    for goal in goals:
        print(f"  - [{goal['time_horizon']}] {goal['declared_text']} (复杂度: {goal['complexity_score']})")
    
    print("\n3️⃣ 测试添加目标")
    if goals:
        goal_data = goals[0]
        goal = gm.add_goal(goal_data['declared_text'], goal_data['declared_at'], goal_data['time_horizon'])
        print(f"添加成功！目标ID: {goal.id}, 状态: {goal.status}")
    
    print("\n4️⃣ 测试正则表达式回退（禁用LLM）")
    gm_no_llm = GoalManager('flow_ecosystem.db', use_llm=False)
    goals_no_llm = gm_no_llm.extract_goals_from_text("帮我修改flow ecosystem的技能", datetime.now())
    
    print(f"用户消息: 帮我修改flow ecosystem的技能")
    print(f"提取的目标:")
    for goal in goals_no_llm:
        print(f"  - [{goal['time_horizon']}] {goal['declared_text']}")
    
    print("\n5️⃣ 获取活跃目标统计")
    goals_by_horizon = gm.get_goals_by_horizon()
    for horizon, goal_list in goals_by_horizon.items():
        horizon_label = {'short': '短期', 'medium': '中期', 'long': '长期'}[horizon]
        print(f"{horizon_label}目标: {len(goal_list)}个")
    
    gm.close()
    gm_no_llm.close()
    
    print("\n✅ 测试完成！")

if __name__ == '__main__':
    test_goal_manager_with_llm()