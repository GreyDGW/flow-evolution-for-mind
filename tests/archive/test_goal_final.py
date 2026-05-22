#!/usr/bin/env python3
"""目标提取算法 - 真正的用户目标测试"""

import sqlite3
import re

def extract_goals(text):
    """从文本中提取目标"""
    patterns = [
        r'(我想|我要|我需要|我打算)(?:\s+)(.+?)(?:[。！？；\n]|$)',
        r'(目标是|目的是|任务是|计划)(?:\s+)?(.+?)(?:[。！？；\n]|$)',
        r'(完成|实现|达成|解决|学习|掌握|开发|创建|更新)(?:\s+)(.+?)(?:[。！？；\n]|$)',
    ]
    
    goals = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            goal = match.group(1) + match.group(2)
            if len(goal) > 8:
                goals.append(goal.strip())
    return goals

def test_real_goals():
    conn = sqlite3.connect('flow_ecosystem.db')
    cursor = conn.cursor()
    
    # 搜索包含明确目标的消息
    cursor.execute("""
        SELECT id, content_text, timestamp 
        FROM sessions 
        WHERE role='user' AND content_text IS NOT NULL AND content_text != ''
        AND content_text NOT LIKE '%cron%'
        ORDER BY timestamp DESC
        LIMIT 20
    """)
    
    messages = cursor.fetchall()
    conn.close()
    
    print("=" * 70)
    print("🎯 目标提取算法演示")
    print("=" * 70)
    
    success_count = 0
    for msg_id, content, timestamp in messages:
        goals = extract_goals(content)
        if goals:
            success_count += 1
            print(f"\n✅ 消息 [{msg_id}]")
            print(f"时间: {timestamp}")
            print(f"原始文本: {content[:120]}{'...' if len(content) > 120 else ''}")
            print("提取的目标:")
            for i, goal in enumerate(goals, 1):
                print(f"   {i}. {goal}")
    
    print(f"\n🎉 共分析 {len(messages)} 条消息，成功提取 {success_count} 条目标")

if __name__ == '__main__':
    test_real_goals()