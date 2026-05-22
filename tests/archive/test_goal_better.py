#!/usr/bin/env python3
"""找真正有目标的用户消息"""

import sqlite3

def find_goal_messages():
    conn = sqlite3.connect('flow_ecosystem.db')
    cursor = conn.cursor()
    
    # 搜索包含目标关键词的用户消息
    cursor.execute("""
        SELECT id, content_text, timestamp 
        FROM sessions 
        WHERE role='user' AND content_text IS NOT NULL AND content_text != ''
        AND (content_text LIKE '%我想%' OR content_text LIKE '%我要%' OR 
             content_text LIKE '%目标%' OR content_text LIKE '%任务%' OR
             content_text LIKE '%完成%' OR content_text LIKE '%学习%' OR
             content_text LIKE '%创建%' OR content_text LIKE '%开发%')
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    
    messages = cursor.fetchall()
    conn.close()
    
    print(f"找到 {len(messages)} 条包含目标关键词的消息\n")
    
    for msg_id, content, timestamp in messages:
        print(f"📌 消息 [{msg_id}]")
        print(f"时间: {timestamp}")
        print(f"内容: {content[:150]}{'...' if len(content) > 150 else ''}\n")

if __name__ == '__main__':
    find_goal_messages()