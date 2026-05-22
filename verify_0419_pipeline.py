import sqlite3
from datetime import datetime

DB_PATH = 'data/flow_ecosystem.db'
TARGET_DATE = '2026-04-19'

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=" * 60)
print(f"📅 4月19日全链路验证报告")
print("=" * 60)

# 【1】原始消息层
print("\n【1】原始消息层 (sessions表)")
c.execute("""
    SELECT COUNT(*) as msg_count, COUNT(DISTINCT session_id) as session_count,
           MIN(timestamp) as first_msg, MAX(timestamp) as last_msg
    FROM sessions WHERE date(timestamp) = ?
""", (TARGET_DATE,))
r = c.fetchone()
status = "✅" if r['msg_count'] > 0 else "❌"
print(f"  {status} 消息数:{r['msg_count']} | session数:{r['session_count']}")
print(f"     时间:{r['first_msg']} ~ {r['last_msg']}")

# 【2】语义切割层
print("\n【2】语义切割层 (semantic_sessions表)")
c.execute("""
    SELECT COUNT(*) as cnt, SUM(CASE WHEN duration_minutes>0 THEN 1 ELSE 0 END) as valid_dur
    FROM semantic_sessions WHERE date(start_time)=? OR date(end_time)=?
""", (TARGET_DATE, TARGET_DATE))
r = c.fetchone()
status = "✅" if r['cnt'] > 0 else "⚠️"
print(f"  {status} 语义session:{r['cnt']} (时长>0:{r['valid_dur']})")

# 【3】分析层
print("\n【3】分析层 (session_analyses表)")
c.execute("""
    SELECT COUNT(*) as ana_count, COUNT(DISTINCT session_id) as ana_sessions
    FROM session_analyses
    WHERE session_id IN (SELECT DISTINCT session_id FROM sessions WHERE date(timestamp)=?)
""", (TARGET_DATE,))
r = c.fetchone()
status = "✅" if r['ana_count'] > 0 else "❌"
print(f"  {status} 分析记录:{r['ana_count']} | 覆盖session:{r['ana_sessions']}")

# NULL检查
c.execute("""
    SELECT COUNT(*) as total,
        SUM(CASE WHEN goal_alignment IS NULL THEN 1 ELSE 0 END) as null_goal,
        SUM(CASE WHEN portrait_label IS NULL THEN 1 ELSE 0 END) as null_portrait,
        SUM(CASE WHEN style_pace IS NULL THEN 1 ELSE 0 END) as null_style,
        SUM(CASE WHEN goal_evidence IS NULL OR length(goal_evidence)<20 THEN 1 ELSE 0 END) as bad_evidence
    FROM session_analyses
    WHERE session_id IN (SELECT DISTINCT session_id FROM sessions WHERE date(timestamp)=?)
""", (TARGET_DATE,))
r = c.fetchone()
print(f"     四维NULL:{r['null_goal']} | portraitNULL:{r['null_portrait']} | styleNULL:{r['null_style']} | 证据不合格:{r['bad_evidence']}")

# 【4】断裂检查
print("\n【4】链路断裂检查")
c.execute("""
    SELECT DISTINCT s.session_id FROM sessions s
    LEFT JOIN session_analyses sa ON s.session_id = sa.session_id
    WHERE date(s.timestamp)=? AND sa.session_id IS NULL
""", (TARGET_DATE,))
orphan = c.fetchall()
if orphan:
    print(f"  ⚠️ {len(orphan)}个session未分析")
    for o in orphan[:3]: print(f"     {o['session_id'][:40]}...")
else:
    print(f"  ✅ 所有session都有分析记录")

# 【5】重复检查
print("\n【5】重复分析检查")
c.execute("""
    SELECT session_id, COUNT(*) as cnt FROM session_analyses
    WHERE session_id IN (SELECT DISTINCT session_id FROM sessions WHERE date(timestamp)=?)
    GROUP BY session_id HAVING cnt > 1
""", (TARGET_DATE,))
dups = c.fetchall()
if dups:
    print(f"  ❌ {len(dups)}个session被重复分析")
    for d in dups: print(f"     {d['session_id'][:40]}... x{d['cnt']}")
else:
    print(f"  ✅ 无重复")

# 【6】画像分布
print("\n【6】画像分布")
c.execute("""
    SELECT portrait_label, COUNT(*) as cnt,
        ROUND(AVG(CASE goal_alignment WHEN '高' THEN 3 WHEN '中' THEN 2 ELSE 1 END),2) as avg_goal
    FROM session_analyses
    WHERE session_id IN (SELECT DISTINCT session_id FROM sessions WHERE date(timestamp)=?)
    GROUP BY portrait_label ORDER BY cnt DESC
""", (TARGET_DATE,))
for r in c.fetchall():
    print(f"  • {r['portrait_label']}: {r['cnt']}次 (目标均分:{r['avg_goal']})")

# 【7】报告组装数据就绪检查
print("\n【7】报告组装就绪检查")
c.execute("""
    SELECT sa.session_id, sa.goal_alignment, sa.closure_index, sa.flow_depth, sa.cognition_growth,
           sa.portrait_label, sa.goal_evidence, sa.portrait_description, sa.portrait_suggestion
    FROM session_analyses sa
    WHERE sa.session_id IN (SELECT DISTINCT session_id FROM sessions WHERE date(timestamp)=?)
    ORDER BY sa.created_at
""", (TARGET_DATE,))
rows = c.fetchall()
if rows:
    missing = sum(1 for r in rows if not r['portrait_label'] or not r['goal_evidence'])
    print(f"  ✅ 数据源就绪: {len(rows)}条")
    if missing:
        print(f"  ⚠️ {missing}/{len(rows)}条缺少关键字段，报告可能不完整")
    else:
        print(f"  ✅ 字段完整，可生成/flow报告")
else:
    print(f"  ❌ 无数据，无法生成报告")

conn.close()
print("\n" + "=" * 60)
print("🔚 验证结束")
print("=" * 60)