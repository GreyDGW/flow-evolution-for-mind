#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
切割后数据有效性抽检 v2 - 诊断版（先检查数据量）
"""

import sqlite3

db_path = 'data/flow_ecosystem.db'

print("=" * 80)
print("【切割后数据有效性抽检 - 诊断版】")
print("=" * 80)

conn = sqlite3.connect(db_path)
c = conn.cursor()

# 步骤1: 检查数据总量
print("\n📊 数据库现状:")
print("-" * 60)

c.execute("SELECT COUNT(*) FROM sessions WHERE session_id LIKE '%#%'")
cut_count = c.fetchone()[0]
print(f"切割后Session总数: {cut_count}")

c.execute("""
    SELECT COUNT(*) 
    FROM sessions 
    WHERE session_id LIKE '%#%'
      AND (is_system_noise = 0 OR is_system_noise IS NULL)
      AND (is_auto_push = 0 OR is_auto_push IS NULL)
      AND role IN ('user', 'assistant')
""")
valid_count = c.fetchone()[0]
print(f"有效消息数(纯净+user/assistant): {valid_count}")

if valid_count == 0:
    print("\n⚠️ 未找到符合条件的消息，尝试放宽条件...")
    
    # 检查各种条件组合
    conditions = [
        ("仅切割后", "session_id LIKE '%#%'"),
        ("+ 去噪声", "session_id LIKE '%#%' AND (is_system_noise = 0 OR is_system_noise IS NULL)"),
        ("+ 去自动推送", "session_id LIKE '%#%' AND (is_auto_push = 0 OR is_auto_push IS NULL)"),
        ("+ 只要user/assistant", "session_id LIKE '%#%' AND role IN ('user', 'assistant')"),
        ("全部条件", "session_id LIKE '%#%' AND (is_system_noise = 0 OR is_system_noise IS NULL) AND (is_auto_push = 0 OR is_auto_push IS NULL) AND role IN ('user', 'assistant')"),
    ]
    
    for desc, cond in conditions:
        c.execute(f"SELECT COUNT(*) FROM sessions WHERE {cond}")
        count = c.fetchone()[0]
        print(f"  {desc}: {count} 条")

# 如果有数据，继续抽检
if valid_count > 0:
    # 查询1: 随机抽取100条（或所有如果<100）
    sample_size = min(100, valid_count)
    
    print(f"\n📋 随机抽取 {sample_size} 条切割后Session的消息:")
    print("-" * 120)

    c.execute(f"""
        WITH cut_sessions AS (
            SELECT DISTINCT session_id
            FROM sessions
            WHERE session_id LIKE '%#%'
              AND (is_system_noise = 0 OR is_system_noise IS NULL)
              AND (is_auto_push = 0 OR is_auto_push IS NULL)
        )
        SELECT
            s.session_id,
            s.role,
            SUBSTR(s.content_text, 1, 120) as content_preview,
            s.agent_id,
            s.is_system_noise,
            s.is_auto_push
        FROM sessions s
        JOIN cut_sessions cs ON s.session_id = cs.session_id
        WHERE s.role IN ('user', 'assistant')
        ORDER BY RANDOM()
        LIMIT {sample_size}
    """)

    rows = c.fetchall()
    print(f"\n实际抽取: {len(rows)} 条\n")

    # 显示前30条
    display_count = min(30, len(rows))
    for i, row in enumerate(rows[:display_count], 1):
        sid = row[0][:35] + '..' if len(row[0]) > 37 else row[0]
        role = f"{row[1]:<10}"
        preview = (row[2][:115] + '..') if row[2] and len(row[2]) > 120 else (row[2] or '(空)')
        
        print(f"[{i:3d}] {sid} | {role} | {preview}")

    if len(rows) > display_count:
        print(f"\n... 还有 {len(rows) - display_count} 条未显示")

    # 查询2: Role分布统计
    print("\n" + "=" * 80)
    print("📊 Role 分布统计:")
    print("=" * 80)

    c.execute(f"""
        WITH sample_{sample_size} AS (
            SELECT session_id, role, content_text, agent_id, is_system_noise, is_auto_push
            FROM sessions
            WHERE session_id LIKE '%#%'
              AND (is_system_noise = 0 OR is_system_noise IS NULL)
              AND (is_auto_push = 0 OR is_auto_push IS NULL)
              AND role IN ('user', 'assistant')
            ORDER BY RANDOM()
            LIMIT {sample_size}
        )
        SELECT
            role,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / {sample_size}, 0) as pct,
            COUNT(DISTINCT agent_id) as agents,
            MIN(LENGTH(content_text)) as min_len,
            MAX(LENGTH(content_text)) as max_len,
            ROUND(AVG(LENGTH(content_text)), 0) as avg_len
        FROM sample_{sample_size}
        GROUP BY role
    """)

    role_stats = c.fetchall()
    print(f"\n{'Role':<12} {'数量':>6} {'占比':>6} {'Agent数':>8} {'最短':>6} {'最长':>7} {'平均长度':>8}")
    print("-" * 60)

    total_user = 0
    total_assistant = 0

    for r in role_stats:
        role = r[0] or 'Unknown'
        count = r[1]
        pct = r[2]
        agents = r[3]
        min_len = r[4] or 0
        max_len = r[5] or 0
        avg_len = int(r[6]) if r[6] else 0
        
        print(f"{role:<12} {count:>6} {pct:>5}% {agents:>8} {min_len:>6} {max_len:>7} {avg_len:>8}")
        
        if role == 'user':
            total_user = count
        elif role == 'assistant':
            total_assistant = count

    if total_user + total_assistant > 0:
        ratio = total_assistant / total_user if total_user > 0 else 0
        print(f"\n{'汇总':<12} {total_user+total_assistant:>6} {'100%':>6} {'-':>8} {'-':>6} {'-':>7} {'-':>8}")
        print(f"\nU:A 比值: {ratio:.2f}")

    # 查询3: 异常内容检测
    print("\n" + "=" * 80)
    print("🔍 异常内容检测（关键词匹配）:")
    print("=" * 80)

    c.execute(f"""
        WITH sample_{sample_size} AS (
            SELECT session_id, role, content_text, agent_id
            FROM sessions
            WHERE session_id LIKE '%#%'
              AND (is_system_noise = 0 OR is_system_noise IS NULL)
              AND (is_auto_push = 0 OR is_auto_push IS NULL)
              AND role IN ('user', 'assistant')
            ORDER BY RANDOM()
            LIMIT {sample_size}
        )
        SELECT
            'HEARTBEAT残留' as check_item,
            COUNT(*) as count
        FROM sample_{sample_size}
        WHERE content_text LIKE '%HEARTBEAT%'
        UNION ALL
        SELECT
            'NO_REPLY残留',
            COUNT(*)
        FROM sample_{sample_size}
        WHERE content_text LIKE '%NO_REPLY%'
        UNION ALL
        SELECT
            'cron任务残留',
            COUNT(*)
        FROM sample_{sample_size}
        WHERE content_text LIKE '%[cron:%'
        UNION ALL
        SELECT
            'Agent中转残留',
            COUNT(*)
        FROM sample_{sample_size}
        WHERE content_text LIKE '%Agent-to-agent%'
        UNION ALL
        SELECT
            '纯确认残留(收到/已同步)',
            COUNT(*)
        FROM sample_{sample_size}
        WHERE content_text LIKE '收到%' OR content_text LIKE '%已同步%' OR content_text LIKE '%待命%'
    """)

    anomaly_results = c.fetchall()

    print(f"\n{'检测项':<25} {'发现数量':>10} {'状态'}")
    print("-" * 50)

    all_clean = True
    anomaly_details = []
    
    for item in anomaly_results:
        check_name = item[0]
        count = item[1]
        status = "✅ 无残留" if count == 0 else f"❌ 发现 {count} 条"
        if count > 0:
            all_clean = False
            anomaly_details.append((check_name, count))
        print(f"{check_name:<25} {count:>10} {status}")

    # 额外检测：空内容和极短内容
    print("\n--- 内容质量检查 ---")

    c.execute(f"""
        WITH sample_{sample_size} AS (
            SELECT content_text
            FROM sessions
            WHERE session_id LIKE '%#%'
              AND (is_system_noise = 0 OR is_system_noise IS NULL)
              AND (is_auto_push = 0 OR is_auto_push IS NULL)
              AND role IN ('user', 'assistant')
            ORDER BY RANDOM()
            LIMIT {sample_size}
        )
        SELECT
            CASE
                WHEN content_text IS NULL OR TRIM(content_text) = '' THEN '空内容'
                WHEN LENGTH(content_text) <= 5 THEN '极短(≤5字符)'
                WHEN LENGTH(content_text) <= 20 THEN '较短(≤20字符)'
                ELSE '正常(>20字符)'
            END as quality_category,
            COUNT(*) as count
        FROM sample_{sample_size}
        GROUP BY quality_category
    """)

    quality_stats = c.fetchall()
    print(f"\n{'质量分类':<18} {'数量':>6} {'占比':>6}")
    print("-" * 35)
    for cat, cnt in quality_stats:
        pct = round(cnt / sample_size * 100, 0) if sample_size > 0 else 0
        status = '⚠️' if '空' in cat or '极短' in cat else ('🟡' if '较短' in cat else '✅')
        print(f"{cat:<18} {cnt:>6} {pct:>5}% {status}")

    # 最终评估
    print("\n" + "=" * 80)
    print("【验证完成 - 数据质量评估】")
    print("=" * 80)

    if all_clean:
        print("\n✅ 数据质量优秀！")
        print(f"   - 所有异常检测项均为 0")
        print(f"   - {sample_size}条抽检消息全部为真实对话内容")
        print("   - 可以放心进入批量分析阶段")
    else:
        print("\n⚠️ 发现异常内容，需要进一步清理:")
        for name, cnt in anomaly_details:
            print(f"   - {name}: {cnt}条")
        print("\n   建议：运行 cleanup_historical_noise.py 再次清理")

else:
    print("\n❌ 无可抽检的数据！")
    print("   可能原因：")
    print("   1. 还未执行切割操作")
    print("   2. 过滤条件过于严格")
    print("   3. 数据库被清空")
    print("\n   建议：先运行 batch_session_cutter.py --date <日期> 进行切割")

conn.close()
print("\n" + "=" * 80)
