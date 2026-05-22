#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能剖析脚本 v2 - 修复版（确保测试有消息的session）
"""

import time
import sqlite3
from datetime import datetime

def log(msg):
    print(f'[{time.strftime("%H:%M:%S")}] {msg}', flush=True)

DB_PATH = 'data/flow_ecosystem.db'

def main():
    log('开始性能剖析切割 v2')
    
    # 1. 连接数据库
    t0 = time.perf_counter()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    t1 = time.perf_counter()
    log(f'数据库连接: {(t1-t0)*1000:.1f}ms')
    
    # 2. 查找原始session（放宽条件，只看未切割的）
    t0 = time.perf_counter()
    c.execute("""
        SELECT session_id, COUNT(*) as msg_count
        FROM sessions
        WHERE session_id NOT LIKE '%#%'
        GROUP BY session_id
        HAVING COUNT(*) >= 4
        ORDER BY msg_count DESC
        LIMIT 10
    """)
    raw_sessions = c.fetchall()
    t1 = time.perf_counter()
    log(f'查找原始session: {(t1-t0)*1000:.1f}ms | 找到 {len(raw_sessions)} 个')
    
    if not raw_sessions:
        log('没有找到足够的原始session，尝试查找已切割的...')
        # 备选：查找已切割但消息较多的session
        c.execute("""
            SELECT session_id, COUNT(*) as msg_count
            FROM sessions
            WHERE session_id LIKE '%#%'
              AND (is_system_noise = 0 OR is_system_noise IS NULL)
            GROUP BY session_id
            HAVING COUNT(*) >= 6
            ORDER BY msg_count DESC
            LIMIT 10
        """)
        raw_sessions = c.fetchall()
        log(f'备选：找到 {len(raw_sessions)} 个已切割session (>=6条)')
    
    if not raw_sessions:
        log('没有需要分析的session')
        return
    
    # 显示前5个候选
    log('\n前5个候选session:')
    for i, (sid, cnt) in enumerate(raw_sessions[:5], 1):
        log(f'  [{i}] {sid[:40]}... ({cnt}条)')
    
    # 3. 加载模型
    log('\n开始加载 sentence-transformers 模型...')
    t0 = time.perf_counter()
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    model_load_time = time.perf_counter() - t0
    log(f'模型加载完成: {model_load_time:.1f}秒 ({model_load_time*1000:.0f}ms)')
    
    # 4. 导入相似度计算
    from sklearn.metrics.pairwise import cosine_similarity
    
    # 5. 逐个分析（取前3个有足够消息的）
    total_embed = 0
    total_hardrule = 0
    total_sim = 0
    tested = 0
    
    for idx, (session_id, msg_count) in enumerate(raw_sessions[:5], 1):
        if tested >= 3:
            break
            
        log('')
        log(f'--- 测试 [{idx}] Session: {session_id[:40]}... (总计{msg_count}条) ---')
        
        # 读取消息（不过滤，先看看有多少）
        t0 = time.perf_counter()
        if session_id.endswith('#') or '#' in session_id:
            # 已切割的session
            c.execute("""
                SELECT role, content_text, timestamp
                FROM sessions
                WHERE session_id = ?
                  AND role IN ('user', 'assistant')
                ORDER BY timestamp
            """, (session_id,))
        else:
            # 原始session
            c.execute("""
                SELECT role, content_text, timestamp
                FROM sessions
                WHERE session_id = ?
                  AND role IN ('user', 'assistant')
                  AND (is_auto_push = 0 OR is_auto_push IS NULL)
                ORDER BY timestamp
            """, (session_id,))
            
        msgs = c.fetchall()
        t1 = time.perf_counter()
        log(f'  读取消息: {(t1-t0)*1000:.1f}ms | {len(msgs)}条')
        
        if len(msgs) < 2:
            log(f'  跳过：消息不足2条')
            continue
        
        tested += 1
        
        # HardRules（时间间隔检测）
        t0 = time.perf_counter()
        cut_points = []
        for i in range(1, len(msgs)):
            try:
                ts_prev = msgs[i-1][2]
                ts_curr = msgs[i][2]
                
                # 处理各种时间格式
                if ts_prev and ts_curr:
                    prev_time = datetime.fromisoformat(ts_prev.replace('Z', '+00:00'))
                    curr_time = datetime.fromisoformat(ts_curr.replace('Z', '+00:00'))
                    diff = (curr_time - prev_time).total_seconds()
                    if diff > 900:  # 15分钟
                        cut_points.append(i)
            except Exception as e:
                pass
                
        t1 = time.perf_counter()
        hardrule_ms = (t1-t0)*1000
        total_hardrule += hardrule_ms
        log(f'  HardRules: {hardrule_ms:.1f}ms | 切割点: {len(cut_points)}个')
        
        # Embedding
        t0 = time.perf_counter()
        texts = [m[1] for m in msgs if m[1] and len(m[1].strip()) > 0]
        
        if texts:
            embeddings = model.encode(texts, show_progress_bar=False)
        else:
            embeddings = []
            log('  ⚠️ 无有效文本内容')
            
        t1 = time.perf_counter()
        embed_ms = (t1-t0)*1000
        total_embed += embed_ms
        per_msg = embed_ms / len(texts) if texts else 0
        log(f'  Embedding: {embed_ms:.1f}ms | 有效文本{len(texts)}条 | 每条约 {per_msg:.1f}ms')
        
        # 相似度计算
        t0 = time.perf_counter()
        sim_count = 0
        if len(embeddings) >= 2:
            for i in range(1, len(embeddings)):
                _ = cosine_similarity([embeddings[i-1]], [embeddings[i]])[0][0]
                sim_count += 1
        t1 = time.perf_counter()
        sim_ms = (t1-t0)*1000
        total_sim += sim_ms
        log(f'  相似度计算: {sim_ms:.1f}ms | 计算了{sim_count}对')
        
        session_total = hardrule_ms + embed_ms + sim_ms
        log(f'  本session总计: {session_total:.1f}ms')
    
    # 汇总
    log('')
    log('========================================')
    log('性能剖析汇总')
    log('========================================')
    log(f'测试Session数: {tested}')
    log(f'模型加载: {model_load_time:.1f}秒 (一次性成本)')
    log(f'HardRules总计: {total_hardrule:.1f}ms')
    log(f'Embedding总计: {total_embed:.1f}ms')
    log(f'相似度总计: {total_sim:.1f}ms')
    
    if tested > 0:
        total_all = total_hardrule + total_embed + total_sim
        avg_per_session = total_all / tested
        log(f'平均每Session: {avg_per_session:.1f}ms')
        
        total_with_load = model_load_time + total_all/1000
        load_pct = (model_load_time / total_with_load) * 100
        log(f'模型加载占比: {load_pct:.1f}%')
        
        # 性能评估
        log('')
        log('【性能评估】')
        if model_load_time < 20:
            log('✅ 模型加载速度: 快 (<20秒)')
        elif model_load_time < 30:
            log('✅ 模型加载速度: 正常 (20-30秒)')
        else:
            log('⚠️ 模型加载速度: 较慢 (>30秒)')
            
        if per_msg < 5:
            log('✅ Embedding效率: 高效 (<5ms/条)')
        elif per_msg < 10:
            log('✅ Embedding效率: 正常 (5-10ms/条)')
        else:
            log('⚠️ Embedding效率: 待优化 (>10ms/条)')
            
        if load_pct > 70:
            log('💡 瓶颈分析: 模型加载是主要耗时（建议缓存模型）')
        elif load_pct > 50:
            log('💡 瓶颈分析: 模型加载占比较大（可考虑预加载）')
        else:
            log('✅ 瓶颈分析: 切割计算本身是主要耗时')
    
    log('========================================')

if __name__ == '__main__':
    main()
