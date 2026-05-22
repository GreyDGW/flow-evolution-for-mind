import sqlite3
conn = sqlite3.connect('data/flow_ecosystem.db')
c = conn.cursor()

print("=== 检查 sessions 表中的日期分布 ===")
c.execute("""
    SELECT DATE(timestamp) as date, COUNT(*) as cnt
    FROM sessions
    GROUP BY DATE(timestamp)
    ORDER BY date DESC
    LIMIT 10
""")
print("\nsessions 表日期分布:")
for row in c.fetchall():
    print(f"  {row[0]}: {row[1]} 条")

print("\n=== 检查 session_analyses 表 ===")
c.execute("""
    SELECT sa.prompt_version, 
           MIN(sa.created_at) as earliest,
           MAX(sa.created_at) as latest,
           COUNT(*) as total
    FROM session_analyses sa
    GROUP BY sa.prompt_version
""")
print("\nanalyses 表版本分布:")
for row in c.fetchall():
    print(f"  版本{row[0]}: {row[3]}条 | 最早:{str(row[1])[:10]} | 最新:{str(row[2])[:10]}")

print("\n=== 检查4/20是否有sessions ===")
c.execute("""
    SELECT COUNT(*), MIN(timestamp), MAX(timestamp)
    FROM sessions
    WHERE timestamp >= '2026-04-20' AND timestamp <= '2026-04-20 23:59:59'
""")
cnt, min_t, max_t = c.fetchone()
print(f"4/20 sessions数: {cnt}")
if cnt > 0:
    print(f"时间范围: {min_t} ~ {max_t}")

print("\n=== 检查4/20是否有analyses ===")
c.execute("""
    SELECT COUNT(*), prompt_version
    FROM session_analyses
    WHERE session_id IN (
        SELECT session_id FROM sessions 
        WHERE timestamp >= '2026-04-20' AND timestamp <= '2026-04-20 23:59:59'
    )
    GROUP BY prompt_version
""")
rows = c.fetchall()
if rows:
    for r in rows:
        print(f"4/20 analyses: {r[0]}条 (版本{r[1]})")
else:
    print("4/20 analyses: 0 条 ❌")

conn.close()