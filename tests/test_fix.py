import sys
sys.path.insert(0, '.')
import path_setup
import sqlite3
from plugin.session_analyzer import SessionAnalyzer

conn = sqlite3.connect('data/flow_ecosystem.db')
c = conn.cursor()

c.execute('''
    SELECT content_text, thinking_text, tool_call_text, role, timestamp
    FROM sessions
    WHERE session_id = "d7387af7-18c7-4825-937b-c7c209a5b080"
    ORDER BY timestamp
''')
rows = c.fetchall()
conn.close()

msgs = []
for ct, tt, tct, role, ts in rows:
    msg = {
        'role': role,
        'content_text': ct,
        'thinking_text': tt,
        'tool_call_text': tct,
        'timestamp': str(ts)
    }
    msgs.append(msg)

print('=== 修复后的 _format_conversation 输出 ===')
analyzer = SessionAnalyzer.__new__(SessionAnalyzer)
analyzer.llm_client = None

result = analyzer._format_conversation(msgs)
lines = result.split('\n')
print(f'总行数: {len(lines)}')
for i, line in enumerate(lines[:5], 1):
    print(f'[{i}] {line[:80]}')
if len(lines) > 5:
    print(f'... 共 {len(lines)} 行')
