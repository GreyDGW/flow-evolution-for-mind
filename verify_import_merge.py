#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤4验证：全量导入 + 合并效果检查
"""

import sqlite3

db_path = 'data/flow_ecosystem.db'

print("=" * 80)
print("【步骤4验证：导入 + 合并效果】")
print("=" * 80)

conn = sqlite3.connect(db_path)
c = conn.cursor()

# 检查表是否存在
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
if not c.fetchone():
    print("\n❌ sessions 表不存在！需要先执行 init.py")
    exit(1)

print("\n📊 总体统计:")
print("-" * 60)

c.execute("""
    SELECT 
        COUNT(*) as total_msgs,
        COUNT(DISTINCT session_id) as unique_sessions,
        SUM(CASE WHEN role='user' THEN 1 ELSE 0 END) as user_count,
        SUM(CASE WHEN role='assistant' THEN 1 ELSE 0 END) as assistant_count,
        ROUND(
            SUM(CASE WHEN role='user' THEN 1 ELSE 0 END) * 1.0 / 
            NULLIF(SUM(CASE WHEN role='assistant' THEN 1 ELSE 0 END), 0),
        2) as ua_ratio
    FROM sessions
    WHERE (is_system_noise=0 OR is_system_noise IS NULL)
      AND (is_auto_push=0 OR is_auto_push IS NULL)
""")

row = c.fetchone()
if row[0] == 0:
    print("\n⚠️ 数据库为空！可能原因:")
    print("   1. init.py 判断数据库非空，跳过了导入")
    print("   2. JSONL 文件路径不正确")
    print("   3. 所有文件都被排除(.reset/.checkpoint)")
    
    # 检查原始表状态
    print("\n📋 原始统计（包含所有标记）:")
    c.execute("SELECT COUNT(*) FROM sessions")
    total_all = c.fetchone()[0]
    print(f"   总消息数(含噪声): {total_all}")
    
    if total_all > 0:
        c.execute("""
            SELECT role, COUNT(*) 
            FROM sessions 
            GROUP BY role
        """)
        print("\n   Role分布:")
        for r in c.fetchall():
            print(f"     {r[0]}: {r[1]}")
else:
    print(f"\n  总消息数: {row[0]}")
    print(f"  唯一Session数: {row[1]}")
    print(f"  User消息: {row[2]}")
    print(f"  Assistant消息: {row[3]}")
    print(f"  U:A比值: {row[4]}")
    
    # 评估U:A比值
    ua_ratio = row[4]
    if ua_ratio and 0.8 <= float(ua_ratio) <= 0.9:
        print(f"\n  ✅ U:A比值达标 ({ua_ratio} ∈ [0.8-0.9])")
    elif ua_ratio and float(ua_ratio) >= 0.7:
        print(f"\n  🟡 U:A比值可接受 ({ua_ratio}，目标 0.8-0.9)")
    else:
        print(f"\n  ⚠️ U:A比值偏低 ({ua_ratio}，可能仍有流式分段未合并)")

# 流式分段残留检测
print("\n" + "=" * 80)
print("🔍 连续分段残留检测:")
print("=" * 80)

c.execute("""
    WITH pairs AS (
        SELECT 
            session_id,
            (julianday(timestamp)-julianday(LAG(timestamp) OVER (PARTITION BY session_id ORDER BY timestamp)))*86400 as gap,
            role,
            LAG(role) OVER (PARTITION BY session_id ORDER BY timestamp) as prev_role
        FROM sessions
        WHERE role='assistant' 
          AND (is_system_noise=0 OR is_system_noise IS NULL) 
          AND (is_auto_push=0 OR is_auto_push IS NULL)
    )
    SELECT COUNT(*) as remaining_segments 
    FROM pairs 
    WHERE prev_role='assistant' AND gap < 30
""")

segment_row = c.fetchone()
remaining = segment_row[0]

print(f"\n  残留的连续Assistant分段对数(间隔<30秒): {remaining}")

if remaining == 0:
    print("  ✅ 完美！无流式分段残留")
elif remaining <= 5:
    print(f"  🟡 极少量残留({remaining}对)，可接受")
elif remaining <= 20:
    print(f"  ⚠️ 有一定数量残留({remaining}对)，建议检查")
else:
    print(f"  ❌ 大量残留({remaining}对)，合并函数可能未生效")

# 详细查看残留样本（如果有）
if remaining > 0:
    print("\n  📝 残留样本（前5对）:")
    c.execute("""
        SELECT 
            session_id,
            SUBSTR(LAG(content_text) OVER (PARTITION BY session_id ORDER BY timestamp), 1, 50) as part1,
            SUBSTR(content_text, 1, 50) as part2,
            ROUND(gap, 2) as gap_sec
        FROM pairs
        WHERE prev_role='assistant' AND gap < 30
        LIMIT 5
    """)
    
    for i, r in enumerate(c.fetchall(), 1):
        sid = r[0][:40] + '..' if len(r[0]) > 42 else r[0]
        p1 = r[1] or '(空)'
        p2 = r[2] or '(空)'
        gap = r[3]
        print(f"\n    [{i}] Session: {sid}")
        print(f"        Part1: {p1}")
        print(f"        Part2: {p2}")
        print(f"        间隔: {gap}秒")

conn.close()

print("\n" + "=" * 80)
print("【验证完成】")
print("=" * 80)

print("\n判断标准:")
print("1. U:A 比值应在 0.8-0.9 范围内（当前实际值已显示上方）")
print("2. remaining_segments 应接近 0（当前实际值已显示上方）")
print("3. 如果两项都达标，说明流式合并修复成功！")
