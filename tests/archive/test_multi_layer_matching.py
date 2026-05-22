from src.openclaw_flow_plugin.core.goal_manager import GoalManager

def test_multi_layer_matching():
    print("=" * 70)
    print("🧠 多层匹配器 - 真实数据测试")
    print("=" * 70)
    
    # 初始化目标管理器
    gm = GoalManager(db_path='flow_ecosystem.db', use_llm=False)
    
    # 获取活跃目标
    active_goals = gm.get_active_goals()
    print(f"\n📊 数据库中活跃目标数: {len(active_goals)}")
    
    if len(active_goals) == 0:
        print("⚠️ 没有活跃目标，请先添加目标")
        return
    
    # 显示部分活跃目标
    print("\n🎯 活跃目标列表:")
    for i, goal in enumerate(active_goals[:5]):
        print(f"  {i+1}. [{goal.time_horizon}] {goal.declared_text[:50]}...")
    
    # 测试消息列表
    test_messages = [
        '我想学习Python编程',
        '帮我修改flow ecosystem的技能',
        '创建一个个人进化系统',
        '完成API文档',
        '学Pyhton编程',
        '修改flow的配置',
        '了解一下flow ecosystem',
        '做一个进化系统',
        '写代码',
        '这个怎么做'
    ]
    
    print("\n" + "=" * 70)
    print("🔍 匹配测试结果")
    print("=" * 70)
    
    for msg in test_messages:
        is_match, goal, score = gm.find_matching_goal(msg)
        if is_match:
            print(f"✅ [{score:.2f}] '{msg}' -> '{goal.declared_text[:50]}...'")
        else:
            print(f"❌ '{msg}' -> 未匹配")
    
    # 测试批量匹配
    print("\n" + "=" * 70)
    print("📈 批量匹配测试")
    print("=" * 70)
    
    message = "学习编程"
    matches = gm.find_top_matching_goals(message, top_n=3)
    print(f"查询: '{message}'")
    for goal, score in matches:
        print(f"  - [{score:.2f}] {goal.declared_text}")
    
    # 测试阈值调整
    print("\n" + "=" * 70)
    print("⚙️ 阈值调整测试")
    print("=" * 70)
    
    original_threshold = gm.matcher.similarity_threshold
    print(f"原始相似度阈值: {original_threshold}")
    
    # 降低阈值（更宽松）
    gm.update_matcher_thresholds(similarity_threshold=0.2)
    is_match, goal, score = gm.find_matching_goal("写代码")
    print(f"阈值=0.2时: '写代码' -> {'匹配' if is_match else '未匹配'} (分数: {score:.2f})")
    
    # 恢复原阈值
    gm.update_matcher_thresholds(similarity_threshold=original_threshold)
    
    gm.close()
    print("\n✅ 测试完成！")

if __name__ == '__main__':
    test_multi_layer_matching()