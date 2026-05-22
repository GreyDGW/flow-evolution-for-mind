import sqlite3
from plugin.session_analyzer import SessionAnalyzer
from plugin.llm_client import DeepSeekLLMClient

conn = sqlite3.connect('data/flow_ecosystem.db')
c = conn.cursor()

# 找出那个失败的session（53953df4-3869-44e8-893e-ec7c581c4bf4，不是checkpoint版本）
c.execute("""
    SELECT DISTINCT s.session_id, COUNT(*) as msg_cnt
    FROM sessions s
    LEFT JOIN session_analyses sa ON s.session_id = sa.session_id AND sa.prompt_version = 'v8.5'
    WHERE s.timestamp >= '2026-04-20' AND s.timestamp <= '2026-04-20 23:59:59'
    AND sa.id IS NULL
""")
missing = c.fetchall()

print(f"未分析的4/20 session: {len(missing)} 个\n")

if not missing:
    print("✅ 所有4/20 session已全部分析完成！")
    conn.close()
    exit()

llm = DeepSeekLLMClient()

for sid, msg_cnt in missing:
    print(f"正在分析 (新Prompt带【格式约束】): {sid[:35]}...")
    print(f"  消息数: {msg_cnt}")
    
    # 获取消息
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
                # Portrait & Style 字段
                result.portrait_label or '平稳推进',
                result.portrait_description or '状态平稳，保持观察',
                result.portrait_suggestion or '保持当前节奏',
                result.portrait_rule_insight or '状态组合未命中明确规则，保持观察',
                result.style_pace or 'explore',
                result.style_depth or 'deep',
                result.style_tone or 'neutral'
            ))
            conn.commit()
            print(f"  ✅ 成功！")
            print(f"     goal={len(result.goal_evidence)}|closure={len(result.closure_evidence)}")
            print(f"     flow={len(result.flow_evidence)}|cog={len(result.cognition_evidence)}")
        else:
            print(f"  ❌ 分析返回空结果")
    except Exception as e:
        print(f"  ❌ 失败: {str(e)[:120]}")

# 最终验证
print("\n" + "=" * 60)
print("📊 最终验证")
print("=" * 60)

c.execute("""
    SELECT COUNT(DISTINCT sa.session_id)
    FROM session_analyses sa
    WHERE sa.session_id IN (
        SELECT DISTINCT session_id FROM sessions 
        WHERE timestamp >= '2026-04-20' AND timestamp <= '2026-04-20 23:59:59'
    )
    AND sa.prompt_version = 'v8.5'
""")
total = c.fetchone()[0]
print(f"\n4/20 v8.5 分析数: {total}/5")

if total == 5:
    print("🎉 全部5个session分析完成！")
else:
    print(f"⚠️ 还有 {5-total} 个未成功")

conn.close()