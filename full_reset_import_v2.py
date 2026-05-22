#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的数据重置、导入和切割流程（修复版）
- 重置数据库
- 清除导入状态
- 全量导入
- 批量切割
"""

import sqlite3
import subprocess
import sys
import os
from datetime import datetime

db_path = 'data/flow_ecosystem.db'
state_file = '.collect_state.json'

print("=" * 80)
print("【完整数据重置与重新导入流程 - 修复版】")
print("=" * 80)

# 步骤1: 备份数据库
print("\n📦 创建数据库备份...")
backup_name = f"data/flow_ecosystem_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
try:
    import shutil
    shutil.copy2(db_path, backup_name)
    print(f"✅ 备份完成: {backup_name}")
except Exception as e:
    print(f"❌ 备份失败: {e}")

# 步骤2: 清空所有相关表
print("\n🗑️ 清空数据表...")
conn = sqlite3.connect(db_path)
c = conn.cursor()

tables_to_clear = [
    "sessions",
    "session_analyses", 
    "kv_store",
    "agent_goals"
]

for table in tables_to_clear:
    try:
        c.execute(f"DELETE FROM {table}")
        print(f"  ✅ 清空 {table}: {c.rowcount} 行")
    except Exception as e:
        print(f"  ℹ️ 表 {table} 可能不存在")

try:
    c.execute("DELETE FROM sqlite_sequence WHERE name IN ('sessions', 'session_analyses', 'kv_store', 'agent_goals')")
    print("  ✅ 重置自增序列")
except:
    pass

conn.commit()
conn.close()

# 步骤3: 清除导入状态文件（关键！）
print(f"\n🔄 清除导入状态文件: {state_file}")
if os.path.exists(state_file):
    try:
        # 备份旧状态
        backup_state = f"{state_file}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.rename(state_file, backup_state)
        print(f"✅ 已备份并删除状态文件 → {backup_state}")
    except Exception as e:
        print(f"⚠️ 无法备份状态文件，尝试直接删除...")
        try:
            os.remove(state_file)
            print("✅ 已删除状态文件")
        except Exception as e2:
            print(f"❌ 删除失败: {e2}")
else:
    print("ℹ️ 状态文件不存在，无需清除")

# 验证空库
print("\n📊 空库验证:")
conn = sqlite3.connect(db_path)
c = conn.cursor()
for table in ['sessions', 'session_analyses', 'kv_store']:
    try:
        c.execute(f"SELECT COUNT(*) FROM {table}")
        count = c.fetchone()[0]
        status = "✅" if count == 0 else "⚠️"
        print(f"  {status} {table}: {count} 条")
    except:
        print(f"  ℹ️ {table}: 表不存在")
conn.close()

# 步骤4: 全量导入
print("\n" + "=" * 80)
print("📥 开始全量导入...")
print("=" * 80)

try:
    result = subprocess.run(
        [sys.executable, "adapters/openclaw/scripts/init.py"],
        capture_output=True,
        text=True,
        timeout=180,
        cwd=os.getcwd(),
        env={**os.environ, 'PYTHONPATH': os.getcwd()}
    )
    
    print("\n导入输出:")
    if result.stdout:
        output_lines = result.stdout.split('\n')
        for line in output_lines[-30:]:  # 显示最后30行
            print(f"  {line}")
    
    if result.stderr:
        print("\n错误/警告:")
        err_lines = result.stderr.split('\n')
        for line in err_lines[-15:]:
            print(f"  {line}")
    
    if result.returncode == 0:
        print("\n✅ 导入完成")
    else:
        print(f"\n⚠️ 导入返回码: {result.returncode}")
        
except subprocess.TimeoutExpired:
    print("❌ 导入超时（>180秒）")
except Exception as e:
    print(f"❌ 导入错误: {e}")

# 验证导入结果
print("\n📊 导入结果验证:")
conn = sqlite3.connect(db_path)
c = conn.cursor()

try:
    c.execute("""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(DISTINCT session_id) as unique_sessions,
            COUNT(DISTINCT agent_id) as agents
        FROM sessions
    """)
    row = c.fetchone()
    print(f"\n  总记录数: {row[0]}")
    print(f"  唯一Session: {row[1]}")
    print(f"  Agent数量: {row[2]}")
except Exception as e:
    print(f"❌ 查询失败: {e}")

# 噪音标记分布
print("\n🔍 is_system_noise 分布:")
try:
    c.execute("""
        SELECT 
            is_system_noise,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as pct
        FROM sessions
        GROUP BY is_system_noise
        ORDER BY is_system_noise
    """)
    rows = c.fetchall()
    for r in rows:
        noise_val = str(r[0]) if r[0] is not None else 'NULL'
        print(f"  {noise_val}: {r[1]} 条 ({r[2]}%)")
except Exception as e:
    print(f"  ❌ 查询失败: {e}")

conn.close()

# 步骤5: 批量切割
print("\n" + "=" * 80)
print("✂️ 批量切割Session")
print("=" * 80)

try:
    result = subprocess.run(
        [sys.executable, "batch_session_cutter.py"],
        capture_output=True,
        text=True,
        timeout=300,  # 5分钟超时
        cwd=os.getcwd()
    )
    
    print("\n切割输出:")
    if result.stdout:
        cut_lines = result.stdout.split('\n')
        for line in cut_lines[-50:]:  # 显示最后50行
            print(f"  {line}")
    
    if result.stderr and len(result.stderr.strip()) > 0:
        print("\n切割错误/警告:")
        err_lines = result.stderr.split('\n')
        for line in err_lines[-20:]:
            if line.strip():
                print(f"  {line}")
        
except subprocess.TimeoutExpired:
    print("❌ 切割超时（>300秒）")
except Exception as e:
    print(f"❌ 切割错误: {e}")

# 步骤6: 切割后统计分析
print("\n" + "=" * 80)
print("📈 切割后统计分析")
print("=" * 80)

conn = sqlite3.connect(db_path)
c = conn.cursor()

# 总体统计
print("\n【切割后总体统计】")
try:
    c.execute("""
        SELECT 
            COUNT(DISTINCT session_id) as cut_sessions,
            COUNT(*) as total_messages,
            ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT session_id), 1) as avg_per_session
        FROM sessions
        WHERE session_id LIKE '%#%'
          AND (is_system_noise = 0 OR is_system_noise IS NULL)
          AND (is_auto_push = 0 OR is_auto_push IS NULL)
    """)
    row = c.fetchone()
    print(f"  切割Session总数: {row[0]}")
    print(f"  总消息数: {row[1]}")
    print(f"  平均每Session: {row[2]} 条消息")
except Exception as e:
    print(f"  ❌ 查询失败: {e}")

# 消息数量分布
print("\n【Session长度分布】")
try:
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
    print(f"\n  {'长度区间':<18} {'数量':>8} {'占比':>8} {'状态'}")
    print(f"  {'-'*45}")
    for r in rows:
        status = '✅' if '正常' in r[0] or '良好' in r[0] or '优秀' in r[0] else ('⚠️' if '过短' in r[0] else '')
        print(f"  {r[0]:<18} {r[1]:>8} {r[2]:>7}% {status}")
except Exception as e:
    print(f"  ❌ 查询失败: {e}")

# U:A 比值
print("\n【User:Assistant 比值】")
try:
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
    print(f"  User消息: {row[0]}")
    print(f"  Assistant消息: {row[1]}")
    print(f"  U:A比值: {row[2]}")
except Exception as e:
    print(f"  ❌ 查询失败: {e}")

# 短session抽样检查（检查是否还有噪声）
print("\n【短Session内容抽样（前5个）】")
try:
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
            LIMIT 5
        )
        SELECT 
            s.session_id,
            s.role,
            SUBSTR(s.content_text, 1, 60) as preview,
            s.agent_id
        FROM sessions s
        JOIN short_sessions ss ON s.session_id = ss.session_id
        WHERE s.role IN ('user', 'assistant')
        ORDER BY s.session_id, s.timestamp
        LIMIT 15
    """)
    rows = c.fetchall()
    for i, r in enumerate(rows):
        sid = r[0][:35] + '..' if len(r[0]) > 37 else r[0]
        preview = r[2][:58] + '..' if len(r[2]) > 60 else r[2]
        print(f"  [{i+1}] {sid} | {r[1]:10} | {preview}")
    
    if not rows:
        print("  ✅ 无短Session（所有Session都>=6条消息）")
        
except Exception as e:
    print(f"  ❌ 抽样查询失败: {e}")

conn.close()

print("\n" + "=" * 80)
print("✅ 全链路验证完成！")
print("=" * 80)
