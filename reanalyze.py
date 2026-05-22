import sqlite3
from plugin.session_analyzer import SessionAnalyzer
from plugin.llm_client import DeepSeekLLMClient

conn = sqlite3.connect("data/flow_ecosystem.db")
c = conn.cursor()

# 找出 4/20 的所有 session
c.execute("SELECT DISTINCT session_id FROM sessions WHERE timestamp >= '2026-04-20' AND timestamp <= '2026-04-20 23:59:59'")
sessions = [r[0] for r in c.fetchall()]
print(f"4/20 需要重新分析的 session: {len(sessions)} 个")

llm = DeepSeekLLMClient()

for sid in sessions:
    # 删除旧分析
    c.execute("DELETE FROM session_analyses WHERE session_id = ?", (sid,))
    conn.commit()
    
    # 获取消息
    c.execute("SELECT role, content_text FROM sessions WHERE session_id = ? ORDER BY timestamp", (sid,))
    messages = [{'role': r, 'content': t or ''} for r, t in c.fetchall()]
    print(f"  处理 {sid[:16]}... 消息数: {len(messages)}")
    
    # 分析
    analyzer = SessionAnalyzer(llm_client=llm)
    result = analyzer.analyze(messages, session_id=sid)
    
    if result:
        # 写入数据库
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
            'deepseek-chat', 0, 'v8.0'
        ))
        conn.commit()
        print(f"  ✅ {sid[:16]}... goal={len(result.goal_evidence)}|closure={len(result.closure_evidence)}|flow={len(result.flow_evidence)}|cog={len(result.cognition_evidence)}")
    else:
        print(f"  ❌ {sid[:16]}... 分析失败")

conn.close()
print("重新分析完成")