import sqlite3
import sys

print("=" * 70)
print("🔍 VectorLayer 乱切根因诊断")
print("=" * 70)

# ── 1. content_text 质量诊断 ──
print("\n【1】content_text 字段质量诊断")
conn = sqlite3.connect('data/flow_ecosystem.db')
c = conn.cursor()

c.execute("""
    SELECT 
        COUNT(*) as total, 
        SUM(CASE WHEN content_text IS NULL THEN 1 ELSE 0 END) as null_count, 
        SUM(CASE WHEN content_text = '' THEN 1 ELSE 0 END) as empty_count, 
        SUM(CASE WHEN content_length IS NULL OR content_length = 0 THEN 1 ELSE 0 END) as zero_len, 
        AVG(CASE WHEN content_length > 0 THEN content_length END) as avg_len, 
        MAX(content_length) as max_len 
    FROM sessions 
    WHERE date(timestamp) = '2026-04-19' 
""")
r = c.fetchone()
total = r[0]
null_pct = r[1] / total * 100 if total > 0 else 0
empty_pct = r[2] / total * 100 if total > 0 else 0
zero_pct = r[3] / total * 100 if total > 0 else 0

print(f"  总消息: {total}")
print(f"  content_text NULL: {r[1]} ({null_pct:.1f}%)")
print(f"  content_text 空字符串: {r[2]} ({empty_pct:.1f}%)")
print(f"  content_length = 0: {r[3]} ({zero_pct:.1f}%)")
print(f"  平均长度(非零): {r[4]:.1f} 字符")
print(f"  最大长度: {r[5]}")

# 按 role 分布
c.execute("""
    SELECT role, 
        COUNT(*) as cnt, 
        SUM(CASE WHEN content_text IS NULL OR content_text = '' THEN 1 ELSE 0 END) as empty 
    FROM sessions 
    WHERE date(timestamp) = '2026-04-19' 
    GROUP BY role 
""")
print(f"\n  按 role 分布:")
for r in c.fetchall():
    pct = r[2] / r[1] * 100 if r[1] else 0
    print(f"    {r[0]:12s}: {r[1]:3d}条 | 空内容: {r[2]:3d} ({pct:.1f}%)")

# ── 2. 嵌入模型加载诊断 ──
print("\n【2】ChromaEmbedder 加载诊断")
try:
    from plugin.session.embedding import create_embedder
    embedder = create_embedder()
    print(f"  ✅ create_embedder() 成功")
    print(f"  模型类型: {type(embedder).__name__}")
    
    # 测试编码
    test_texts = ["这是一个测试", "hello world", ""]
    for t in test_texts:
        vec = embedder.encode(t)
        status = "✅" if vec is not None and len(vec) > 0 else "❌"
        print(f"  {status} 编码 '{t[:10]}...' → 向量长度: {len(vec) if vec else 'None'}")
        
except Exception as e:
    print(f"  ❌ 嵌入模型加载失败: {e}")

# ── 3. 相似度计算诊断 ──
print("\n【3】VectorLayer 相似度计算诊断")
try:
    from plugin.session.session_cutter import VectorLayer
    vl = VectorLayer(embedder=embedder)
    
    # 取 4月19日前 20 条有内容的消息，逐轮计算相似度
    c.execute("""
        SELECT content_text, has_code 
        FROM sessions 
        WHERE date(timestamp) = '2026-04-19' 
          AND content_text IS NOT NULL 
          AND content_text != '' 
        ORDER BY timestamp 
        LIMIT 20 
    """)
    msgs = c.fetchall()
    
    print(f"  测试消息数: {len(msgs)}")
    similarities = []
    
    for i, (content, has_code) in enumerate(msgs):
        vec = vl.add_turn(content)
        if i > 0 and vec is not None:
            session_avg = vl.get_session_average_vector()
            if session_avg:
                sim = vl.compute_similarity(vec, session_avg)
                similarities.append(sim)
                marker = "🔪" if sim < 0.15 else "✅" if sim > 0.40 else "⚠️"
                print(f"  {marker} 第{i}轮: sim={sim:.3f} | '{content[:30]}...'")
    
    if similarities:
        import statistics
        print(f"\n  相似度统计:")
        print(f"    最小: {min(similarities):.3f}")
        print(f"    最大: {max(similarities):.3f}")
        print(f"    平均: {statistics.mean(similarities):.3f}")
        print(f"    中位数: {statistics.median(similarities):.3f}")
        
        low = sum(1 for s in similarities if s < 0.15)
        high = sum(1 for s in similarities if s > 0.40)
        print(f"    <0.15 (会切): {low}/{len(similarities)} ({low/len(similarities)*100:.1f}%)")
        print(f"    >0.40 (延续): {high}/{len(similarities)} ({high/len(similarities)*100:.1f}%)")

except Exception as e:
    print(f"  ❌ VectorLayer 诊断失败: {e}")
    import traceback
    traceback.print_exc()

conn.close()

print("\n" + "=" * 70)
print("🔚 诊断结束")
print("=" * 70)