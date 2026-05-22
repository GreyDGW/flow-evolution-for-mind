import sqlite3
from datetime import datetime

def clean_and_reimport_goals():
    print("=" * 70)
    print("🧹 清理并重新导入目标数据")
    print("=" * 70)
    
    conn = sqlite3.connect('flow_ecosystem.db')
    cursor = conn.cursor()
    
    # 备份原表
    cursor.execute("DROP TABLE IF EXISTS goals_backup")
    cursor.execute("CREATE TABLE goals_backup AS SELECT * FROM goals")
    print("✅ 已备份原goals表")
    
    # 删除所有目标记录
    cursor.execute("DELETE FROM goals")
    print("✅ 已清空goals表")
    
    # 从sessions表读取用户消息
    cursor.execute("""
        SELECT content_text, timestamp 
        FROM sessions 
        WHERE role='user' 
          AND content_text IS NOT NULL 
          AND content_text != ''
          AND content_text NOT LIKE '%[Bootstrap%'
          AND content_text NOT LIKE '%media attached%'
        ORDER BY timestamp
    """)
    user_messages = cursor.fetchall()
    
    print(f"\n📊 找到 {len(user_messages)} 条有效用户消息")
    
    # 定义有效目标的模式
    goal_patterns = [
        r'(帮我|我想|我要|我需要)([^。！？；]{6,})',
        r'(完成|实现|达成|解决|学习|掌握|开发|创建|写|做)([^。！？；]{6,})',
        r'(修改|调整|优化|改进)([^。！？；]{6,})',
        r'(分析|设计|规划)([^。！？；]{6,})',
    ]
    
    import re
    
    added_goals = []
    seen = set()
    
    for content, timestamp in user_messages:
        # 跳过太短或无效的消息
        if len(content) < 10:
            continue
        
        # 尝试匹配目标模式
        matched = False
        for pattern in goal_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                goal_text = match.group(1) + match.group(2).strip()
                goal_text = re.sub(r'[。！？；,，"\']+$', '', goal_text)
                
                # 过滤规则
                if len(goal_text) < 8:
                    continue
                if goal_text in seen:
                    continue
                if any(kw in goal_text for kw in ['json', 'JSON', '```', '#']):
                    continue
                if len(goal_text) > 200:
                    goal_text = goal_text[:200]
                
                # 判断时间跨度
                time_horizon = 'short'
                text_lower = goal_text.lower()
                if '本周' in text_lower or '这周' in text_lower:
                    time_horizon = 'medium'
                elif '长期' in text_lower or '目标' in text_lower or '愿景' in text_lower:
                    time_horizon = 'long'
                
                added_goals.append({
                    'declared_text': goal_text,
                    'declared_at': timestamp,
                    'time_horizon': time_horizon
                })
                seen.add(goal_text)
                matched = True
        
        # 如果没有匹配到模式，但消息看起来像目标
        if not matched and len(content) >= 15:
            # 检查是否包含动作词
            action_words = ['学习', '创建', '完成', '修改', '开发', '设计', '实现', '做']
            if any(word in content for word in action_words):
                goal_text = re.sub(r'[。！？；,，"\']+$', '', content.strip())
                if goal_text not in seen and len(goal_text) <= 200:
                    time_horizon = 'short'
                    text_lower = goal_text.lower()
                    if '本周' in text_lower:
                        time_horizon = 'medium'
                    elif '长期' in text_lower:
                        time_horizon = 'long'
                    
                    added_goals.append({
                        'declared_text': goal_text,
                        'declared_at': timestamp,
                        'time_horizon': time_horizon
                    })
                    seen.add(goal_text)
    
    # 插入新目标
    for goal in added_goals:
        cursor.execute("""
            INSERT INTO goals (declared_text, declared_at, status, drift_score, last_mentioned, complexity_score, time_horizon, completion_score)
            VALUES (?, ?, 'active', 0.0, ?, 0.0, ?, 0.0)
        """, (goal['declared_text'], goal['declared_at'], datetime.now(), goal['time_horizon']))
    
    conn.commit()
    print(f"\n✅ 已导入 {len(added_goals)} 条高质量目标")
    
    # 统计
    cursor.execute("SELECT COUNT(*) FROM goals WHERE status='active'")
    active_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT time_horizon, COUNT(*) FROM goals GROUP BY time_horizon")
    horizon_stats = cursor.fetchall()
    
    print(f"\n📊 数据库状态：")
    print(f"  活跃目标总数: {active_count}")
    for horizon, count in horizon_stats:
        print(f"  {horizon}: {count} 个")
    
    # 显示部分目标
    cursor.execute("SELECT id, declared_text, time_horizon FROM goals LIMIT 10")
    print("\n🎯 前10条目标：")
    for row in cursor.fetchall():
        print(f"  [{row[2]}] {row[1]}")
    
    conn.close()
    print("\n✅ 数据库清理完成！")

if __name__ == '__main__':
    clean_and_reimport_goals()