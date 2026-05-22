import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import path_setup
import sqlite3, json, sys

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "flow_ecosystem.db")
conn = sqlite3.connect(DB)
conn.execute("PRAGMA foreign_keys = ON")
c = conn.cursor()
passed = 0
total = 9

def check(name, ok):
    global passed
    if ok: passed += 1; print(f"✅ {name}")
    else: print(f"❌ {name}")
    return ok

# 1. 表存在
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
check("semantic_sessions 存在", "semantic_sessions" in tables)
check("session_analyses 存在", "session_analyses" in tables)
check("daily_summaries 存在", "daily_summaries" in tables)

# 2. CHECK 约束（非法值被拒绝）
try:
    c.execute("INSERT INTO semantic_sessions (id, start_time, style_pace) VALUES ('t1', datetime('now'), 'bad')")
    conn.commit(); check("semantic_sessions CHECK", False); c.execute("DELETE FROM semantic_sessions WHERE id='t1'")
except sqlite3.IntegrityError:
    check("semantic_sessions CHECK", True)

try:
    c.execute("INSERT INTO session_analyses (session_id, goal_alignment) VALUES ('t2', 'bad')")
    conn.commit(); check("session_analyses CHECK", False); c.execute("DELETE FROM session_analyses WHERE session_id='t2'")
except sqlite3.IntegrityError:
    check("session_analyses CHECK", True)

# 3. 数据迁移行数
c.execute("SELECT COUNT(*) FROM semantic_sessions")
new_count = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM semantic_sessions_v7_no_check_backup")
old_count = c.fetchone()[0]
check(f"数据迁移: 新表{new_count} == 旧表{old_count}", new_count == old_count)

# 4. 外键约束
try:
    c.execute("INSERT INTO session_analyses (session_id, goal_alignment) VALUES ('fake-id', '高')")
    conn.commit(); check("外键约束", False); c.execute("DELETE FROM session_analyses WHERE session_id='fake-id'")
except sqlite3.IntegrityError:
    check("外键约束", True)

# 5. 全链路写入/读取/删除
c.execute("SELECT id FROM semantic_sessions LIMIT 1")
sid = c.fetchone()[0]
c.execute("""INSERT INTO session_analyses (session_id, goal_alignment, closure_index, flow_depth, cognition_growth, goal_evidence, closure_evidence, flow_evidence, cognition_evidence) VALUES (?,?,?,?,?,?,?,?,?)""", (sid, '高', '低', '高', '中', '目标明确', '无产出', '沉浸', '理解锁'))
conn.commit()
c.execute("SELECT goal_alignment, closure_index FROM session_analyses WHERE session_id=?", (sid,))
row = c.fetchone()
check(f"写入读取: goal={row[0]}, closure={row[1]}", row == ('高', '低'))
c.execute("DELETE FROM session_analyses WHERE session_id=?", (sid,))
conn.commit()

# 6. daily_summaries 写入
c.execute("INSERT INTO daily_summaries (date, goal_high, goal_trend) VALUES ('2099-12-31', 2, '持平')")
conn.commit()
c.execute("SELECT goal_high FROM daily_summaries WHERE date='2099-12-31'")
row = c.fetchone()
check("daily_summaries 写入", row[0] == 2)
c.execute("DELETE FROM daily_summaries WHERE date='2099-12-31'")
conn.commit()

conn.close()
print(f"\n{'='*40}")
print(f"结果: {passed}/{total} 通过")
print(f"{'🎉 Schema就绪' if passed==total else '⚠️ 有失败项，需修复'}")
print(f"{'='*40}")
sys.exit(0 if passed==total else 1)