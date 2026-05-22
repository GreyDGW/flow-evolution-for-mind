import sqlite3
conn = sqlite3.connect('data/flow_ecosystem.db')
c = conn.cursor()

print("=== session_analyses 表结构 ===\n")
c.execute("PRAGMA table_info(session_analyses)")
for row in c.fetchall():
    print(f"  {row[1]:30} | 类型:{row[2]:10} | 非空:{row[3]} | 默认值:{row[4]}")

print("\n=== 检查哪些字段有数据，哪些全是NULL ===")
c.execute("SELECT * FROM session_analyses LIMIT 1")
cols = [desc[0] for desc in c.description]
first_row = c.fetchone()

print("\n字段状态:")
for i, col in enumerate(cols):
    val = first_row[i] if first_row else None
    if val is None:
        status = "❌ 全NULL"
    else:
        status = f"✅ 有值 ({str(val)[:40]}...)"
    print(f"  {col:30} | {status}")

print("\n=== 统计：各字段非NULL的记录数 ===")
for col in cols:
    c.execute(f"SELECT COUNT(*) FROM session_analyses WHERE \"{col}\" IS NOT NULL")
    not_null = c.fetchone()[0]
    total = 37  # 总记录数
    if not_null == 0:
        print(f"  {col:30} | {not_null}/{total} (全部NULL)")
    else:
        print(f"  {col:30} | {not_null}/{total}")

conn.close()