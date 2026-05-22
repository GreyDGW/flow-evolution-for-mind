import sqlite3
conn = sqlite3.connect('data/flow_ecosystem.db')
c = conn.cursor()

print("=== 找出未分析的4/20 session ===\n")

# 所有4/20的session
c.execute("""
    SELECT DISTINCT session_id, COUNT(*) as msg_cnt
    FROM sessions
    WHERE timestamp >= '2026-04-20' AND timestamp <= '2026-04-20 23:59:59'
    GROUP BY session_id
""")
all_sessions = {r[0]: r[1] for r in c.fetchall()}

# 已分析的4/20 session
c.execute("""
    SELECT DISTINCT session_id
    FROM session_analyses
    WHERE session_id IN (
        SELECT DISTINCT session_id FROM sessions 
        WHERE timestamp >= '2026-04-20' AND timestamp <= '2026-04-20 23:59:59'
    )
""")
analyzed = {r[0] for r in c.fetchall()}

print(f"4/20 总session数: {len(all_sessions)}")
print(f"已分析数: {len(analyzed)}")

missing = set(all_sessions.keys()) - analyzed
print(f"\n❌ 未分析的session ({len(missing)}个):")
for sid in missing:
    print(f"  {sid} | 消息数:{all_sessions[sid]}")

print(f"\n✅ 已分析的session ({len(analyzed)}个):")
for sid in analyzed:
    print(f"  {sid} | 消息数:{all_sessions[sid]}")

conn.close()