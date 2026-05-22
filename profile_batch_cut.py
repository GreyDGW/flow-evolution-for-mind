#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能剖析脚本 - 分析切割性能瓶颈
"""

import time
import sqlite3
from datetime import datetime

def log(msg):
    print(f'[{time.strftime("%H:%M:%S")}] {msg}', flush=True)

DB_PATH = 'data/flow_ecosystem.db'

def main():
    log('开始性能剖析切割')
    
    # 1. 连接数据库
    t0 = time.perf_counter()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    t1 = time.perf_counter()
    log(f'数据库连接: {(t1-t0)*1000:.1f}ms')
    
    # 2. 查找原始session
    t0 = time.perf_counter()
    c.execute("""
        SELECT session_id, COUNT(*) as msg_count
        FROM sessions
        WHERE session_id NOT LIKE '%#%'
          AND (is_system_noise = 0 OR is_system_noise IS NULL)
          AND (is_auto_push = 0 OR is_auto_push IS NULL)
        GROUP BY session_id
        HAVING COUNT(*) >= 2
    """)
    raw_sessions = c.fetchall()
    t1 = time.perf_counter()
    log(f'查找原始session: {(t1-t0)*1000:.1f}ms | 找到 {len(raw_sessions)} 个')
    
    if not raw_sessions:
        log('没有需要切割的session')
        return
    
    # 3. 加载模型
    log('开始加载 sentence-transformers 模型...')
    t0 = time.perf_counter()
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    model_load_time = time.perf_counter() - t0
    log(f'模型加载完成: {model_load_time:.1f}秒 ({model_load_time*1000:.0f}ms)')
    
    # 4. 导入相似度计算
    from sklearn.metrics.pairwise import cosine_similarity
    
    # 5. 逐个切割（只测前3个）
    total_embed = 0
    total_hardrule = 0
    total_sim = 0
    
    for idx, (session_id, msg_count) in enumerate(raw_sessions[:3], 1):
        log('')
        log(f'--- [{idx}/3] 切割 {session_id} ({msg_count}条消息) ---')
        
        # 读取消息
        t0 = time.perf_counter()
        c.execute("""
            SELECT role, content_text, timestamp
            FROM sessions
            WHERE session_id = ?
              AND role IN ('user', 'assistant')
              AND (is_system_noise = 0 OR is_system_noise IS NULL)
              AND (is_auto_push = 0 OR is_auto_push IS NULL)
            ORDER BY timestamp
        """, (session_id,))
        msgs = c.fetchall()
        t1 = time.perf_counter()
        log(f'  读取消息: {(t1-t0)*1000:.1f}ms | {len(msgs)}条')
        
        if len(msgs) < 2:
            log('  跳过：消息不足2条')
            continue
        
        # HardRules（时间间隔检测）
        t0 = time.perf_counter()
        cut_points = []
        for i in range(1, len(msgs)):
            try:
                prev_time = datetime.fromisoformat(msgs[i-1][2].replace('Z', '+00:00'))
                curr_time = datetime.fromisoformat(msgs[i][2].replace('Z', '+00:00'))
                if (curr_time - prev_time).total_seconds() > 900:
                    cut_points.append(i)
            except:
                pass
        t1 = time.perf_counter()
        hardrule_ms = (t1-t0)*1000
        total_hardrule += hardrule_ms
        log(f'  HardRules: {hardrule_ms:.1f}ms | 切割点: {len(cut_points)}个')
        
        # Embedding
        t0 = time.perf_counter()
        texts = [m[1] for m in msgs if m[1]]
        if texts:
            embeddings = model.encode(texts, show_progress_bar=False)
        t1 = time.perf_counter()
        embed_ms = (t1-t0)*1000
        total_embed += embed_ms
        per_msg = embed_ms / len(texts) if texts else 0
        log(f'  Embedding: {embed_ms:.1f}ms | {len(texts)}条 | 每条约 {per_msg:.1f}ms')
        
        # 相似度计算
        t0 = time.perf_counter()
        if len(texts) >= 2:
            for i in range(1, len(embeddings)):
                _ = cosine_similarity([embeddings[i-1]], [embeddings[i]])[0][0]
        t1 = time.perf_counter()
        sim_ms = (t1-t0)*1000
        total_sim += sim_ms
        log(f'  相似度计算: {sim_ms:.1f}ms')
        
        session_total = hardrule_ms + embed_ms + sim_ms
        log(f'  本session总计: {session_total:.1f}ms')
    
    # 汇总
    log('')
    log('========================================')
    log('性能剖析汇总（前3个session）')
    log('========================================')
    log(f'模型加载: {model_load_time:.1f}秒 (一次性)')
    log(f'HardRules总计: {total_hardrule:.1f}ms')
    log(f'Embedding总计: {total_embed:.1f}ms')
    log(f'相似度总计: {total_sim:.1f}ms')
    total_all = total_hardrule + total_embed + total_sim
    log(f'切割总计: {total_all:.1f}ms')
    total_with_load = model_load_time + total_all/1000
    log(f'模型加载占比: {model_load_time/total_with_load*100:.1f}%')
    log('========================================')

if __name__ == '__main__':
    main()
