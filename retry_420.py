import sqlite3
from plugin.session_analyzer import SessionAnalyzer
from plugin.llm_client import DeepSeekLLMClient

conn = sqlite3.connect('data/flow_ecosystem.db')
c = conn.cursor()

# 找出仍然未分析的4/20 session
c.execute("""
    SELECT DISTINCT s.session_id
    FROM sessions s
    LEFT JOIN session_analyses sa ON s.session_id = sa.session_id AND sa.prompt_version = 'v8.5'
    WHERE s.timestamp >= '2026-04-20' AND s.timestamp <= '2026-04-20 23:59:59'
    AND sa.id IS NULL
""")
still_missing = [r[0] for r in c.fetchall()]

print(f"仍需补全的4/20 session: {len(still_missing)} 个\n")

llm = DeepSeekLLMClient()

for sid in still_missing:
    print(f"正在重试: {sid[:35]}...")
    
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
                'deepseek-chat', 0, 'v8.5'
            ))
            conn.commit()
            print(f"  ✅ 成功 | goal={len(result.goal_evidence)}|closure={len(result.closure_evidence)}|flow={len(result.flow_evidence)}|cog={len(result.cognition_evidence)}")
        else:
            print(f"  ❌ 分析返回空结果")
    except Exception as e:
        print(f"  ❌ 失败: {str(e)[:100]}")

# 最终验证
print("\n" + "=" * 60)
print("📊 最终验证")
print("=" * 60)

c.execute("""
    SELECT COUNT(*), prompt_version
    FROM session_analyses
    WHERE session_id IN (
        SELECT DISTINCT session_id FROM sessions 
        WHERE timestamp >= '2026-04-20' AND timestamp <= '2026-04-20 23:59:59'
    )
    GROUP BY prompt_version
""")
rows = c.fetchall()
total = sum(r[0] for r in rows)
print(f"\n4/20 总分析记录: {total} 条")
for cnt, ver in rows:
    print(f"  版本{ver}: {cnt}条")

if total == 5:
    print("🎉 全部5个session补全完成！")
else:
    print(f"⚠️ 完成 {total}/5，还有 {5-total} 个未成功")

conn.close()