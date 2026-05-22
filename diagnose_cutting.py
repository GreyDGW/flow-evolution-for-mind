#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

db_path = 'data/flow_ecosystem.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("=" * 80)
print("B. 查看1-5条短session的实际内容（随机10个样本）")
print("=" * 80)

c.execute("""
    WITH short_sessions AS (
        SELECT session_id, COUNT(*) as msg_count
        FROM sessions
        WHERE session_id LIKE '%#%'
          AND (is_system_noise = 0 OR is_system_noise IS NULL)
          AND (is_auto_push = 0 OR is_auto_push IS NULL)
        GROUP BY session_id
        HAVING msg_count <= 5
        ORDER BY RANDOM()
        LIMIT 10
    )
    SELECT 
        s.session_id,
        s.role,
        SUBSTR(s.content_text, 1, 80) as content_preview,
        s.timestamp,
        s.agent_id
    FROM sessions s
    JOIN short_sessions ss ON s.session_id = ss.session_id
    WHERE s.role IN ('user', 'assistant')
    ORDER BY s.session_id, s.timestamp
    LIMIT 30
""")

rows = c.fetchall()
print(f"{'Session ID':<45} {'Role':<10} {'Content Preview':<45} {'Timestamp':<20} {'Agent'}")
print("-" * 140)
for row in rows:
    sid = row[0][:42] + '..' if len(row[0]) > 44 else row[0]
    preview = row[2][:43] + '..' if len(row[2]) > 45 else row[2]
    print(f"{sid:<45} {row[1]:<10} {preview:<45} {str(row[3]):<20} {row[4]}")

if not rows:
    print("⚠️ 未找到符合条件的记录")

print("\n" + "=" * 80)
print("C. 重新计算正确的消息总数")
print("=" * 80)

# 正确的消息总数
c.execute("""
    SELECT 
        COUNT(DISTINCT session_id) as cut_session_count,
        COUNT(*) as total_messages,
        ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT session_id), 1) as avg_per_session
    FROM sessions
    WHERE session_id LIKE '%#%'
      AND (is_system_noise = 0 OR is_system_noise IS NULL)
      AND (is_auto_push = 0 OR is_auto_push IS NULL)
""")
row = c.fetchone()
print(f"\n【切割后 Session 统计】")
print(f"Session 数量: {row[0]}")
print(f"消息总数（正确）: {row[1]}")
print(f"平均每 Session 消息数: {row[2]}")

# 对比原始 vs 切割后
c.execute("""
    SELECT 
        '原始session（无#后缀）' as type,
        COUNT(DISTINCT session_id) as session_count,
        COUNT(*) as message_count
    FROM sessions
    WHERE session_id NOT LIKE '%#%'
      AND (is_system_noise = 0 OR is_system_noise IS NULL)
      AND (is_auto_push = 0 OR is_auto_push IS NULL)
    UNION ALL
    SELECT 
        '切割后session（有#后缀）' as type,
        COUNT(DISTINCT session_id) as session_count,
        COUNT(*) as message_count
    FROM sessions
    WHERE session_id LIKE '%#%'
      AND (is_system_noise = 0 OR is_system_noise IS NULL)
      AND (is_auto_push = 0 OR is_auto_push IS NULL)
""")

print(f"\n【原始 vs 切割后 对比】")
print(f"{'类型':<25} {'Session 数':>12} {'消息数':>12}")
print("-" * 55)
for row in c.fetchall():
    print(f"{row[0]:<25} {row[1]:>12} {row[2]:>12}")

print("\n" + "=" * 80)
print("D. 查看切割来源（Top 15 原始 Session）")
print("=" * 80)

c.execute("""
    SELECT 
        REPLACE(REPLACE(session_id, '#1', ''), '#2', '') as original_id,
        COUNT(DISTINCT session_id) as cut_count,
        COUNT(*) as total_msgs
    FROM sessions
    WHERE session_id LIKE '%#%'
      AND (is_system_noise = 0 OR is_system_noise IS NULL)
      AND (is_auto_push = 0 OR is_auto_push IS NULL)
    GROUP BY original_id
    ORDER BY total_msgs DESC
    LIMIT 15
""")

print(f"\n{'原始 Session ID':<42} {'切割数':>8} {'总消息':>8}")
print("-" * 65)
for row in c.fetchall():
    oid = row[0][:40] + '..' if len(row[0]) > 42 else row[0]
    print(f"{oid:<42} {row[1]:>8} {row[2]:>8}")

conn.close()
print("\n✅ 诊断完成")
