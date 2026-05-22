#!/usr/bin/env python3
"""测试加权混合相似度对 #5 的影响"""

import sqlite3
import sys
sys.path.insert(0, '.')

from plugin.session.embedding import create_embedder

DB_PATH = 'data/flow_ecosystem.db'
SESSION_ID = '2176204d-4621-4554-9b95-f8b6eae398b2#5'

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

embedder = create_embedder()

def cosine(a, b):
    dot = sum(x*y for x, y in zip(a, b))
    norm_a = sum(x*x for x in a) ** 0.5
    norm_b = sum(x*x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)

# 定义加权混合函数
def weighted_sim(embeddings, idx):
    if idx == 0:
        return 1.0
    # 最近3条平均
    recent = embeddings[max(0, idx-2):idx+1]
    recent_avg = [sum(x)/len(recent) for x in zip(*recent)]
    sim_recent = cosine(embeddings[idx], recent_avg)
    # 上一条
    sim_prev = cosine(embeddings[idx], embeddings[idx-1])
    # 加权
    return 0.6 * sim_recent + 0.4 * sim_prev

# 预计算所有 embedding
embeddings = []
for content, ts, role in msgs:
    text = content or ""
    emb = embedder.encode(text)
    embeddings.append(emb)

# 测试不同方案
print(f"\n🔍 测试不同相似度方案（前85条）:")
print("-" * 70)

def full_history_avg_sim(embs, idx):
    if idx == 0:
        return 1.0
    avg = [sum(x)/(idx+1) for x in zip(*embs[:idx+1])]
    return cosine(embs[idx], avg)

def adjacent_sim(embs, idx):
    if idx == 0:
        return 1.0
    return cosine(embs[idx-1], embs[idx])

results = [
    ("原方案: 全历史平均", lambda embs, i: full_history_avg_sim(embs, i)),
    ("方案A: 相邻消息", lambda embs, i: adjacent_sim(embs, i)),
    ("方案B: 0.6*最近3 + 0.4*上一条", lambda embs, i: weighted_sim(embs, i)),
]

for name, calc_fn in results:
    cuts = 0
    for i in range(1, len(embeddings)):
        sim = calc_fn(embeddings, i)
        if sim < 0.15:
            cuts += 1
    print(f"{name}: 切割点={cuts}")

print("-" * 70)

# 详细查看加权混合的结果
print(f"\n🔍 加权混合相似度详情（前50条，⚡ = <0.15）:")
cuts = []
for i in range(1, min(50, len(embeddings))):
    sim = weighted_sim(embeddings, i)

    if sim < 0.15:
        marker = "⚡"
        cuts.append(i)
    elif sim < 0.20:
        marker = "📊"
    else:
        marker = "  "

    if sim < 0.25:
        role = msgs[i][2]
        text = (msgs[i][0] or "")[:40]
        print(f"{marker} [{i:2d}] sim={sim:.3f} [{role:8s}] {text}...")

print(f"\n📊 切割点统计（前50条）:")
print(f"   总对数: {min(50, len(embeddings))-1}")
print(f"   ⚡ sim < 0.15: {len(cuts)}")
print(f"   切割位置: {cuts}")
