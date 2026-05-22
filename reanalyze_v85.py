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

for sid in sessions:
    c.execute("DELETE FROM session_analyses WHERE session_id = ?", (sid,))
    conn.commit()
    
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
                 llm_model, llm_latency_ms, prompt_version,
                 portrait_label, portrait_description, portrait_suggestion, portrait_rule_insight,
                 style_pace, style_depth, style_tone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sid,
                result.goal_alignment, result.closure_index, result.flow_depth, result.cognition_growth,
                result.goal_evidence, result.closure_evidence, result.flow_evidence, result.cognition_evidence,
                'deepseek-chat', 0, 'v8.5',
                result.portrait_label or '平稳推进',
                result.portrait_description or '状态平稳，保持观察',
                result.portrait_suggestion or '保持当前节奏',
                result.portrait_rule_insight or '状态组合未命中明确规则，保持观察',
                result.style_pace or 'explore',
                result.style_depth or 'deep',
                result.style_tone or 'neutral'
            ))
            conn.commit()
            print(f"  ✅ {sid[:16]}... goal={len(result.goal_evidence)}|closure={len(result.closure_evidence)}|flow={len(result.flow_evidence)}|cog={len(result.cognition_evidence)}")
    except Exception as e:
        print(f"  ❌ {sid[:16]}... 失败: {e}")

conn.close()
print("重新分析完成")