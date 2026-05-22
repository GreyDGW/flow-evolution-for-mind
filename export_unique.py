import sqlite3
conn = sqlite3.connect("data/flow_ecosystem.db")
c = conn.cursor()

# 清理重复记录，只保留每个session的最新分析
c.execute("""
    DELETE FROM session_analyses
    WHERE session_id IN (
        SELECT session_id FROM sessions 
        WHERE timestamp >= '2026-04-20' AND timestamp <= '2026-04-20 23:59:59'
    )
    AND id NOT IN (
        SELECT MAX(id)
        FROM session_analyses
        WHERE session_id IN (
            SELECT session_id FROM sessions 
            WHERE timestamp >= '2026-04-20' AND timestamp <= '2026-04-20 23:59:59'
        )
        GROUP BY session_id
    )
""")
conn.commit()
print(f"已删除 {c.rowcount} 条重复记录")

# 获取去重后的分析记录
c.execute("""
    SELECT sa.session_id, sa.goal_evidence, sa.closure_evidence, sa.flow_evidence, sa.cognition_evidence
    FROM session_analyses sa
    WHERE sa.session_id IN (
        SELECT DISTINCT session_id FROM sessions 
        WHERE timestamp >= '2026-04-20' AND timestamp <= '2026-04-20 23:59:59'
    )
""")

rows = c.fetchall()
print(f"4/20 有效分析记录: {len(rows)} 条\n")

with open("v85_unique_evidence.txt", "w", encoding="utf-8") as f:
    for i, (sid, g, cl, fl, cg) in enumerate(rows):
        f.write(f"{'='*70}\n")
        f.write(f"SESSION {i+1}\n")
        f.write(f"Session ID: {sid}\n")
        f.write(f"目标对齐: {len(g)}字 | 闭环指数: {len(cl)}字 | 心流深度: {len(fl)}字 | 认知成长: {len(cg)}字\n")
        f.write(f"{'='*70}\n")
        
        f.write(f"\n【目标对齐】{len(g)}字:\n")
        f.write(f"{g}\n")
        
        f.write(f"\n【闭环指数】{len(cl)}字:\n")
        f.write(f"{cl}\n")
        
        f.write(f"\n【心流深度】{len(fl)}字:\n")
        f.write(f"{fl}\n")
        
        f.write(f"\n【认知成长】{len(cg)}字:\n")
        f.write(f"{cg}\n")
        
        f.write(f"\n{'='*70}\n\n")

conn.close()
print("已保存到 v85_unique_evidence.txt")