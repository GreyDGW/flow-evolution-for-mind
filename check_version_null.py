import sqlite3
conn = sqlite3.connect('data/flow_ecosystem.db')
c = conn.cursor()

print("=== 按版本分组检查NULL情况 ===\n")

c.execute("""
    SELECT sa.prompt_version,
           COUNT(*) as total,
           SUM(CASE WHEN sa.portrait_label IS NULL THEN 1 ELSE 0 END) as portrait_null,
           SUM(CASE WHEN sa.style_pace IS NULL THEN 1 ELSE 0 END) as style_null,
           SUM(CASE WHEN sa.extended_dimensions IS NULL THEN 1 ELSE 0 END) as ext_null
    FROM session_analyses sa
    GROUP BY sa.prompt_version
""")

print(f"{'版本':<10} {'总数':>6} {'portrait_NULL':>14} {'style_NULL':>12} {'ext_NULL':>10}")
print("-" * 60)
for row in c.fetchall():
    ver, total, p_null, s_null, e_null = row
    print(f"{ver:<10} {total:>6} {p_null:>14} {s_null:>12} {e_null:>10}")

print("\n=== v8.5 记录详情 ===")
c.execute("""
    SELECT id, session_id, 
           CASE WHEN portrait_label IS NULL THEN '❌' ELSE '✅' END as portrait,
           CASE WHEN style_pace IS NULL THEN '❌' ELSE '✅' END as style
    FROM session_analyses
    WHERE prompt_version = 'v8.5'
""")
for row in c.fetchall():
    print(f"  ID={row[0]} | {row[1][:25]}... | portrait={row[2]} | style={row[3]}")

conn.close()