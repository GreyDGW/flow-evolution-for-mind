import sqlite3
from datetime import datetime

DB_PATH = 'data/flow_ecosystem.db'
TARGET_DATE = '2026-04-19'

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=" * 70)
print(f"🔍 4月19日 Session 切割深度审计")
print("=" * 70)

# ── 1. 原始 session 的时间跨度 ──
print("\n【1】原始 sessions 表：2 个 session_id 的时间分布")
c.execute("""
    SELECT session_id,
           COUNT(*) as msg_count,
           MIN(timestamp) as start_time,
           MAX(timestamp) as end_time,
           ROUND((julianday(MAX(timestamp)) - julianday(MIN(timestamp))) * 24 * 60, 1) as duration_minutes
    FROM sessions
    WHERE date(timestamp) = ?
    GROUP BY session_id
    ORDER BY MIN(timestamp)
""", (TARGET_DATE,))
for r in c.fetchall():
    dur_h = r['duration_minutes'] // 60
    dur_m = r['duration_minutes'] % 60
    print(f"  📦 {r['session_id'][:40]}...")
    print(f"     消息数:{r['msg_count']} | 跨度:{dur_h}小时{dur_m}分钟")
    print(f"     起止:{r['start_time']} ~ {r['end_time']}")

# ── 2. 消息间隔 > 30 分钟的断点 ──
print("\n【2】消息间隔 > 30 分钟的潜在切割点（硬规则层应触发）")
c.execute("""
    WITH ordered AS (
        SELECT timestamp,
               LAG(timestamp) OVER (ORDER BY timestamp) as prev_time,
               session_id
        FROM sessions
        WHERE date(timestamp) = ?
    )
    SELECT timestamp, prev_time,
           ROUND((julianday(timestamp) - julianday(prev_time)) * 24 * 60, 1) as gap_minutes,
           session_id
    FROM ordered
    WHERE prev_time IS NOT NULL
    AND (julianday(timestamp) - julianday(prev_time)) * 24 * 60 > 30
    ORDER BY timestamp
""", (TARGET_DATE,))
gaps = c.fetchall()
if gaps:
    for r in gaps:
        print(f"  ⛔ {r['timestamp']} (间隔 {r['gap_minutes']} 分钟) [session:{r['session_id'][:20]}...]")
    print(f"  ⚠️ 共 {len(gaps)} 个 >30分钟断点，应触发硬规则切割")
else:
    print("  ✅ 无 >30 分钟断点（所有消息连续）")

# ── 3. semantic_sessions 的时间分布 ──
print("\n【3】semantic_sessions 表：63 个片段的时间分布（前10个）")
c.execute("""
    SELECT id, start_time, end_time, duration_minutes, interaction_count, total_message_count
    FROM semantic_sessions
    WHERE date(start_time) = ? OR date(end_time) = ?
    ORDER BY start_time
    LIMIT 10
""", (TARGET_DATE, TARGET_DATE))
for r in c.fetchall():
    print(f"  🔪 {r['id'][:30]}... | {r['start_time'][11:16]}~{r['end_time'][11:16]} | dur={r['duration_minutes']}min | turns={r['interaction_count']}")

# 统计
c.execute("""
    SELECT COUNT(*) as total,
           SUM(CASE WHEN duration_minutes > 0 THEN 1 ELSE 0 END) as valid_dur,
           MIN(start_time) as first_start,
           MAX(end_time) as last_end
    FROM semantic_sessions
    WHERE date(start_time) = ? OR date(end_time) = ?
""", (TARGET_DATE, TARGET_DATE))
r = c.fetchone()
print(f"  📊 总计:{r['total']}个 | 时长>0:{r['valid_dur']} | 范围:{r['first_start']} ~ {r['last_end']}")

# ── 4. 关键断裂检查：semantic_sessions.id vs sessions.session_id ──
print("\n【4】断裂点审计：semantic_sessions.id 是否等于 sessions.session_id？")
c.execute("""
    SELECT DISTINCT s.session_id
    FROM sessions s
    WHERE date(s.timestamp) = ?
    AND s.session_id IN (SELECT id FROM semantic_sessions)
""", (TARGET_DATE,))
matches = c.fetchall()
print(f"  sessions.session_id 存在于 semantic_sessions.id 中的数量: {len(matches)}")

c.execute("""
    SELECT DISTINCT sem.id
    FROM semantic_sessions sem
    WHERE (date(sem.start_time) = ? OR date(sem.end_time) = ?)
    AND sem.id IN (SELECT session_id FROM sessions)
""", (TARGET_DATE, TARGET_DATE))
matches2 = c.fetchall()
print(f"  semantic_sessions.id 存在于 sessions.session_id 中的数量: {len(matches2)}")

if not matches and not matches2:
    print("  ❌❌❌ 两表主键零交集！这是 PRD 2.3.4 断裂点 #1")
    print("     → semantic_sessions 和 sessions 是完全独立的两个命名空间")
    print("     → SessionCutter 切了 63 个片段，但 ReportAssembler 无法关联到原始消息")

# ── 5. 按小时分布的消息密度 ──
print("\n【5】4月19日消息密度（按小时）")
c.execute("""
    SELECT strftime('%H', timestamp) as hour, COUNT(*) as cnt
    FROM sessions
    WHERE date(timestamp) = ?
    GROUP BY hour
    ORDER BY hour
""", (TARGET_DATE,))
for r in c.fetchall():
    bar = "█" * (r['cnt'] // 5)
    print(f"  {r['hour']}:00 | {r['cnt']:3d}条 {bar}")

conn.close()
print("\n" + "=" * 70)
print("🔚 审计结束")
print("=" * 70)