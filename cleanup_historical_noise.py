#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务1: 清理包含噪声的切割session
- 识别受污染的切割session
- 备份受影响数据
- 删除噪声session
"""

import sqlite3
from datetime import datetime

db_path = 'data/flow_ecosystem.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("=" * 80)
print("【任务1】清理历史噪声数据 - 诊断阶段")
print("=" * 80)

# 1.1 统计切割session中的噪声分布
print("\n--- 1.1 切割session中的is_system_noise分布 ---")
c.execute("""
    SELECT
        s.is_system_noise,
        COUNT(DISTINCT s.session_id) as affected_sessions,
        COUNT(*) as noise_messages,
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM sessions WHERE session_id LIKE '%#%'), 2) as pct_of_cut
    FROM sessions s
    WHERE s.session_id LIKE '%#%'
    GROUP BY s.is_system_noise
    ORDER BY s.is_system_noise
""")

print(f"{'is_system_noise':<18} {'受影响Session数':>16} {'噪声消息数':>12} {'占切割数据%':>12}")
print("-" * 65)
total_affected = 0
for row in c.fetchall():
    noise_val = str(row[0]) if row[0] is not None else 'NULL'
    print(f"{noise_val:<18} {row[1]:>16} {row[2]:>12} {row[3]:>11}%")
    if row[0] == 1:
        total_affected = row[1]

# 1.2 识别完全由噪声组成的短session（<=5条且全部是噪声）
print("\n--- 1.2 完全由噪声组成的短Session（应优先删除）---")
c.execute("""
    WITH noisy_short_sessions AS (
        SELECT
            s.session_id,
            COUNT(*) as total_msgs,
            SUM(CASE WHEN s.is_system_noise = 1 THEN 1 ELSE 0 END) as noise_count,
            ROUND(SUM(CASE WHEN s.is_system_noise = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as noise_pct
        FROM sessions s
        WHERE s.session_id LIKE '%#%'
        GROUP BY s.session_id
        HAVING COUNT(*) <= 5 AND SUM(CASE WHEN s.is_system_noise = 1 THEN 1 ELSE 0 END) = COUNT(*)
    )
    SELECT COUNT(*) as pure_noise_sessions, SUM(total_msgs) as total_noise_msgs
    FROM noisy_short_sessions
""")

row = c.fetchone()
print(f"纯噪声短Session数量: {row[0]}")
print(f"包含的总消息数: {row[1]}")

# 1.3 识别部分污染的session（有噪声但也有正常消息）
print("\n--- 1.3 部分污染的Session（混合了噪声和正常消息）---")
c.execute("""
    WITH mixed_sessions AS (
        SELECT
            s.session_id,
            COUNT(*) as total_msgs,
            SUM(CASE WHEN s.is_system_noise = 1 THEN 1 ELSE 0 END) as noise_count,
            SUM(CASE WHEN s.is_system_noise = 0 THEN 1 ELSE 0 END) as clean_count
        FROM sessions s
        WHERE s.session_id LIKE '%#%'
        GROUP BY s.session_id
        HAVING SUM(CASE WHEN s.is_system_noise = 1 THEN 1 ELSE 0 END) > 0
           AND SUM(CASE WHEN s.is_system_noise = 0 THEN 1 ELSE 0 END) > 0
    )
    SELECT COUNT(*) as mixed_session_count, SUM(total_msgs) as total_msgs_in_mixed,
           SUM(noise_count) as total_noise_in_mixed, SUM(clean_count) as total_clean_in_mixed
    FROM mixed_sessions
""")

row = c.fetchone()
print(f"部分污染Session数量: {row[0]}")
print(f"总消息数: {row[1]} (其中噪声: {row[2]}, 正常: {row[3]})")

# 1.4 创建备份表（安全措施）
print("\n--- 1.4 创建备份表 ---")
backup_table_name = f'sessions_backup_before_noise_cleanup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'

try:
    c.execute(f"""
        CREATE TABLE IF NOT EXISTS {backup_table_name} AS
        SELECT * FROM sessions WHERE session_id LIKE '%#%'
    """)
    conn.commit()
    print(f"✅ 已创建备份表: {backup_table_name}")
    print(f"   备份记录数: {c.execute(f'SELECT COUNT(*) FROM {backup_table_name}').fetchone()[0]}")
except Exception as e:
    print(f"❌ 备份失败: {e}")

# 1.5 执行清理操作
print("\n" + "=" * 80)
print("【任务1】执行清理操作")
print("=" * 80)

# 1.5.1 删除纯噪声短session（最安全）
print("\n--- 1.5.1 删除纯噪声短Session (< 6条消息且100%噪声) ---")
c.execute("""
    DELETE FROM sessions
    WHERE session_id IN (
        SELECT session_id
        FROM sessions
        WHERE session_id LIKE '%#%'
        GROUP BY session_id
        HAVING COUNT(*) <= 5
           AND SUM(CASE WHEN is_system_noise = 1 THEN 1 ELSE 0 END) = COUNT(*)
    )
""")
deleted_pure_noise = c.rowcount
conn.commit()
print(f"✅ 已删除纯噪声短Session: {deleted_pure_noise} 条消息")

# 1.5.2 从部分污染的session中删除噪声消息
print("\n--- 1.5.2 从混合Session中删除噪声消息（保留正常消息）---")
c.execute("""
    DELETE FROM sessions
    WHERE session_id LIKE '%#%'
      AND is_system_noise = 1
""")
deleted_noise_from_mixed = c.rowcount
conn.commit()
print(f"✅ 已从混合Session中删除噪声消息: {deleted_noise_from_mixed} 条")

# 1.6 验证清理结果
print("\n--- 1.6 清理后验证 ---")
c.execute("""
    SELECT
        COUNT(DISTINCT session_id) as remaining_sessions,
        COUNT(*) as remaining_messages,
        ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT session_id), 1) as avg_per_session,
        SUM(CASE WHEN is_system_noise = 1 THEN 1 ELSE 0 END) as remaining_noise
    FROM sessions
    WHERE session_id LIKE '%#%'
""")

row = c.fetchone()
print(f"\n【清理后统计】")
print(f"剩余切割Session数: {row[0]}")
print(f"剩余消息总数: {row[1]}")
print(f"平均每Session消息数: {row[2]}")
print(f"残留噪声消息数: {row[3]}")

if row[3] == 0:
    print("\n✅ 清理成功！所有切割Session已无噪声消息")
else:
    print(f"\n⚠️ 仍有 {row[3]} 条噪声消息残留，需进一步检查")

conn.close()
print("\n" + "=" * 80)
print("✅ 任务1完成：历史噪声数据清理")
print("=" * 80)
