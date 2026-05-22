import sqlite3
conn = sqlite3.connect("data/flow_ecosystem.db")
c = conn.cursor()

# 检查4/20记录
c.execute("""
    SELECT sa.session_id, sa.prompt_version, COUNT(*) as cnt
    FROM session_analyses sa
    JOIN sessions s ON sa.session_id = s.session_id
    WHERE s.timestamp >= '2026-04-20' AND s.timestamp <= '2026-04-20 23:59:59'
    GROUP BY sa.session_id, sa.prompt_version
""")
print("4/20 记录分布:")
for sid, ver, cnt in c.fetchall():
    print(f"  {sid[:16]}... | {ver} | {cnt}条")

# 清理重复记录
c.execute("""
    DELETE FROM session_analyses
    WHERE id NOT IN (
        SELECT MAX(id)
        FROM session_analyses
        GROUP BY session_id
    )
""")
conn.commit()
print(f"\n已清理重复记录，删除了 {c.rowcount} 条")

# 验证清理结果
c.execute("SELECT COUNT(*) FROM session_analyses")
print(f"清理后总记录数: {c.fetchone()[0]}")

conn.close()