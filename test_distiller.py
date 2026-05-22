from plugin.session_analyzer import SessionAnalyzer
from plugin.state_distiller import StateDistiller
from plugin.llm_client import DeepSeekLLMClient
import sqlite3

# 测试 StateDistiller 是否正常工作
print("=== 测试 StateDistiller ===\n")
distiller = StateDistiller()

# 测试各种组合
test_cases = [
    ('高', '低', '低', '低'),
    ('高', '中', '低', '低'),
    ('高', '高', '高', '高'),
]

for g, c, f, cg in test_cases:
    p = distiller.distill(g, c, f, cg)
    print(f"输入: goal={g}, closure={c}, flow={f}, cog={cg}")
    print(f"输出: label={p.label}, pace={p.style_pace}, depth={p.style_depth}")
    print()

# 测试完整的 analyze() 流程（使用已有的4/20 session）
print("=== 测试完整流程 ===\n")

conn = sqlite3.connect('data/flow_ecosystem.db')
c = conn.cursor()

# 获取一个已分析的session
c.execute("""
    SELECT sa.session_id
    FROM session_analyses sa
    WHERE sa.prompt_version = 'v8.5'
    LIMIT 1
""")
sid = c.fetchone()[0]
print(f"测试Session: {sid[:30]}...")

# 获取消息
c.execute("SELECT role, content_text FROM sessions WHERE session_id = ? ORDER BY timestamp", (sid,))
messages = [{'role': r, 'content': t or ''} for r, t in c.fetchall()]

llm = DeepSeekLLMClient()
analyzer = SessionAnalyzer(llm_client=llm)

try:
    result = analyzer.analyze(messages, session_id=sid + "_test")
    
    if result:
        print(f"\n✅ 分析成功!")
        print(f"  四维: {result.goal_alignment}/{result.closure_index}/{result.flow_depth}/{result.cognition_growth}")
        print(f"  Portrait:")
        print(f"    label: {result.portrait_label}")
        print(f"    description: {result.portrait_description[:50]}...")
        print(f"    suggestion: {result.portrait_suggestion[:50]}...")
        print(f"  Style:")
        print(f"    pace: {result.style_pace}")
        print(f"    depth: {result.style_depth}")
        print(f"    tone: {result.style_tone}")
        
        # 检查是否有NULL
        has_null = any([
            result.portrait_label is None,
            result.portrait_description is None,
            result.style_pace is None
        ])
        
        if has_null:
            print("\n❌ 仍有 NULL 字段!")
        else:
            print("\n✅ 所有字段都有值！")
    else:
        print("❌ 分析返回空结果")
except Exception as e:
    print(f"❌ 错误: {e}")

conn.close()
print("\n测试完成")