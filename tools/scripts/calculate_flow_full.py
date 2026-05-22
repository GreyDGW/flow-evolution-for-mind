import sqlite3
import math
from datetime import datetime

db_path = '/Users/duguowei/Desktop/skill相关文档/openclaw_flow_plugin/flow_ecosystem.db'

def is_cron_session(content):
    cron_keywords = ['cron', 'FlowGuard', '定时任务', '健康检查', '监控', 'registry.json']
    return any(kw.lower() in content.lower() for kw in cron_keywords)

def analyze_quality(content):
    logic_depth = min(content.count('因为') + content.count('所以') + content.count('因此') + 
                      content.count('如果') + content.count('那么') + content.count('推导'), 3)
    orderliness = min((content.count('。') + content.count('？') + content.count('！')) // 2, 3)
    progressiveness = min(content.count('接下来') + content.count('然后') + content.count('继续') +
                         content.count('深入') + content.count('展开'), 3)
    judgment_vector = min(content.count('确定') + content.count('明确') + content.count('肯定') +
                         content.count('同意'), 3)
    goal_alignment = min(content.count('目标') + content.count('完成') + content.count('实现') +
                        content.count('达成') + content.count('解决'), 3)
    
    total = (logic_depth + orderliness + progressiveness + judgment_vector + goal_alignment) / 15
    return total

def calculate_signal_gain(content):
    rebel = min(content.count('不对') + content.count('错误') + content.count('不是') +
               content.count('不同意') + content.count('应该这样'), 3)
    question = min(content.count('？') + content.count('吗') + content.count('为什么'), 3)
    correct = min(content.count('修正') + content.count('更正') + content.count('应该是'), 3)
    meta = min(content.count('思考') + content.count('反思') + content.count('总结') +
              content.count('回顾'), 3)
    
    total = (rebel + question + correct + meta) / 12
    signal_gain = 1.0 + total * 0.6
    if rebel == 3:
        signal_gain += 0.2
    return min(signal_gain, 1.8)

def calculate_time_coefficient(duration_min):
    if duration_min <= 0:
        return 0.0
    max_minutes = 180
    return min(math.log(1 + duration_min / 5) / math.log(1 + max_minutes / 5), 1.0)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute('''
    SELECT DISTINCT session_id
    FROM sessions
    WHERE role = 'user'
''')
all_sessions = [row[0] for row in cursor.fetchall()]

user_sessions = []
cron_count = 0

for session_id in all_sessions:
    cursor.execute('''
        SELECT content_text
        FROM sessions
        WHERE session_id = ? AND role = 'user'
        LIMIT 1
    ''', (session_id,))
    row = cursor.fetchone()
    if row and not is_cron_session(row[0]):
        user_sessions.append(session_id)
    else:
        cron_count += 1

print(f'总会话数: {len(all_sessions)}')
print(f'Cron任务会话: {cron_count}')
print(f'用户会话: {len(user_sessions)}')
print()

flow_results = []

for session_id in user_sessions:
    cursor.execute('''
        SELECT role, content_text, timestamp
        FROM sessions
        WHERE session_id = ?
        ORDER BY timestamp
    ''', (session_id,))
    rows = cursor.fetchall()
    
    if not rows:
        continue
    
    user_messages = [r for r in rows if r[0] == 'user']
    if not user_messages:
        continue
    
    first_time = datetime.fromisoformat(user_messages[0][2].replace('Z', '+00:00'))
    last_time = datetime.fromisoformat(user_messages[-1][2].replace('Z', '+00:00'))
    duration_min = (last_time - first_time).total_seconds() / 60
    
    total_quality = 0
    total_signal_gain = 0
    
    for _, content, _ in user_messages:
        total_quality += analyze_quality(content)
        total_signal_gain += calculate_signal_gain(content)
    
    avg_quality = total_quality / len(user_messages)
    avg_signal = total_signal_gain / len(user_messages)
    
    fragment_index = min(avg_quality * avg_signal, 1.0)
    time_coeff = calculate_time_coefficient(duration_min)
    flow_depth = fragment_index * time_coeff
    
    flow_results.append({
        'session_id': session_id,
        'flow_depth': flow_depth,
        'duration_min': duration_min,
        'message_count': len(user_messages),
        'quality': avg_quality,
        'signal_gain': avg_signal,
        'time_coeff': time_coeff
    })

conn.close()

if flow_results:
    depths = [r['flow_depth'] for r in flow_results]
    print('【排除Cron任务后的PRD完整算法计算】')
    print('-'*50)
    print(f'分析会话数: {len(flow_results)}')
    print(f'平均心流深度: {sum(depths)/len(depths)*100:.1f}%')
    print(f'最高心流深度: {max(depths)*100:.1f}%')
    print(f'最低心流深度: {min(depths)*100:.1f}%')
    print()
    
    print('【心流等级分布】')
    levels = {'high': 0, 'medium': 0, 'low': 0, 'critical': 0}
    for r in flow_results:
        d = r['flow_depth']
        if d >= 0.75:
            levels['high'] += 1
        elif d >= 0.5:
            levels['medium'] += 1
        elif d >= 0.25:
            levels['low'] += 1
        else:
            levels['critical'] += 1
    
    for level, count in levels.items():
        print(f'  {level}: {count} ({count/len(flow_results)*100:.1f}%)')