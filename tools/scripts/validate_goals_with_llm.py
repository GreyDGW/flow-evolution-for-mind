import sqlite3
import sys
sys.path.insert(0, '/Users/duguowei/Desktop/skill相关文档/openclaw_flow_plugin/src')

from openclaw_flow_plugin.core.llm_manager import LLMManager

def validate_all_goals():
    conn = sqlite3.connect('/Users/duguowei/Desktop/skill相关文档/openclaw_flow_plugin/flow_ecosystem.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, declared_text FROM goals')
    all_goals = cursor.fetchall()
    
    print(f"总目标数量: {len(all_goals)}")
    
    llm = LLMManager()
    llm.use_mock = False
    
    valid_count = 0
    invalid_count = 0
    valid_goals = []
    invalid_goals = []
    
    print("\n开始使用LLM验证目标...")
    
    for i, (goal_id, declared_text) in enumerate(all_goals, 1):
        try:
            is_valid = llm.is_valid_goal(declared_text)
            
            if is_valid:
                valid_count += 1
                valid_goals.append((goal_id, declared_text))
            else:
                invalid_count += 1
                invalid_goals.append((goal_id, declared_text))
            
            if i % 10 == 0:
                print(f"已验证: {i}/{len(all_goals)} | 有效: {valid_count} | 无效: {invalid_count}")
                
        except Exception as e:
            print(f"验证目标ID {goal_id} 时出错: {e}")
            invalid_count += 1
            invalid_goals.append((goal_id, declared_text))
    
    print("\n" + "="*60)
    print(f"验证完成!")
    print(f"总目标数: {len(all_goals)}")
    print(f"有效目标: {valid_count} ({(valid_count/len(all_goals)*100):.1f}%)")
    print(f"无效目标: {invalid_count} ({(invalid_count/len(all_goals)*100):.1f}%)")
    print("="*60)
    
    print("\n无效目标示例:")
    for goal_id, text in invalid_goals[:10]:
        print(f"  ID {goal_id}: {text[:60]}...")
    
    print("\n有效目标示例:")
    for goal_id, text in valid_goals[:10]:
        print(f"  ID {goal_id}: {text[:60]}...")
    
    conn.close()
    
    return {
        'total': len(all_goals),
        'valid': valid_count,
        'invalid': invalid_count,
        'valid_goals': valid_goals,
        'invalid_goals': invalid_goals
    }

if __name__ == '__main__':
    result = validate_all_goals()
