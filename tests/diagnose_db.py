import sqlite3
conn=sqlite3.connect('data/flow_ecosystem.db')
c=conn.cursor()

print("=== 所有表及记录数 ===")
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
for (t,) in c.fetchall():
    try:
        c.execute(f"SELECT COUNT(*) FROM {t}")
        n=c.fetchone()[0]
        print(f"  {t}: {n}")
    except: pass

print("\n=== 含消息字段的表 ===")
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
for (t,) in c.fetchall():
    c.execute(f"PRAGMA table_info({t})")
    cols=[x[1] for x in c.fetchall()]
    hits=[x for x in cols if any(k in x.lower() for k in ['message','content'])]
    if hits:
        print(f"  {t}: {hits}")

print("\n=== turns 表样本 ===")
c.execute("SELECT user_message, assistant_response FROM turns LIMIT 2")
for row in c.fetchall():
    print(f"  user: {str(row[0])[:80]}")
    print(f"  asst: {str(row[1])[:80]}")

print("\n=== semantic_sessions 表样本 ===")
c.execute("SELECT id, title, topic_summary, overall_goal FROM semantic_sessions LIMIT 2")
for row in c.fetchall():
    print(f"  id: {row[0][:20]}")
    print(f"  title: {str(row[1])[:80]}")
    print(f"  goal: {str(row[3])[:80]}")
conn.close()
