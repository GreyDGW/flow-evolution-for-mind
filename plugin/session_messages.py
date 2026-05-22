"""
从 sessions 表读取消息，组装成 SessionAnalyzer 需要的数组
核心规则：
1. 只提取 content_text（排除 thinking_text / tool_call_text）
2. 合并连续 assistant 消息为一条（同一轮回复被切分的情况）
"""
import sqlite3
from typing import List, Dict

def get_session_messages(session_id: str, db_path: str = "data/flow_ecosystem.db") -> List[Dict]:
    """
    按 session_id 读取消息，只提取 content_text，合并连续 assistant
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("""
        SELECT role, content_text, timestamp
        FROM sessions
        WHERE session_id = ?
        ORDER BY timestamp ASC
    """, (session_id,))
    
    rows = c.fetchall()
    conn.close()
    
    # 第一步：过滤空内容
    raw_messages = []
    for row in rows:
        content = (row['content_text'] or '').strip()
        if not content:
            continue
        raw_messages.append({
            'role': row['role'],
            'content': content,
            'timestamp': row['timestamp']
        })
    
    # 第二步：合并连续 assistant
    merged = []
    for msg in raw_messages:
        if msg['role'] == 'assistant' and merged and merged[-1]['role'] == 'assistant':
            merged[-1]['content'] += '\n\n' + msg['content']
        else:
            merged.append(msg)
    
    return merged

def get_all_semantic_session_ids(db_path: str = "data/flow_ecosystem.db") -> List[str]:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT id FROM semantic_sessions ORDER BY start_time DESC")
    rows = [r[0] for r in c.fetchall()]
    conn.close()
    return rows

def get_session_stats(session_id: str, db_path: str = "data/flow_ecosystem.db") -> Dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("""
        SELECT role, content_text
        FROM sessions
        WHERE session_id = ? AND content_text IS NOT NULL AND content_text != ''
        ORDER BY timestamp ASC
    """, (session_id,))
    
    rows = c.fetchall()
    conn.close()
    
    raw_user = sum(1 for r in rows if r['role'] == 'user')
    raw_assistant = sum(1 for r in rows if r['role'] == 'assistant')
    
    merged = get_session_messages(session_id, db_path)
    merged_user = sum(1 for m in merged if m['role'] == 'user')
    merged_assistant = sum(1 for m in merged if m['role'] == 'assistant')
    
    return {
        'session_id': session_id,
        'raw_count': raw_user + raw_assistant,
        'raw_user': raw_user,
        'raw_assistant': raw_assistant,
        'merged_count': len(merged),
        'merged_user': merged_user,
        'merged_assistant': merged_assistant,
        'assistant_merged': raw_assistant - merged_assistant
    }
