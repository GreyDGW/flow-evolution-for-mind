#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补充步骤：对多个日期执行批量切割
"""

import sqlite3
import subprocess
import sys
import os

db_path = 'data/flow_ecosystem.db'

print("=" * 80)
print("【补充步骤】多日期批量切割")
print("=" * 80)

# 查找所有有原始session（无#后缀）的日期
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("\n📅 查找待切割的日期...")
c.execute("""
    SELECT DATE(timestamp) as date, 
           COUNT(DISTINCT session_id) as sessions,
           COUNT(*) as messages
    FROM sessions
    WHERE session_id NOT LIKE '%#%'
      AND (is_system_noise = 0 OR is_system_noise IS NULL)
      AND (is_auto_push = 0 OR is_auto_push IS NULL)
      AND role IN ('user', 'assistant')
    GROUP BY DATE(timestamp)
    ORDER BY date DESC
""")

dates_info = c.fetchall()
conn.close()

if not dates_info:
    print("✅ 所有session已切割完成！")
else:
    print(f"\n找到 {len(dates_info)} 个待切割日期:")
    print(f"{'日期':<12} {'Session数':>10} {'消息数':>10}")
    print(f"{'-'*35}")
    for d in dates_info:
        print(f"{d[0]:<12} {d[1]:>10} {d[2]:>10}")
    
    # 批量切割每个日期
    print("\n" + "=" * 80)
    print("✂️ 开始批量切割...")
    print("=" * 80)
    
    success_count = 0
    fail_count = 0
    
    for i, (date_str, sess_count, msg_count) in enumerate(dates_info):
        print(f"\n[{i+1}/{len(dates_info)}] 切割 {date_str} ({sess_count} sessions, {msg_count} msgs)...")
        
        try:
            result = subprocess.run(
                [sys.executable, "batch_session_cutter.py", "--date", date_str],
                capture_output=True,
                text=True,
                timeout=120,  # 每个日期2分钟超时
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                success_count += 1
                # 提取关键输出
                if result.stdout:
                    lines = result.stdout.split('\n')
                    for line in lines[-5:]:
                        if line.strip():
                            print(f"  ✅ {line}")
            else:
                fail_count += 1
                print(f"  ⚠️ 返回码: {result.returncode}")
                if result.stderr:
                    err_lines = result.stderr.split('\n')
                    for line in err_lines[-3:]:
                        if line.strip():
                            print(f"  ❌ {line}")
                            
        except subprocess.TimeoutExpired:
            fail_count += 1
            print(f"  ❌ 超时（>120秒）")
        except Exception as e:
            fail_count += 1
            print(f"  ❌ 错误: {e}")
    
    print("\n" + "=" * 80)
    print(f"切割完成: 成功 {success_count}/{len(dates_info)}, 失败 {fail_count}")
    print("=" * 80)

# 最终验证
print("\n📊 最终验证:")
conn = sqlite3.connect(db_path)
c = conn.cursor()

# 总体统计
c.execute("""
    SELECT 
        COUNT(DISTINCT CASE WHEN session_id LIKE '%#%' THEN session_id ELSE NULL END) as cut_sessions,
        COUNT(DISTINCT CASE WHEN session_id NOT LIKE '%#%' THEN session_id ELSE NULL END) as uncut_sessions,
        COUNT(*) as total_messages,
        ROUND(COUNT(CASE WHEN session_id LIKE '%#%' THEN 1 END) * 100.0 / COUNT(*), 1) as cut_pct
    FROM sessions
    WHERE (is_system_noise = 0 OR is_system_noise IS NULL)
      AND (is_auto_push = 0 OR is_auto_push IS NULL)
""")
row = c.fetchone()
print(f"\n  切割Session: {row[0]}")
print(f"  未切割Session: {row[1]}")
print(f"  总消息数: {row[2]}")
print(f"  切割比例: {row[3]}%")

# Session长度分布（只看切割后的）
print("\n【切割后Session长度分布】")
c.execute("""
    SELECT 
        CASE 
            WHEN msg_count <= 5 THEN '1-5条(过短)'
            WHEN msg_count <= 10 THEN '6-10条(正常)'
            WHEN msg_count <= 20 THEN '11-20条(良好)'
            ELSE '>20条(优秀)'
        END as size_bucket,
        COUNT(*) as session_count,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as pct
    FROM (
        SELECT session_id, COUNT(*) as msg_count
        FROM sessions
        WHERE session_id LIKE '%#%'
          AND (is_system_noise = 0 OR is_system_noise IS NULL)
          AND (is_auto_push = 0 OR is_auto_push IS NULL)
        GROUP BY session_id
    )
    GROUP BY size_bucket
    ORDER BY MIN(msg_count)
""")
rows = c.fetchall()
print(f"\n  {'长度区间':<18} {'数量':>8} {'占比':>8}")
for r in rows:
    status = '✅' if '正常' in r[0] or '良好' in r[0] or '优秀' in r[0] else ('⚠️' if '过短' in r[0] else '')
    print(f"  {r[0]:<18} {r[1]:>8} {r[2]:>7}% {status}")

# U:A比值
print("\n【User:Assistant 比值】")
c.execute("""
    SELECT 
        SUM(CASE WHEN role='user' THEN 1 ELSE 0 END) as user_count,
        SUM(CASE WHEN role='assistant' THEN 1 ELSE 0 END) as assistant_count,
        ROUND(
            SUM(CASE WHEN role='user' THEN 1 ELSE 0 END) * 1.0 /
            NULLIF(SUM(CASE WHEN role='assistant' THEN 1 ELSE 0 END), 0),
        2) as ratio
    FROM sessions
    WHERE session_id LIKE '%#%'
      AND (is_system_noise = 0 OR is_system_noise IS NULL)
      AND (is_auto_push = 0 OR is_auto_push IS NULL)
""")
row = c.fetchone()
print(f"  User: {row[0]} | Assistant: {row[1]} | U:A = {row[2]}")

# 噪声检查
print("\n【噪声残留检查】")
c.execute("""
    SELECT COUNT(*) 
    FROM sessions 
    WHERE session_id LIKE '%#%'
      AND is_system_noise = 1
""")
noise_count = c.fetchone()[0]
if noise_count == 0:
    print("  ✅ 切割后Session中无噪声残留")
else:
    print(f"  ⚠️ 仍有 {noise_count} 条噪声消息混入切割Session")

conn.close()

print("\n" + "=" * 80)
print("✅ 全部流程完成！")
print("=" * 80)
