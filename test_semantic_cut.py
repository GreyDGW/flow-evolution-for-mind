#!/usr/bin/env python3
"""测试 SemanticSessionCutter 对历史数据的切割效果"""

import sqlite3
import sys
sys.path.insert(0, '.')

from plugin.session.session_cutter import SemanticSessionCutter

DB_PATH = 'data/flow_ecosystem.db'

# 获取 4月21日所有消息
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute("""
    SELECT role, content_text, timestamp 
    FROM sessions 
    WHERE date(timestamp) = '2026-04-21'
      AND role IN ('user', 'assistant')
    ORDER BY timestamp
""")
msgs = [{'role': r['role'], 'content': r['content_text'] or '', 'timestamp': r['timestamp']} for r in c.fetchall()]
conn.close()

print(f"📊 4月21日有效对话消息: {len(msgs)} 条")

# 使用 SemanticSessionCutter 切割
cutter = SemanticSessionCutter()
sessions = cutter.cut_sessions(msgs, threshold=0.15)

print(f"\n🔪 SemanticSessionCutter 切割结果 (threshold=0.15):")
print(f"   切割后 session 数量: {len(sessions)}")
for i, session in enumerate(sessions, 1):
    print(f"   Session {i}: {len(session)} 条消息")

stats = cutter.get_stats(sessions)
print(f"\n📈 统计信息:")
print(f"   总消息数: {stats['total_messages']}")
print(f"   Session 数: {stats['session_count']}")
print(f"   平均每 session: {stats['avg_session_length']:.1f} 条")
print(f"   阈值: {stats['threshold']}")
