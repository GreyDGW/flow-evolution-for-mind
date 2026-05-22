import sqlite3
conn = sqlite3.connect('data/flow_ecosystem.db')
c = conn.cursor()

print("=" * 60)
print("📊 数据库完整诊断")
print("=" * 60)

# 1. 基本信息
c.execute("SELECT COUNT(*) FROM sessions")
total_sessions = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM session_analyses")
total_analyses = c.fetchone()[0]

print(f"\n【基本信息】")
print(f"  sessions 表总记录: {total_sessions}")
print(f"  session_analyses 表总记录: {total_analyses}")

# 2. 4/20 sessions 详情
print(f"\n【4/20 sessions 表】")
c.execute("""
    SELECT COUNT(DISTINCT session_id), 
           MIN(timestamp), 
           MAX(timestamp)
    FROM sessions
    WHERE timestamp >= '2026-04-20' AND timestamp <= '2026-04-20 23:59:59'
""")
cnt, min_t, max_t = c.fetchone()
print(f"  不同session数: {cnt}")
print(f"  时间范围: {min_t} ~ {max_t}")
print(f"  总消息数: (包含在{cnt}个session中)")

# 3. 4/20 analyses 详情
print(f"\n【4/20 session_analyses 表】")
c.execute("""
    SELECT sa.id, sa.prompt_version, sa.created_at,
           length(sa.goal_evidence) as g_len,
           substr(sa.session_id, 1, 20) as sid_short
    FROM session_analyses sa
    WHERE sa.session_id IN (
        SELECT DISTINCT session_id FROM sessions 
        WHERE timestamp >= '2026-04-20' AND timestamp <= '2026-04-20 23:59:59'
    )
    ORDER BY sa.created_at DESC
""")
rows = c.fetchall()
print(f"  分析记录数: {len(rows)}")
for r in rows:
    print(f"    ID={r[0]} | 版本={r[1]} | 时间={r[2][:19]} | goal={r[3]}字 | session={r[4]}...")

# 4. 所有 analyses 按日期分布
print(f"\n【所有 analyses 按 created_at 日期】")
c.execute("""
    SELECT DATE(created_at) as date, 
           prompt_version,
           COUNT(*) as cnt
    FROM session_analyses
    GROUP BY DATE(created_at), prompt_version
    ORDER BY date DESC
""")
for row in c.fetchall():
    print(f"  {row[0]} | 版本{row[1]} | {row[2]}条")

# 5. 对比：sessions 有多少 vs analyses 有多少
print(f"\n【关键对比】")
c.execute("""
    SELECT COUNT(DISTINCT s.session_id) as has_session,
           COUNT(DISTINCT sa.session_id) as has_analysis
    FROM sessions s
    LEFT JOIN session_analyses sa ON s.session_id = sa.session_id
    WHERE s.timestamp >= '2026-04-20' AND s.timestamp <= '2026-04-20 23:59:59'
""")
has_session, has_analysis = c.fetchone()
print(f"  4/20 有sessions的: {has_session} 个")
print(f"  4/20 有analyses的: {has_analysis} 个")
print(f"  ❌ 缺少分析: {has_session - has_analysis} 个session未分析")

conn.close()