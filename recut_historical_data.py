#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务3: 重新切割历史数据
- 使用修复后的代码重新处理
- 验证切割质量
"""

import sqlite3
import subprocess
import sys

db_path = 'data/flow_ecosystem.db'

print("=" * 80)
print("【任务3】重新切割历史数据")
print("=" * 80)

# 3.1 检查当前状态
print("\n--- 3.1 当前数据库状态 ---")
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("""
    SELECT
        CASE WHEN session_id LIKE '%#%' THEN '已切割' ELSE '原始' END as type,
        COUNT(DISTINCT session_id) as session_count,
        COUNT(*) as message_count,
        SUM(CASE WHEN is_system_noise = 1 THEN 1 ELSE 0 END) as noise_count
    FROM sessions
    GROUP BY CASE WHEN session_id LIKE '%#%' THEN '已切割' ELSE '原始' END
""")

print(f"{'类型':<10} {'Session数':>12} {'消息数':>12} {'噪声消息':>10}")
print("-" * 50)
for row in c.fetchall():
    print(f"{row[0]:<10} {row[1]:>12} {row[2]:>12} {row[3] or 0:>10}")

# 3.2 统计待切割的原始session（排除噪声）
print("\n--- 3.2 待切割的原始Session（纯净数据）---")
c.execute("""
    SELECT COUNT(DISTINCT session_id), COUNT(*)
    FROM sessions
    WHERE session_id NOT LIKE '%#%'
      AND role IN ('user', 'assistant')
      AND (is_auto_push = 0 OR is_auto_push IS NULL)
      AND (is_system_noise = 0 OR is_system_noise IS NULL)
    GROUP BY session_id
    HAVING COUNT(*) >= 4
""")
rows = c.fetchall()
if rows:
    total_sessions = len(rows)
    total_messages = sum(r[1] for r in rows)
    print(f"待切割Session数量: {total_sessions}")
    print(f"包含消息总数: {total_messages}")
else:
    print("✅ 所有符合条件的session已经切割完成或无需切割")

conn.close()

# 3.3 执行重新切割（使用修复后的代码）
print("\n" + "=" * 80)
print("--- 3.3 执行批量切割 ---")
print("=" * 80)

try:
    # 调用 batch_session_cutter.py 的主函数
    from batch_session_cutter import find_uncut_sessions, cut_session

    print("\n🔍 查找待切割的session...")
    uncut = find_uncut_sessions(db_path, since_minutes=525600)  # 1年范围
    print(f"找到 {len(uncut)} 个待切割的session")

    if len(uncut) > 0:
        print(f"\n🔪 开始切割前5个session（演示）...")
        success_count = 0
        fail_count = 0

        for i, sid in enumerate(uncut[:5]):  # 只处理前5个作为示例
            try:
                result = cut_session(sid, db_path)
                if result:
                    success_count += 1
                    print(f"  ✅ [{i+1}/{min(len(uncut),5)}] {sid[:40]}... 切割成功: {len(result)} 个子session")
                else:
                    fail_count += 1
                    print(f"  ⚠️ [{i+1}/{min(len(uncut),5)}] {sid[:40]}... 无需切割或失败")
            except Exception as e:
                fail_count += 1
                print(f"  ❌ [{i+1}/{min(len(uncut),5)}] {sid[:40]}... 错误: {str(e)[:50]}")

        print(f"\n切割结果: 成功 {success_count}, 失败/跳过 {fail_count}")

        if len(uncut) > 5:
            print(f"\nℹ️ 还有 {len(uncut) - 5} 个session未处理，可稍后运行完整切割:")
            print(f"   python3 batch_session_cutter.py --all")
    else:
        print("✅ 没有需要切割的session")

except ImportError as e:
    print(f"⚠️ 无法导入切割模块: {e}")
    print("尝试直接调用脚本...")
    result = subprocess.run(
        [sys.executable, "batch_session_cutter.py", "--help"],
        capture_output=True,
        text=True,
        timeout=30
    )
    print(result.stdout if result.stdout else result.stderr)

except Exception as e:
    print(f"❌ 切割过程出错: {e}")

# 3.4 验证切割后的数据质量
print("\n" + "=" * 80)
print("--- 3.4 切割后数据质量验证 ---")
print("=" * 80)

conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("""
    SELECT
        COUNT(DISTINCT session_id) as total_cut,
        COUNT(*) as total_msgs,
        ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT session_id), 1) as avg_per_session,
        SUM(CASE WHEN is_system_noise = 1 THEN 1 ELSE 0 END) as remaining_noise,
        MIN((SELECT COUNT(*) FROM sessions s2 WHERE s2.session_id = s.session_id)) as min_msgs,
        MAX((SELECT COUNT(*) FROM sessions s2 WHERE s2.session_id = s.session_id)) as max_msgs
    FROM sessions s
    WHERE s.session_id LIKE '%#%'
""")
row = c.fetchone()

print(f"\n【切割后统计】")
print(f"总切割Session数: {row[0]}")
print(f"总消息数: {row[1]}")
print(f"平均每Session: {row[2]} 条消息")
print(f"残留噪声: {row[3]} 条 {'✅ (无噪声)' if row[3] == 0 else '❌ 需要清理'}")
print(f"最短Session: {row[4]} 条")
print(f"最长Session: {row[5]} 条")

# 3.5 Session长度分布
print("\n--- Session长度分布 ---")
c.execute("""
    SELECT
        CASE
            WHEN cnt <= 3 THEN '1-3条(过短)'
            WHEN cnt <= 7 THEN '4-7条(正常)'
            WHEN cnt <= 15 THEN '8-15条(良好)'
            ELSE '>15条(优秀)'
        END as bucket,
        COUNT(*) as count,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as pct
    FROM (
        SELECT session_id, COUNT(*) as cnt
        FROM sessions
        WHERE session_id LIKE '%#%'
        GROUP BY session_id
    )
    GROUP BY bucket
    ORDER BY MIN(cnt)
""")

print(f"{'长度区间':<18} {'数量':>8} {'占比':>8}")
print("-" * 40)
for r in c.fetchall():
    status = '✅' if '正常' in r[0] or '良好' in r[0] or '优秀' in r[0] else '⚠️'
    print(f"{r[0]:<18} {r[1]:>8} {r[2]:>7}% {status}")

conn.close()

print("\n" + "=" * 80)
print("✅ 任务3完成：重新切割验证结束")
print("=" * 80)
