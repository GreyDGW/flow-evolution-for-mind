import sqlite3
conn = sqlite3.connect("data/flow_ecosystem.db")
c = conn.cursor()

print("=" * 70)
print("🔍 数据库真相核查")
print("=" * 70)

# 1. 4/20 到底有多少个不同的 session？
c.execute("SELECT COUNT(DISTINCT session_id) FROM sessions WHERE timestamp >= '2026-04-20' AND timestamp <= '2026-04-20 23:59:59'")
print(f"\n【1】4/20 sessions 表里不同 session_id: {c.fetchone()[0]} 个")

# 2. 这些 session 在 session_analyses 里有多少条记录？
c.execute("SELECT sa.session_id, COUNT(*) as cnt, GROUP_CONCAT(DISTINCT sa.prompt_version) as versions FROM session_analyses sa JOIN sessions s ON sa.session_id = s.session_id WHERE s.timestamp >= '2026-04-20' AND s.timestamp <= '2026-04-20 23:59:59' GROUP BY sa.session_id")
rows = c.fetchall()
print(f"\n【2】4/20 的 session_analyses 记录分布:")
for sid, cnt, versions in rows:
    print(f"  {sid[:16]}...: {cnt} 条记录, 版本: {versions}")

# 3. 最新写入的 5 条记录是什么版本、多长？
c.execute("SELECT sa.session_id, sa.prompt_version, length(sa.goal_evidence) as g_len, substr(sa.goal_evidence, 1, 50) as g_preview FROM session_analyses sa ORDER BY sa.created_at DESC LIMIT 5")
print(f"\n【3】最新 5 条 session_analyses（按 created_at）:")
for sid, ver, glen, gprev in c.fetchall():
    print(f"  {sid[:16]}... | {ver} | goal={glen}字 | {gprev}...")

# 4. ReportAssembler 实际用的 SQL 是什么？
print(f"\n【4】ReportAssembler 中的 session_analyses 相关 SQL:")
with open("plugin/report_assembler.py", "r") as f:
    content = f.read()
    import re
    sqls = re.findall(r'"""(.*?)"""', content, re.DOTALL)
    for sql in sqls:
        if "session_analyses" in sql:
            print(f"  {sql.strip()[:200]}...")

conn.close()
print("\n" + "=" * 70)