#!/usr/bin/env python3
"""测试 #5 的 VectorLayer 相似度"""

import sqlite3
import sys
sys.path.insert(0, '.')

from plugin.session.embedding import create_embedder

DB_PATH = 'data/flow_ecosystem.db'
SESSION_ID = '2176204d-4621-4554-9b95-f8b6eae398b2#5'

# 获取消息（只取 user 和 assistant）
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("""
    SELECT content_text, timestamp, role
    FROM sessions
    WHERE session_id = ? AND role IN ('user', 'assistant')
    ORDER BY timestamp
""", (SESSION_ID,))
msgs = c.fetchall()
conn.close()

print(f"📊 Session #5: {len(msgs)} 条 user/assistant 消息")

# 加载 embedder
embedder = create_embedder()
print(f"✅ Embedder: {type(embedder).__name__}")

# 计算相邻消息相似度
def cosine(a, b):
    dot = sum(x*y for x, y in zip(a, b))
    norm_a = sum(x*x for x in a) ** 0.5
    norm_b = sum(x*x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)

# 只取前 30 条测试
test_msgs = msgs[:30]
embeddings = []
for content, ts, role in test_msgs:
    text = content or ""
    emb = embedder.encode(text)
    embeddings.append(emb)

print(f"\n🔍 相邻消息相似度分布（前30条，⚡ = <0.15 应该切割）:")
print("-" * 70)

low_count = 0
medium_count = 0
high_count = 0

for i in range(1, len(embeddings)):
    sim = cosine(embeddings[i-1], embeddings[i])
    prev_role = test_msgs[i-1][2]
    curr_role = test_msgs[i][2]
    prev_text = (test_msgs[i-1][0] or "")[:35]
    curr_text = (test_msgs[i][0] or "")[:35]

    if sim < 0.15:
        marker = "⚡"
        low_count += 1
    elif sim < 0.30:
        marker = "📊"
        medium_count += 1
    else:
        marker = "  "
        high_count += 1

    if sim < 0.35:
        print(f"{marker} [{i-1:2d}]→[{i:2d}] sim={sim:.3f} [{prev_role:8s}→{curr_role:8s}]")
        print(f"        prev: {prev_text}...")
        print(f"        curr: {curr_text}...")

print("-" * 70)
print(f"\n📈 统计:")
print(f"   总对数: {len(embeddings)-1}")
print(f"   ⚡ sim < 0.15 (应切割): {low_count} ({low_count/(len(embeddings)-1)*100:.1f}%)")
print(f"   📊 sim 0.15-0.30: {medium_count} ({medium_count/(len(embeddings)-1)*100:.1f}%)")
print(f"   ✅ sim > 0.30: {high_count} ({high_count/(len(embeddings)-1)*100:.1f}%)")

# 对比：计算当前 vs 历史平均
print(f"\n📊 对比：当前 vs 历史平均（VectorLayer 方式）:")
session_avg = [sum(x) / len(embeddings) for x in zip(*embeddings)]

vs_avg_low = 0
for i in range(1, len(embeddings)):
    sim_vs_avg = cosine(embeddings[i], session_avg)
    if sim_vs_avg < 0.15:
        vs_avg_low += 1

print(f"   ⚡ vs_avg < 0.15: {vs_avg_low} ({vs_avg_low/(len(embeddings)-1)*100:.1f}%)")
