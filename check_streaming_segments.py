#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断脚本：检查流式分段特征
"""

import sqlite3

db_path = 'data/flow_ecosystem.db'

print("=" * 80)
print("【7. 流式分段特征检测】")
print("=" * 80)

conn = sqlite3.connect(db_path)
c = conn.cursor()

# 查询：找同一个session内连续assistant且间隔<30秒的例子
c.execute("""
    WITH assistant_msgs AS (
        SELECT 
            session_id, 
            timestamp, 
            content_text, 
            LAG(timestamp) OVER (PARTITION BY session_id ORDER BY timestamp) as prev_time, 
            LAG(content_text) OVER (PARTITION BY session_id ORDER BY timestamp) as prev_content 
        FROM sessions 
        WHERE role = 'assistant' 
          AND (is_system_noise = 0 OR is_system_noise IS NULL) 
          AND (is_auto_push = 0 OR is_auto_push IS NULL) 
    ) 
    SELECT 
        session_id, 
        SUBSTR(prev_content, 1, 50) as part1_preview, 
        SUBSTR(content_text, 1, 50) as part2_preview, 
        ROUND((julianday(timestamp) - julianday(prev_time)) * 86400, 2) as gap_seconds,
        LENGTH(prev_content) as len_part1,
        LENGTH(content_text) as len_part2
    FROM assistant_msgs 
    WHERE prev_time IS NOT NULL 
      AND (julianday(timestamp) - julianday(prev_time)) * 86400 < 30 
    ORDER BY gap_seconds ASC
    LIMIT 10
""")

rows = c.fetchall()

if rows:
    print(f"\n🔍 发现 {len(rows)} 对疑似流式分段（间隔<30秒的连续assistant消息）:\n")
    print(f"{'Session ID':<40} {'Part1预览':<45} {'Part2预览':<45} {'间隔(s)':>7} {'长度1':>6} {'长度2':>6}")
    print("-" * 160)
    
    for i, row in enumerate(rows, 1):
        sid = row[0][:38] + '..' if len(row[0]) > 40 else row[0]
        p1 = (row[1][:43] + '..') if row[1] and len(row[1]) > 45 else (row[1] or '(空)')
        p2 = (row[2][:43] + '..') if row[2] and len(row[2]) > 45 else (row[2] or '(空)')
        gap = row[3]
        l1 = row[4] or 0
        l2 = row[5] or 0
        
        print(f"\n[{i}] {sid}")
        print(f"    Part1 ({l1}字符): {p1}")
        print(f"    Part2 ({l2}字符): {p2}")
        print(f"    间隔: {gap}秒")
        
        # 判断是否像流式分段
        if l1 < 50 and l2 < 50:
            print("    🟡 可能是短消息快速回复")
        elif (p1 and p2) and ((p1 in p2[:min(len(p2), len(p1)+10)]) or (p2 in p1[:min(len(p1), len(p2)+10)])):
            print("    🔴 高度疑似：内容高度相似，可能是流式分段未合并")
        else:
            print("    ✅ 看起来是独立的消息")
else:
    print("\n✅ 未发现流式分段特征（无间隔<30秒的连续assistant消息对）")

# 统计总体情况
print("\n" + "=" * 80)
print("📊 总体统计:")
print("=" * 80)

c.execute("""
    SELECT 
        COUNT(*) as total_assistant_msgs,
        COUNT(DISTINCT session_id) as sessions_with_assistant,
        AVG(LENGTH(content_text)) as avg_length,
        MIN(LENGTH(content_text)) as min_len,
        MAX(LENGTH(content_text)) as max_len
    FROM sessions
    WHERE role = 'assistant'
      AND (is_system_noise = 0 OR is_system_noise IS NULL)
      AND (is_auto_push = 0 OR is_auto_push IS NULL)
""")
row = c.fetchone()

if row[0]:
    print(f"\nAssistant消息总数: {row[0]}")
    print(f"涉及Session数: {row[1]}")
    print(f"平均长度: {int(row[2]) or 0} 字符")
    print(f"最短: {row[3] or 0} 字符 | 最长: {row[4] or 0} 字符")

conn.close()
print("\n" + "=" * 80)
