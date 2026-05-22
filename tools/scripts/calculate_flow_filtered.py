import sqlite3
import math
from datetime import datetime

db_path = '/Users/duguowei/Desktop/skill相关文档/openclaw_flow_plugin/flow_ecosystem.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('''
    SELECT session_id, content_text
    FROM sessions
    WHERE role = 'user'
    GROUP BY session_id
    HAVING COUNT(*) > 1
''')
sessions = cursor.fetchall()
conn.close()

cron_sessions = set()
normal_sessions = []

for session_id, content in sessions:
    if 'cron' in content.lower() or 'FlowGuard' in content or '定时任务' in content:
        cron_sessions.add(session_id)
    else:
        normal_sessions.append(session_id)

print(f'总会话数: {len(sessions)}')
print(f'Cron任务会话: {len(cron_sessions)}')
print(f'用户会话: {len(normal_sessions)}')
print()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

flow_depths = []
for session_id in normal_sessions:
    cursor.execute('''
        SELECT role, content_text, timestamp
        FROM sessions
        WHERE session_id = ?
        ORDER BY timestamp
    ''', (session_id,))
    rows = cursor.fetchall()
    
    if not rows:
        continue
    
    total_quality = 0
    message_count = 0
    
    for role, content, timestamp in rows:
        if role == 'user':
            logic_depth = content.count('因为') + content.count('所以') + content.count('因此') + content.count('如果') + content.count('那么')
            orderliness = content.count('。') + content.count('？') + content.count('！')
            progressiveness = content.count('接下来') + content.count('然后') + content.count('继续')
            judgment_vector = content.count('确定') + content.count('明确') + content.count('肯定')
            goal_alignment = content.count('目标') + content.count('完成') + content.count('实现')
            
            quality = (min(logic_depth, 3) + min(orderliness // 2, 3) + min(progressiveness, 3) + min(judgment_vector, 3) + min(goal_alignment, 3)) / 15
            total_quality += quality
            message_count += 1
    
    if message_count > 0:
        avg_quality = total_quality / message_count
        flow_depths.append(avg_quality)

conn.close()

if flow_depths:
    print('排除Cron任务后的计算结果：')
    print(f'平均心流深度: {sum(flow_depths)/len(flow_depths)*100:.1f}%')
    print(f'最高心流深度: {max(flow_depths)*100:.1f}%')
    print(f'最低心流深度: {min(flow_depths)*100:.1f}%')
    print(f'分析会话数: {len(flow_depths)}')