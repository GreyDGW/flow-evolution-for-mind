import sqlite3
from plugin.session_analyzer import SessionAnalyzer
from plugin.llm_client import DeepSeekLLMClient

conn = sqlite3.connect("data/flow_ecosystem.db")
c = conn.cursor()

c.execute("""
    SELECT DISTINCT session_id
    FROM sessions
    WHERE timestamp >= '2026-04-20' AND timestamp <= '2026-04-20 23:59:59'
""")
sessions = [r[0] for r in c.fetchall()]
print(f"4/20 需要重新分析的 session: {len(sessions)} 个")

llm = DeepSeekLLMClient()

for i, sid in enumerate(sessions):
    print(f"\n--- Processing {i+1}/{len(sessions)}: {sid[:16]}... ---")
    
    c.execute("SELECT role, content_text FROM sessions WHERE session_id = ? ORDER BY timestamp", (sid,))
    messages = [{'role': r, 'content': t or ''} for r, t in c.fetchall()]
    
    try:
        analyzer = SessionAnalyzer(llm_client=llm)
        result = analyzer.analyze(messages, session_id=sid)
        
        if result:
            c.execute("""
                REPLACE INTO session_analyses
                (session_id, goal_alignment, closure_index, flow_depth, cognition_growth,
                 goal_evidence, closure_evidence, flow_evidence, cognition_evidence,
                 llm_model, llm_latency_ms, prompt_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sid,
                result.goal_alignment, result.closure_index, result.flow_depth, result.cognition_growth,
                result.goal_evidence, result.closure_evidence, result.flow_evidence, result.cognition_evidence,
                'deepseek-chat', 0, 'v8.2'
            ))
            conn.commit()
            print(f"  ✅ 成功！")
            print(f"     goal={len(result.goal_evidence)}字 | closure={len(result.closure_evidence)}字 | flow={len(result.flow_evidence)}字 | cog={len(result.cognition_evidence)}字")
            
            # 显示证据样例
            print(f"     goal样例: {result.goal_evidence[:80]}...")
    except Exception as e:
        print(f"  ❌ 失败: {e}")

conn.close()
print("\n重新分析完成！")