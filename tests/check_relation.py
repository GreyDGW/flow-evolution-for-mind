import sqlite3

conn = sqlite3.connect('data/flow_ecosystem.db')
c = conn.cursor()

# 1. semantic_session_id 分布
c.execute("SELECT COUNT(DISTINCT semantic_session_id) FROM sessions WHERE semantic_session_id IS NOT NULL")
distinct_semantic = c.fetchone()[0]
print("sessions 关联到 %d 个不同的 semantic_session_id" % distinct_semantic)

# 2. 每个 semantic_session_id 有多少条消息
c.execute("""
    SELECT semantic_session_id, COUNT(*) as cnt
    FROM sessions
    WHERE semantic_session_id IS NOT NULL AND role IN ('user', 'assistant')
    GROUP BY semantic_session_id
    ORDER BY cnt DESC
    LIMIT 10
""")
print("\n消息数最多的10个语义会话:")
for sid, cnt in c.fetchall():
    print("  %s: %d 条消息" % (sid[:20], cnt))

# 3. semantic_sessions 表当前有多少条
c.execute("SELECT COUNT(*) FROM semantic_sessions")
print("\nsemantic_sessions 当前: %d 条" % c.fetchone()[0])

# 4. 检查是否有未关联的 sessions（semantic_session_id 为 NULL）
c.execute("SELECT COUNT(*) FROM sessions WHERE semantic_session_id IS NULL AND role IN ('user', 'assistant')")
orphan = c.fetchone()[0]
print("未关联到 semantic_session 的消息: %d 条" % orphan)

# 5. 查看一个 semantic_session 的完整对话
c.execute("""
    SELECT role, content_text, timestamp
    FROM sessions
    WHERE semantic_session_id = (SELECT semantic_session_id FROM sessions WHERE role='user' AND content_text IS NOT NULL LIMIT 1)
    AND role IN ('user', 'assistant')
    ORDER BY timestamp
    LIMIT 10
""")
print("\n示例对话（第一个语义会话）:")
for role, content, ts in c.fetchall():
    text = str(content)[:80] if content else "(空)"
    print("  [%s] %s: %s" % (role[:3], ts[-8:], text))

conn.close()
