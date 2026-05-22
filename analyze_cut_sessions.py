#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

db_path = 'data/flow_ecosystem.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("=" * 80)
print("查询 1: 总体切割 session 数量")
print("=" * 80)

c.execute("""
    SELECT 
        COUNT(DISTINCT session_id) as total_cut_sessions,
        COUNT(*) as total_messages,
        ROUND(AVG(msg_count), 1) as avg_messages_per_session
    FROM (
        SELECT session_id, COUNT(*) as msg_count
        FROM sessions
        WHERE session_id LIKE '%#%'
          AND (is_system_noise = 0 OR is_system_noise IS NULL)
          AND (is_auto_push = 0 OR is_auto_push IS NULL)
        GROUP BY session_id
    )
""")

row = c.fetchone()
print(f"切割后 Session 总数: {row[0]}")
print(f"消息总数: {row[1]}")
print(f"平均每 Session 消息数: {row[2]}")

print("\n" + "=" * 80)
print("查询 2: 消息数量分布（切割后的 session）")
print("=" * 80)

c.execute("""
    SELECT 
        CASE 
            WHEN msg_count <= 5 THEN '1-5条'
            WHEN msg_count <= 10 THEN '6-10条'
            WHEN msg_count <= 20 THEN '11-20条'
            WHEN msg_count <= 50 THEN '21-50条'
            ELSE '50条以上'
        END as size_bucket,
        COUNT(*) as session_count,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as pct,
        MIN(msg_count) as min_msgs,
        MAX(msg_count) as max_msgs
    FROM (
        SELECT session_id, COUNT(*) as msg_count
        FROM sessions
        WHERE session_id LIKE '%#%'
          AND (is_system_noise = 0 OR is_system_noise IS NULL)
          AND (is_auto_push = 0 OR is_auto_push IS NULL)
        GROUP BY session_id
    )
    GROUP BY size_bucket
    ORDER BY min_msgs
""")

print(f"{'消息数量区间':<15} {'Session数':>10} {'占比':>8} {'最小值':>6} {'最大值':>6}")
print("-" * 55)
for row in c.fetchall():
    print(f"{row[0]:<15} {row[1]:>10} {row[2]:>7}% {row[3]:>6} {row[4]:>6}")

print("\n" + "=" * 80)
print("查询 3: 前20个样本的 user:assistant 比例")
print("=" * 80)

c.execute("""
    SELECT 
        session_id,
        COUNT(*) as total,
        SUM(CASE WHEN role = 'user' THEN 1 ELSE 0 END) as user_count,
        SUM(CASE WHEN role = 'assistant' THEN 1 ELSE 0 END) as assistant_count,
        ROUND(
            SUM(CASE WHEN role = 'user' THEN 1 ELSE 0 END) * 1.0 / 
            NULLIF(SUM(CASE WHEN role = 'assistant' THEN 1 ELSE 0 END), 0),
        2) as user_assistant_ratio
    FROM sessions
    WHERE session_id LIKE '%#%'
      AND (is_system_noise = 0 OR is_system_noise IS NULL)
      AND (is_auto_push = 0 OR is_auto_push IS NULL)
    GROUP BY session_id
    ORDER BY total DESC
    LIMIT 20
""")

print(f"{'Session ID':<45} {'总数':>5} {'User':>6} {'Assistant':>10} {'U:A比值':>8}")
print("-" * 85)
for row in c.fetchall():
    # 截断过长的 session_id
    sid = row[0][:42] + '..' if len(row[0]) > 44 else row[0]
    print(f"{sid:<45} {row[1]:>5} {row[2]:>6} {row[3]:>10} {row[4]:>8}")

print("\n" + "=" * 80)
print("查询 4: 全局 user:assistant 汇总")
print("=" * 80)

c.execute("""
    SELECT 
        SUM(CASE WHEN role = 'user' THEN 1 ELSE 0 END) as total_user,
        SUM(CASE WHEN role = 'assistant' THEN 1 ELSE 0 END) as total_assistant,
        ROUND(
            SUM(CASE WHEN role = 'user' THEN 1 ELSE 0 END) * 1.0 / 
            NULLIF(SUM(CASE WHEN role = 'assistant' THEN 1 ELSE 0 END), 0),
        2) as global_ratio
    FROM sessions
    WHERE session_id LIKE '%#%'
      AND (is_system_noise = 0 OR is_system_noise IS NULL)
      AND (is_auto_push = 0 OR is_auto_push IS NULL)
""")

row = c.fetchone()
print(f"User 消息总数: {row[0]}")
print(f"Assistant 消息总数: {row[1]}")
print(f"全局 User:Assistant 比值: {row[2]}")

conn.close()
print("\n✅ 查询完成")
