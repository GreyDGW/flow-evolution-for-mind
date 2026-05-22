#!/usr/bin/env python3
"""目标提取算法测试 - 新手入门体验"""

import sqlite3
from datetime import datetime

def test_goal_extraction():
    print("=" * 60)
    print("🎯 目标提取算法测试")
    print("=" * 60)
    
    # 连接数据库
    conn = sqlite3.connect('flow_ecosystem.db')
    cursor = conn.cursor()
    
    # 获取5条用户消息来测试
    cursor.execute("""
        SELECT id, content_text, timestamp 
        FROM sessions 
        WHERE role='user' AND content_text IS NOT NULL AND content_text != '' 
        ORDER BY timestamp DESC 
        LIMIT 5
    """)
    
    user_messages = cursor.fetchall()
    conn.close()
    
    print(f"\n从数据库中找到了 {len(user_messages)} 条用户消息\n")
    
    # 目标提取规则（简化版）
    goal_patterns = [
        r'(我想|我要|我需要|我打算|目标是|目的是|任务是|计划)(?:\s+)?(.+?)(?:[。！？；\n]|$)',
        r'(完成|实现|达成|解决|学习|掌握|开发|创建)(?:\s+)?(.+?)(?:[。！？；\n]|$)',
    ]
    
    import re
    
    for msg_id, content, timestamp in user_messages:
        print(f"📝 用户消息 [{msg_id}]")
        print(f"时间: {timestamp}")
        print(f"内容: {content[:100]}{'...' if len(content) > 100 else ''}")
        
        # 提取目标
        found_goals = []
        for pattern in goal_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                goal_text = match.group(1) + match.group(2)
                if len(goal_text) > 8:  # 过滤太短的
                    found_goals.append(goal_text.strip())
        
        if found_goals:
            print("🎯 提取到的目标:")
            for i, goal in enumerate(found_goals, 1):
                print(f"   {i}. {goal}")
        else:
            print("⚠️ 未提取到明确目标")
        
        print("-" * 60)

if __name__ == '__main__':
    test_goal_extraction()