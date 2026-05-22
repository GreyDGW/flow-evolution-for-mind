#!/usr/bin/env python3
"""只从用户消息中提取真实目标 - 简化版"""

from datetime import datetime
import re
import sqlite3

def clean_message(content: str) -> str:
    content = re.sub(r'^\[.*?\]\s*', '', content)
    content = re.sub(r'ou_[a-f0-9]+:\s*', '', content)
    content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
    content = re.sub(r'\n+', ' ', content)
    return content.strip()

def is_valid_goal(text: str) -> bool:
    text = text.strip()
    
    if len(text) < 6 or len(text) > 120:
        return False
    
    if text.startswith('{') and text.endswith('}'):
        return False
    
    system_keywords = ['FlowGuard', 'cron', 'Startup', 'execute', 'session', 'memory']
    if any(kw.lower() in text.lower() for kw in system_keywords):
        return False
    
    question_words = ['是什么', '什么是', '什么叫', '为什么', '怎么样', '如何', '谁', '哪里', '何时']
    has_question = any(q in text for q in question_words)
    if has_question:
        return False
    
    if '|' in text and text.count('|') >= 2:
        return False
    
    chinese_chars = re.findall(r'[\u4e00-\u9fa5]', text)
    if len(chinese_chars) < 2:
        return False
    
    return True

def extract_goals_from_text(text: str) -> list:
    goals = []
    seen = set()
    
    patterns = [
        r'(帮我)(\s+[^\n。！？；]{6,100})',
        r'(我想|我要|我需要|我打算|我希望)(\s+[^\n。！？；]{6,100})',
        r'(完成|实现|达成|解决|学习|掌握|开发|创建|更新|设计|构建|优化)(\s+[^\n。！？；]{6,100})',
        r'(把)(\s+[^\n。！？；]{6,100})(共享|修改|更新)',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            if len(match.groups()) >= 2:
                goal_text = match.group(2).strip()
                goal_text = re.sub(r'[。！？；,，\-]$', '', goal_text)
                
                full_text = match.group(1) + match.group(2)
                if goal_text and full_text not in seen and is_valid_goal(goal_text):
                    goals.append(full_text)
                    seen.add(full_text)
    
    if not goals:
        bangwo_match = re.search(r'帮我([^\n。！？；]{6,100})', text)
        if bangwo_match:
            goal_text = bangwo_match.group(1).strip()
            goal_text = re.sub(r'[。！？；,，\-]$', '', goal_text)
            if is_valid_goal(goal_text):
                goals.append("帮我" + goal_text)
    
    return goals

def classify_time_horizon(text: str) -> str:
    text_lower = text.lower()
    if any(kw in text_lower for kw in ['今天', '今日', '立即', '马上', '现在']):
        return 'short'
    if any(kw in text_lower for kw in ['本周', '这周', '下周', '本月', '项目']):
        return 'medium'
    if any(kw in text_lower for kw in ['长期', '目标', '愿景', '成为', '学会', '掌握', '年度', '人生']):
        return 'long'
    return 'short'

def main():
    print("=" * 70)
    print("🎯 只从用户消息中提取真实目标（简化版）")
    print("=" * 70)
    
    conn = sqlite3.connect('flow_ecosystem.db')
    cursor = conn.cursor()
    
    print("\n🔍 查询用户消息（role='user'）...")
    cursor.execute("""
        SELECT id, content_text, timestamp 
        FROM sessions 
        WHERE role='user' AND content_text IS NOT NULL AND content_text != ''
        ORDER BY timestamp DESC 
        LIMIT 100
    """)
    user_messages = cursor.fetchall()
    
    print(f"找到 {len(user_messages)} 条用户消息")
    
    print("\n📝 提取目标...")
    all_goals = []
    for msg_id, content, timestamp in user_messages:
        cleaned_content = clean_message(content)
        if not cleaned_content:
            continue
        
        goals = extract_goals_from_text(cleaned_content)
        for goal_text in goals:
            all_goals.append({
                'text': goal_text,
                'msg_id': msg_id,
                'timestamp': timestamp,
                'horizon': classify_time_horizon(goal_text)
            })
    
    print(f"从用户消息中提取到 {len(all_goals)} 个有效目标")
    
    if all_goals:
        print("\n📋 提取到的用户目标：")
        for i, goal in enumerate(all_goals[:10], 1):
            horizon_label = {'short': '短期', 'medium': '中期', 'long': '长期'}[goal['horizon']]
            print(f"\n{i}. [{horizon_label}] {goal['text']}")
            print(f"   来源: 消息ID {goal['msg_id']}")
        
        print("\n💾 保存到数据库...")
        saved_count = 0
        for goal in all_goals:
            cursor.execute("""
                SELECT id FROM goals 
                WHERE declared_text LIKE ? AND status='active'
            """, (f'%{goal["text"][:30]}%',))
            
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO goals (declared_text, declared_at, status, drift_score, 
                                      last_mentioned, complexity_score, time_horizon, completion_score)
                    VALUES (?, ?, 'active', 0.0, ?, 0.0, ?, 0.0)
                """, (goal['text'], goal['timestamp'], datetime.now(), goal['horizon']))
                saved_count += 1
        
        conn.commit()
        print(f"成功保存 {saved_count} 个新目标")
    else:
        print("\n⚠️ 未提取到有效目标")
        print("\n🔍 调试：显示清理后的消息")
        for msg_id, content, timestamp in user_messages[:10]:
            cleaned = clean_message(content)
            print(f"\n消息ID {msg_id}: {cleaned[:120]}")
    
    conn.close()
    print("\n✅ 完成！")

if __name__ == '__main__':
    main()