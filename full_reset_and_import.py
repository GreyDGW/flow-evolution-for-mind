#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的数据重置、导入和切割流程
"""

import sqlite3
import subprocess
import sys
import os
from datetime import datetime

db_path = 'data/flow_ecosystem.db'

def run_sql(sql, description=""):
    """执行SQL并打印结果"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        c.execute(sql)
        if sql.strip().upper().startswith('SELECT'):
            results = c.fetchall()
            print(f"\n{description}")
            for row in results:
                print(row)
        else:
            conn.commit()
            print(f"✅ {description}: {c.rowcount} 行受影响")
    except Exception as e:
        print(f"⚠️ {description}: {e}")
    finally:
        conn.close()

print("=" * 80)
print("【完整数据重置与重新导入流程】")
print("=" * 80)

# 步骤1: 备份
print("\n📦 创建数据库备份...")
backup_name = f"data/flow_ecosystem_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
try:
    import shutil
    shutil.copy2(db_path, backup_name)
    print(f"✅ 备份完成: {backup_name}")
except Exception as e:
    print(f"❌ 备份失败: {e}")

# 步骤2: 清空表（只清空存在的表）
print("\n🗑️ 清空数据表...")
tables_to_clear = [
    "sessions",
    "session_analyses", 
    "kv_store",
    "agent_goals"
]

for table in tables_to_clear:
    try:
        run_sql(f"DELETE FROM {table}", f"清空 {table}")
    except Exception as e:
        print(f"ℹ️ 表 {table} 可能不存在或已清空")

# 重置自增序列
try:
    run_sql("DELETE FROM sqlite_sequence WHERE name IN ('sessions', 'session_analyses', 'kv_store', 'agent_goals')", "重置自增序列")
except:
    pass

# 验证空库
print("\n📊 空库验证:")
run_sql("""
    SELECT 'sessions' as tbl, COUNT(*) as cnt FROM sessions
    UNION ALL SELECT 'session_analyses', COUNT(*) FROM session_analyses
    UNION ALL SELECT 'kv_store', COUNT(*) FROM kv_store
    UNION ALL SELECT 'agent_goals', COUNT(*) FROM agent_goals
""", "各表记录数（应该都是0）")

# 步骤3: 全量导入
print("\n" + "=" * 80)
print("📥 开始全量导入...")
print("=" * 80)

try:
    result = subprocess.run(
        [sys.executable, "adapters/openclaw/scripts/init.py"],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=os.getcwd()
    )
    
    print("STDOUT:", result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr[-300:] if len(result.stderr) > 300 else result.stderr)
    
    if result.returncode == 0:
        print("\n✅ 导入完成")
    else:
        print(f"\n⚠️ 导入返回码: {result.returncode}")
        
except subprocess.TimeoutExpired:
    print("❌ 导入超时（>120秒）")
except Exception as e:
    print(f"❌ 导入错误: {e}")

# 验证导入结果
print("\n📊 导入结果验证:")
run_sql("""
    SELECT 
        COUNT(*) as total_rows,
        COUNT(DISTINCT session_id) as unique_sessions,
        COUNT(DISTINCT agent_id) as agents
    FROM sessions
""", "总体统计")

# 噪音标记分布
print("\n🔍 is_system_noise 分布:")
run_sql("""
    SELECT 
        is_system_noise,
        COUNT(*) as count,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as pct
    FROM sessions
    GROUP BY is_system_noise
""", "噪音标记分布")

# 步骤4: 批量切割
print("\n" + "=" * 80)
print("✂️ 批量切割Session")
print("=" * 80)

try:
    result = subprocess.run(
        [sys.executable, "batch_session_cutter.py"],
        capture_output=True,
        text=True,
        timeout=180,
        cwd=os.getcwd()
    )
    
    print("切割输出:")
    print(result.stdout[-1000:] if len(result.stdout) > 1000 else result.stdout)
    if result.stderr:
        print("错误/警告:")
        print(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
    
except subprocess.TimeoutExpired:
    print("❌ 切割超时（>180秒）")
except Exception as e:
    print(f"❌ 切割错误: {e}")

# 步骤5: 切割后统计
print("\n" + "=" * 80)
print("📈 切割后统计分析")
print("=" * 80)

# 总体统计
run_sql("""
    SELECT 
        COUNT(DISTINCT session_id) as cut_sessions,
        COUNT(*) as total_messages,
        ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT session_id), 1) as avg_per_session
    FROM sessions
    WHERE session_id LIKE '%#%'
      AND (is_system_noise = 0 OR is_system_noise IS NULL)
      AND (is_auto_push = 0 OR is_auto_push IS NULL)
""", "切割后总体统计")

# 消息数量分布
print("\n📊 Session长度分布:")
run_sql("""
    SELECT 
        CASE 
            WHEN msg_count <= 5 THEN '1-5条'
            WHEN msg_count <= 10 THEN '6-10条'
            WHEN msg_count <= 20 THEN '11-20条'
            WHEN msg_count <= 50 THEN '21-50条'
            ELSE '50条以上'
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
""", "消息数量分布")

# 短session抽样检查
print("\n🔬 短Session内容抽样（1-5条的前10个）:")
run_sql("""
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
        SUBSTR(s.content_text, 1, 80) as preview,
        s.agent_id
    FROM sessions s
    JOIN short_sessions ss ON s.session_id = ss.session_id
    WHERE s.role IN ('user', 'assistant')
    ORDER BY s.session_id, s.timestamp
    LIMIT 30
""", "短session内容抽样")

# U:A 比值
print("\n👥 User:Assistant 比值:")
run_sql("""
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
""", "全局U:A比值")

print("\n" + "=" * 80)
print("✅ 全链路验证完成！")
print("=" * 80)
