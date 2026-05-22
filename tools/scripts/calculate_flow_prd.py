import sqlite3
import math
from datetime import datetime

db_path = '/Users/duguowei/Desktop/skill相关文档/openclaw_flow_plugin/flow_ecosystem.db'

def is_cron_session(content):
    cron_keywords = ['cron', 'FlowGuard', '定时任务', '健康检查', 'registry.json']
    return any(kw.lower() in content.lower() for kw in cron_keywords)

def analyze_quality(content):
    logic_depth = 0
    if '因为' in content or '所以' in content or '因此' in content:
        logic_depth += 1
    if '如果' in content or '那么' in content or '假设' in content:
        logic_depth += 1
    if '推理' in content or '证明' in content or '推导' in content:
        logic_depth += 1
    logic_depth = min(logic_depth, 3)
    
    orderliness = content.count('。') + content.count('？') + content.count('！')
    orderliness = min(orderliness, 3)
    
    progressiveness = 0
    if '接下来' in content or '然后' in content:
        progressiveness += 1
    if '继续' in content or '深入' in content:
        progressiveness += 1
    if '展开' in content or '进一步' in content:
        progressiveness += 1
    progressiveness = min(progressiveness, 3)
    
    judgment_vector = 0
    if '确定' in content or '明确' in content:
        judgment_vector += 1
    if '肯定' in content or '同意' in content:
        judgment_vector += 1
    if '支持' in content:
        judgment_vector += 1
    judgment_vector = min(judgment_vector, 3)
    
    goal_alignment = 0
    if '目标' in content or '完成' in content:
        goal_alignment += 1
    if '实现' in content or '达成' in content:
        goal_alignment += 1
    if '解决' in content or '任务' in content:
        goal_alignment += 1
    goal_alignment = min(goal_alignment, 3)
    
    total = (logic_depth + orderliness + progressiveness + judgment_vector + goal_alignment) / 15
    return total

def calculate_signal_gain(content):
    rebel = 0
    if '不对' in content or '错误' in content or '不是' in content:
        rebel += 1
    if '不同意' in content or '应该这样' in content or '我觉得' in content:
        rebel += 1
    rebel = min(rebel, 3)
    
    question_count = content.count('？') + content.count('吗') + content.count('为什么')
    question = min(question_count, 3)
    
    correct = 0
    if '修正' in content or '更正' in content:
        correct += 1
    if '应该是' in content or '重新' in content:
        correct += 1
    correct = min(correct, 3)
    
    meta = 0
    if '思考' in content or '反思' in content:
        meta += 1
    if '总结' in content or '回顾' in content or '分析' in content:
        meta += 1
    meta = min(meta, 3)
    
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
    total_signal = 0
    
    for _, content, _ in user_messages:
        total_quality += analyze_quality(content)
        total_signal += calculate_signal_gain(content)
    
    avg_quality = total_quality / len(user_messages)
    avg_signal = total_signal / len(user_messages)
    
    fragment_index = min(avg_quality * avg_signal, 1.0)
    time_coeff = calculate_time_coefficient(duration_min)
    flow_depth = fragment_index * time_coeff
    
    flow_results.append({
        'session_id': session_id,
        'flow_depth': flow_depth,
        'quality': avg_quality,
        'signal': avg_signal,
        'time_coeff': time_coeff,
        'duration': duration_min
    })

conn.close()

if flow_results:
    depths = [r['flow_depth'] for r in flow_results]
    qualities = [r['quality'] for r in flow_results]
    times = [r['time_coeff'] for r in flow_results]
    
    print('【排除Cron任务后的PRD完整算法计算】')
    print('='*50)
    print(f'分析会话数: {len(flow_results)}')
    print()
    print(f'平均心流深度: {sum(depths)/len(depths)*100:.1f}%')
    print(f'平均质量分: {sum(qualities)/len(qualities)*100:.1f}%')
    print(f'平均时间系数: {sum(times)/len(times)*100:.1f}%')
    print()
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
    
    print()
    print('【详细数据（前5个高质量会话）】')
    sorted_results = sorted(flow_results, key=lambda x: -x['flow_depth'])[:5]
    for r in sorted_results:
        print(f'会话: {r["session_id"][:20]}...')
        print(f'  心流深度: {r["flow_depth"]*100:.1f}%')
        print(f'  质量分: {r["quality"]*100:.1f}%')
        print(f'  信号增益: {r["signal"]:.2f}')
        print(f'  时间系数: {r["time_coeff"]*100:.1f}%')
        print(f'  时长: {r["duration"]:.1f}分钟')
        print()