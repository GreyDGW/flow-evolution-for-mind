import sqlite3
conn = sqlite3.connect('data/flow_ecosystem.db')
c = conn.cursor()

print("=== 4/20 的 analyses 详情 ===")
c.execute("""
    SELECT sa.id, sa.session_id, sa.prompt_version, 
           sa.created_at, length(sa.goal_evidence) as g_len
    FROM session_analyses sa
    WHERE sa.session_id IN (
        SELECT session_id FROM sessions 
        WHERE timestamp >= '2026-04-20' AND timestamp <= '2026-04-20 23:59:59'
    )
    ORDER BY sa.created_at DESC
""")
rows = c.fetchall()
print(f"\n4/20 分析记录数: {len(rows)}")
for r in rows:
    print(f"  ID={r[0]} | 版本={r[2]} | 创建时间={r[3]} | goal长度={r[4]}")

print("\n=== 所有 analyses 的 created_at 日期分布 ===")
c.execute("""
    SELECT DATE(created_at) as date, COUNT(*) as cnt
    FROM session_analyses
    GROUP BY DATE(created_at)
    ORDER BY date
""")
print("\nanalyses 创建日期分布:")
for row in c.fetchall():
    print(f"  {row[0]}: {row[1]} 条")

print("\n=== sessions 表中是否有 2026-04-20 的数据 ===")
c.execute("""
    SELECT COUNT(*)
    FROM sessions
    WHERE timestamp LIKE '2026-04-20%'
""")
cnt = c.fetchone()[0]
print(f"4/20 sessions 数量: {cnt}")

conn.close()