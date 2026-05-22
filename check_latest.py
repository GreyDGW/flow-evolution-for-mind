import sqlite3
conn = sqlite3.connect('data/flow_ecosystem.db')
c = conn.cursor()

print("=== 检查最新分析的session ===\n")

c.execute("""
    SELECT sa.session_id, sa.goal_evidence, sa.created_at
    FROM session_analyses sa
    WHERE sa.session_id IN (
        SELECT DISTINCT session_id FROM sessions 
        WHERE timestamp >= '2026-04-20' AND timestamp <= '2026-04-20 23:59:59'
    )
    AND sa.prompt_version = 'v8.5'
    ORDER BY sa.created_at DESC
    LIMIT 1
""")
row = c.fetchone()
if row:
    sid, g, created = row
    print(f"Session: {sid[:40]}...")
    print(f"创建时间: {created}")
    print(f"\n目标对齐 ({len(g)}字):")
    print(g)
    
    # 检查是否有引号
    has_cn_quote = '"' in g or '"' in g
    has_en_quote = '"' in g
    print(f"\n中文引号: {has_cn_quote} | 英文引号: {has_en_quote}")

conn.close()