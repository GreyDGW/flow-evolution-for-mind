#!/usr/bin/env python3
"""测试滑动窗口对 #5 相似度的影响"""

import sqlite3
import sys
sys.path.insert(0, '.')

from plugin.session.embedding import create_embedder

DB_PATH = 'data/flow_ecosystem.db'
SESSION_ID = '2176204d-4621-4554-9b95-f8b6eae398b2#5'

# 获取消息
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

def cosine(a, b):
    dot = sum(x*y for x, y in zip(a, b))
    norm_a = sum(x*x for x in a) ** 0.5
    norm_b = sum(x*x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)

# 模拟 VectorLayer 的滑动窗口逻辑
MAX_HISTORY = 10
session_vectors = []

embeddings = []
for content, ts, role in msgs:
    text = content or ""
    emb = embedder.encode(text)
    embeddings.append(emb)

print(f"\n🔍 测试不同窗口大小对相似度的影响:")
print("-" * 70)

for window_size in [3, 5, 10, 20]:
    session_vectors = []
    cuts = 0

    for i, emb in enumerate(embeddings):
        # 滑动窗口
        session_vectors.append(emb)
        if len(session_vectors) > window_size:
            session_vectors.pop(0)

        # 计算与窗口平均的相似度
        if len(session_vectors) > 0:
            avg = [sum(x) / len(session_vectors) for x in zip(*session_vectors)]
            sim = cosine(emb, avg)

            if sim < 0.15:
                cuts += 1

    print(f"窗口={window_size:2d}: 切割点数量={cuts}")

print("-" * 70)

# 对比：相邻消息相似度
cuts_adjacent = 0
for i in range(1, len(embeddings)):
    sim = cosine(embeddings[i-1], embeddings[i])
    if sim < 0.15:
        cuts_adjacent += 1

print(f"相邻消息: 切割点数量={cuts_adjacent}")
