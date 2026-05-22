import sqlite3
from plugin.session_analyzer import SessionAnalyzer
from plugin.llm_client import DeepSeekLLMClient

conn = sqlite3.connect('data/flow_ecosystem.db')
c = conn.cursor()

# 找出未分析的4/20 session
c.execute("""
    SELECT DISTINCT s.session_id
    FROM sessions s
    LEFT JOIN session_analyses sa ON s.session_id = sa.session_id
    WHERE s.timestamp >= '2026-04-20' AND s.timestamp <= '2026-04-20 23:59:59'
    AND sa.id IS NULL
""")
missing_sessions = [r[0] for r in c.fetchall()]

print(f"需要补全的4/20 session: {len(missing_sessions)} 个\n")

llm = DeepSeekLLMClient()

for sid in missing_sessions:
    print(f"正在分析: {sid[:30]}...")
    
    # 获取消息
    c.execute("SELECT role, content_text FROM sessions WHERE session_id = ? ORDER BY timestamp", (sid,))
    messages = [{'role': r, 'content': t or ''} for r, t in c.fetchall()]
    
    try:
        analyzer = SessionAnalyzer(llm_client=llm)
        result = analyzer.analyze(messages, session_id=sid)
        
        if result:
            # REPLACE INTO 自动覆盖（如果存在）或插入（如果不存在）
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
            print(f"  ✅ 成功 | goal={len(result.goal_evidence)}|closure={len(result.closure_evidence)}|flow={len(result.flow_evidence)}|cog={len(result.cognition_evidence)}")
        else:
            print(f"  ❌ 分析返回空结果")
    except Exception as e:
        print(f"  ❌ 失败: {e}")

# 验证最终结果
print("\n" + "=" * 60)
print("📊 补全后验证")
print("=" * 60)

c.execute("""
    SELECT COUNT(DISTINCT sa.session_id)
    FROM session_analyses sa
    WHERE sa.session_id IN (
        SELECT DISTINCT session_id FROM sessions 
        WHERE timestamp >= '2026-04-20' AND timestamp <= '2026-04-20 23:59:59'
    )
""")
total_analyzed = c.fetchone()[0]
print(f"\n✅ 4/20 已分析session数: {total_analyzed}/5")

if total_analyzed == 5:
    print("🎉 全部补全完成！")
else:
    print(f"⚠️ 还有 {5 - total_analyzed} 个未成功")

conn.close()