#!/usr/bin/env python3
"""测试分析并保存 22e1e24c session"""

import sys
sys.path.insert(0, '.')
import sqlite3

from plugin.session_analyzer import SessionAnalyzer
from plugin.llm_client import DeepSeekLLMClient

DB_PATH = 'data/flow_ecosystem.db'
SESSION_ID = '22e1e24c-f088-497b-af5b-1cd3a0812056#2'

# 读取消息
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute('''
    SELECT role, content_text, timestamp
    FROM sessions
    WHERE session_id = ?
    ORDER BY timestamp
''', (SESSION_ID,))
msgs = [{'role': r['role'], 'content_text': r['content_text'], 'timestamp': r['timestamp']} for r in c.fetchall()]
conn.close()

print(f'📊 共 {len(msgs)} 条消息')

llm = DeepSeekLLMClient()
analyzer = SessionAnalyzer(llm_client=llm)

results = analyzer.analyze_batch(msgs, SESSION_ID, gap_minutes=15)
print(f'📊 分析结果数量: {len(results)}')

INSERT_SQL = """
INSERT OR REPLACE INTO session_analyses (
    session_id, goal_alignment, closure_index, flow_depth, cognition_growth,
    goal_evidence, closure_evidence, flow_evidence, cognition_evidence,
    llm_model, llm_latency_ms, prompt_version,
    portrait_label, portrait_description, portrait_suggestion, portrait_rule_insight,
    style_pace, style_depth, style_tone
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

for r in results:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(INSERT_SQL, (
        SESSION_ID,  # 使用实际的 session_id
        r.goal_alignment, r.closure_index, r.flow_depth, r.cognition_growth,
        r.goal_evidence, r.closure_evidence, r.flow_evidence, r.cognition_evidence,
        'deepseek-chat', 0, 'v1',
        r.portrait_label, r.portrait_description, r.portrait_suggestion, r.portrait_rule_insight,
        r.style_pace, r.style_depth, r.style_tone
    ))
    conn.commit()
    conn.close()

    print(f'  ✅ 4维: {r.goal_alignment}/{r.closure_index}/{r.flow_depth}/{r.cognition_growth}')
    print(f'     🎭 {r.portrait_label}')
    print(f'     💾 已保存 → {SESSION_ID[:40]}...')

# 验证保存结果
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute('SELECT session_id, goal_alignment, portrait_label FROM session_analyses WHERE session_id = ?', (SESSION_ID,))
row = c.fetchone()
if row:
    print(f'\n✅ 验证成功: {row[0][:40]}... → {row[1]}/{row[2]}')
else:
    print(f'\n❌ 验证失败')
conn.close()
