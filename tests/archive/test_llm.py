from llm_manager import LLMManager

def test_llm_integration():
    print("=" * 70)
    print("🧠 LLM管理器测试（模拟模式）")
    print("=" * 70)
    
    llm = LLMManager()
    
    print("\n1️⃣ 测试目标提取")
    user_message = "我想学习Python编程，这周完成基础语法学习"
    result = llm.extract_goals(user_message)
    print(f"用户消息: {user_message}")
    print(f"提取的目标: {result}")
    
    print("\n2️⃣ 测试隐含目标提取")
    user_message = "帮我修改flow ecosystem的技能"
    result = llm.extract_goals(user_message)
    print(f"用户消息: {user_message}")
    print(f"提取的目标: {result}")
    
    print("\n3️⃣ 测试闭环分析")
    conversation = """
    用户：我计划今天完成API文档。
    用户：文档已经写完了，正在检查。
    用户：发现了几个错误，已经修正了。
    """
    result = llm.analyze_closure(conversation)
    print(f"闭环分析结果: {result}")
    
    print("\n✅ 测试完成！")
    print("\n💡 提示：当网络恢复后，只需将llm.use_mock设置为False即可使用真实的Phi-2模型")

if __name__ == '__main__':
    test_llm_integration()