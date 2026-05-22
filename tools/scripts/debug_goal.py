from src.openclaw_flow_plugin.core.llm_manager import LLMManager
import sqlite3

print("=== 目标验证调试 ===")
print()

# 查看数据库中的目标
conn = sqlite3.connect('flow_ecosystem.db')
cursor = conn.cursor()

cursor.execute('SELECT id, declared_text FROM goals WHERE status = "active" LIMIT 20')
goals = cursor.fetchall()

print("数据库中的目标:")
for goal_id, text in goals:
    print(f"{goal_id}. {text}")

print()
print("=" * 60)
print()

# 测试验证逻辑
llm = LLMManager()
llm.use_mock = True

test_goal = None
for goal_id, text in goals:
    if "心流程度" in text:
        test_goal = text
        break

if test_goal:
    print(f"测试目标: {test_goal}")
    print()
    
    # 用模拟模式验证
    result = llm.is_valid_goal(test_goal)
    print(f"模拟模式判定: {result}")
    print()
    
    # 分析为什么被误判
    print("=== 验证逻辑分析 ===")
    print(f"目标长度: {len(test_goal)}")
    
    valid_patterns = ["帮我", "我想", "我要", "完成", "创建", "学习", "修改", "实现", "解决", "开发", "分析", "设计", "优化", "检查", "验证", "测试", "研究", "了解", "理解", "搞懂"]
    
    matched = []
    for p in valid_patterns:
        if p in test_goal:
            matched.append(p)
    
    print(f"匹配的关键词: {matched}")
    print(f"是否匹配有效关键词: {len(matched) > 0}")
    print(f"长度大于10: {len(test_goal.strip()) > 10}")
    
    # 检查无效模式
    invalid_patterns = [
        r'^.{1,4}$',
        r'^[一二三四五六七八九十0-9]$',
        r'^\{.*\}$',
        r'^```',
    ]
    
    import re
    is_invalid = any(re.match(p, test_goal.strip()) for p in invalid_patterns)
    print(f"是否匹配无效模式: {is_invalid}")
    
    # 手动计算应该返回什么
    expected = len(matched) > 0 or len(test_goal.strip()) > 10
    print(f"预期判定: {expected}")
else:
    print("未找到心流相关的目标")

conn.close()
