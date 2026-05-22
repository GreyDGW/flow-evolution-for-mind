#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

db_path = 'data/flow_ecosystem.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("=" * 80)
print("B. 检查旧数据的 is_system_noise 分布")
print("=" * 80)

c.execute("""
    SELECT 
        is_system_noise,
        COUNT(*) as count,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as pct
    FROM sessions
    GROUP BY is_system_noise
    ORDER BY is_system_noise
""")

print(f"\n{'is_system_noise':<20} {'数量':>10} {'占比':>8}")
print("-" * 45)
for row in c.fetchall():
    noise_val = str(row[0]) if row[0] is not None else 'NULL'
    print(f"{noise_val:<20} {row[1]:>10} {row[2]:>7}%")

print("\n--- is_system_noise=1 的典型内容 ---")
c.execute("""
    SELECT 
        role,
        SUBSTR(content_text, 1, 60) as preview,
        COUNT(*) as count
    FROM sessions
    WHERE is_system_noise = 1
    GROUP BY role, preview
    ORDER BY count DESC
    LIMIT 10
""")

print(f"\n{'Role':<12} {'Content Preview':<50} {'数量':>6}")
print("-" * 75)
for row in c.fetchall():
    preview = row[1][:48] + '..' if len(row[1]) > 50 else row[1]
    print(f"{row[0]:<12} {preview:<50} {row[2]:>6}")

if c.rowcount == 0:
    print("⚠️ 未找到 is_system_noise=1 的记录")

print("\n" + "=" * 80)
print("C. 检查短session中消息的 is_system_noise 值")
print("=" * 80)

c.execute("""
    WITH short_sessions AS (
        SELECT session_id
        FROM sessions
        WHERE session_id LIKE '%#%'
        GROUP BY session_id
        HAVING COUNT(*) <= 5
        LIMIT 20
    )
    SELECT 
        s.is_system_noise,
        s.is_auto_push,
        s.role,
        SUBSTR(s.content_text, 1, 60) as preview,
        COUNT(*) as count
    FROM sessions s
    JOIN short_sessions ss ON s.session_id = ss.session_id
    GROUP BY s.is_system_noise, s.is_auto_push, s.role, preview
    ORDER BY count DESC
    LIMIT 20
""")

print(f"\n{'is_system_noise':<18} {'is_auto_push':<14} {'Role':<10} {'Preview':<45} {'数量':>5}")
print("-" * 100)
for row in c.fetchall():
    noise = str(row[0]) if row[0] is not None else 'NULL'
    push = str(row[1]) if row[1] is not None else 'NULL'
    role = row[2] if row[2] else ''
    preview = (row[3][:43] + '..') if row[3] and len(row[3]) > 45 else (row[3] or '')
    print(f"{noise:<18} {push:<14} {role:<10} {preview:<45} {row[4]:>5}")

conn.close()

print("\n" + "=" * 80)
print("D. 检查切割时是否过滤了 is_system_noise")
print("=" * 80)
