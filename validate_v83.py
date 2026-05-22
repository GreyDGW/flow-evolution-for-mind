import sqlite3
import re

conn = sqlite3.connect("data/flow_ecosystem.db")
c = conn.cursor()

c.execute("""
    SELECT sa.session_id, sa.goal_evidence, sa.closure_evidence, sa.flow_evidence, sa.cognition_evidence
    FROM session_analyses sa
    JOIN sessions s ON sa.session_id = s.session_id
    WHERE s.timestamp >= '2026-04-20' AND s.timestamp <= '2026-04-20 23:59:59'
    ORDER BY sa.created_at DESC
""")
rows = c.fetchall()

print("=" * 70)
print("📊 v8.3 证据质量检查（截断检测）")
print("=" * 70)

for i, (sid, g, cl, f, cg) in enumerate(rows):
    print(f"\nSession {i+1}: {sid[:16]}...")
    for dim, ev in [("目标对齐", g), ("闭环指数", cl), ("心流深度", f), ("认知成长", cg)]:
        if not ev:
            print(f"  ❌ {dim}: NULL")
            continue
        is_complete = bool(re.search(r'[。！？.!?"\"\']$', ev.strip()))
        status = "✅" if is_complete else "⚠️ 截断"
        print(f"  {status} {dim}: {len(ev)}字 | 末尾: '{ev.strip()[-20:]}'")

all_evs = [g for _, g, _, _, _ in rows] + [cl for _, _, cl, _, _ in rows] + [f for _, _, _, f, _ in rows] + [cg for _, _, _, _, cg in rows]
lengths = [len(ev) for ev in all_evs if ev]
print(f"\n{'='*70}")
print("📊 长度分布:")
from collections import Counter
for length, cnt in sorted(Counter(lengths).items()):
    print(f"  {length}字: {cnt} 条")

conn.close()