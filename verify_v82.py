import sqlite3
from collections import Counter

conn = sqlite3.connect("data/flow_ecosystem.db")
c = conn.cursor()

c.execute("""
    SELECT length(goal_evidence) as len, goal_evidence
    FROM session_analyses sa
    JOIN sessions s ON sa.session_id = s.session_id
    WHERE s.timestamp >= '2026-04-20' AND s.timestamp <= '2026-04-20 23:59:59'
""")
rows = c.fetchall()

print("📊 4/20 证据长度分布（关键指标：不再统一 150）")
lengths = [r[0] for r in rows]
for length, cnt in sorted(Counter(lengths).items()):
    print(f"  {length}字: {cnt} 条")

print(f"\n总记录数: {len(rows)}（应等于 session 数，即 5）")

# 检查是否有原文片段 + 质量
c.execute("""
    SELECT goal_evidence, closure_evidence, flow_evidence, cognition_evidence
    FROM session_analyses sa
    JOIN sessions s ON sa.session_id = s.session_id
    WHERE s.timestamp >= '2026-04-20' AND s.timestamp <= '2026-04-20 23:59:59'
    ORDER BY sa.created_at DESC
    LIMIT 1
""")
result = c.fetchone()

if result:
    g, cl, f, cg = result
    print(f"\n最新记录质量:")
    print(f"  goal: {len(g)}字 | closure: {len(cl)}字 | flow: {len(f)}字 | cog: {len(cg)}字")
    print(f"  含原文引号: {'✅' if any('"' in (x or '') for x in [g, cl, f, cg]) else '❌'}")

    # 检查是否有系统视角垃圾词
    bad_words = ["助手响应", "系统调用", "toolResult", "立即响应", "连续调用"]
    has_bad = any(w in (x or '') for x in [g, cl, f, cg] for w in bad_words)
    print(f"  无系统视角垃圾: {'✅' if not has_bad else '❌'}")

    # 检查是否有重复原话（简单启发式：同一对引号出现2次以上）
    has_repeat = any((x or '').count('"') >= 4 for x in [g, cl, f, cg])
    print(f"  无重复原话: {'✅' if not has_repeat else '❌'}")
else:
    print("未找到分析记录")

conn.close()