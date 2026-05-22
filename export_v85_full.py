import sqlite3
conn = sqlite3.connect("data/flow_ecosystem.db")
c = conn.cursor()

c.execute("""
    SELECT sa.session_id, sa.goal_evidence, sa.closure_evidence, sa.flow_evidence, sa.cognition_evidence
    FROM session_analyses sa
    JOIN sessions s ON sa.session_id = s.session_id
    WHERE s.timestamp >= '2026-04-20' AND s.timestamp <= '2026-04-20 23:59:59'
    AND sa.prompt_version = 'v8.5'
    ORDER BY sa.created_at DESC
""")

rows = c.fetchall()

with open("v85_full_evidence.txt", "w", encoding="utf-8") as f:
    f.write(f"=" * 70 + "\n")
    f.write(f"v8.5 四维证据完整内容（共{len(rows)}条）\n")
    f.write(f"=" * 70 + "\n\n")
    
    for i, (sid, g, cl, fl, cg) in enumerate(rows):
        f.write(f"\n{'='*70}\n")
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
        
        f.write(f"\n{'='*70}\n")

conn.close()
print(f"已保存 {len(rows)} 条完整证据到 v85_full_evidence.txt")