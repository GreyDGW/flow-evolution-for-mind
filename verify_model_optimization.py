#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证模型复用优化效果
"""

import sqlite3
import subprocess
import sys
import time
import os

db_path = 'data/flow_ecosystem.db'

print("=" * 80)
print("【验证：模型复用优化效果】")
print("=" * 80)

print("\n【预期行为】")
print("1. 只出现 1 次'嵌入模型已全局加载'")
print("2. 后续每个 session 出现'使用传入的嵌入模型（全局复用）'")
print("3. 不应该再出现'嵌入模型已加载（VectorLayer 可用）'")
print("4. 总时间应该 < 20 秒（之前约 60-90 秒）")

# 查看该日期的原始session
print("\n" + "=" * 80)
print("📅 2026-04-19 原始Session统计:")
print("=" * 80)

conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("""
    SELECT 
        session_id, 
        COUNT(*) as msg_count 
    FROM sessions 
    WHERE session_id NOT LIKE '%#%' 
      AND (is_system_noise = 0 OR is_system_noise IS NULL) 
      AND (is_auto_push = 0 OR is_auto_push IS NULL) 
      AND date(timestamp) = '2026-04-19' 
    GROUP BY session_id 
    ORDER BY msg_count DESC 
    LIMIT 5
""")

rows = c.fetchall()
if rows:
    print(f"\n找到 {len(rows)} 个待切割session（显示前5个）:")
    for i, (sid, cnt) in enumerate(rows, 1):
        sid_short = sid[:40] + '...' if len(sid) > 42 else sid
        print(f"  [{i}] {sid_short} ({cnt}条消息)")
else:
    print("\n⚠️ 未找到2026-04-19的未切割session")

conn.close()

# 执行切割并计时
print("\n" + "=" * 80)
print("✂️ 开始切割 2026-04-19（带时间统计）...")
print("=" * 80)

start_time = time.time()

try:
    result = subprocess.run(
        [sys.executable, "batch_session_cutter.py", "--date", "2026-04-19"],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=os.getcwd(),
        env={**os.environ, 'PYTHONPATH': os.getcwd()}
    )
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    # 输出完整日志
    if result.stdout:
        print("\n【切割日志】")
        lines = result.stdout.split('\n')
        for line in lines:
            if line.strip():
                print(f"  {line}")
    
    if result.stderr and len(result.stderr.strip()) > 0:
        print("\n【错误/警告日志】")
        err_lines = result.stderr.split('\n')
        for line in err_lines:
            if line.strip():
                print(f"  ⚠️ {line}")
    
    # 验证结果分析
    print("\n" + "=" * 80)
    print("【验证结果分析】")
    print("=" * 80)
    
    output_text = result.stdout
    
    # 统计关键日志出现次数
    global_load_count = output_text.count('嵌入模型已全局加载')
    reuse_count = output_text.count('使用传入的嵌入模型（全局复用）')
    vector_layer_count = output_text.count('嵌入模型已加载（VectorLayer 可用）')
    
    print(f"\n📊 模型加载日志统计:")
    print(f"  '嵌入模型已全局加载' 出现次数: {global_load_count} {'✅ (应为1)' if global_load_count == 1 else '❌'}")
    print(f"  '使用传入的嵌入模型（全局复用）' 出现次数: {reuse_count}")
    print(f"  '嵌入模型已加载（VectorLayer 可用）' 出现次数: {vector_layer_count} {'✅ (应为0)' if vector_layer_count == 0 else '❌'}")
    
    print(f"\n⏱️ 性能统计:")
    print(f"  总耗时: {elapsed:.2f} 秒")
    
    if elapsed < 20:
        print(f"  状态: ✅ 达标 (<20秒)")
    elif elapsed < 60:
        print(f"  状态: 🟡 可接受 (20-60秒)")
    else:
        print(f"  状态: ❌ 偏慢 (>60秒)")
    
    # 判断优化是否生效
    print(f"\n🎯 优化效果评估:")
    if global_load_count == 1 and vector_layer_count == 0:
        print(f"  ✅ 模型复用机制已生效！只加载了1次模型")
        if reuse_count > 0:
            print(f"  ✅ 成功复用了 {reuse_count} 次")
        
        if elapsed < 30:
            speedup = "显著提速"
        elif elapsed < 60:
            speedup = "明显改善"
        else:
            speedup = "需进一步检查"
            
        print(f"  ✅ 总体评价: {speedup}（{elapsed:.1f}秒 vs 之前估计60-90秒）")
    else:
        print(f"  ⚠️ 可能存在问题：")
        if global_load_count != 1:
            print(f"     - 全局加载出现{global_load_count}次（预期1次）")
        if vector_layer_count > 0:
            print(f"     - VectorLayer加载出现{vector_layer_count}次（预期0次）")
    
    # 返回码检查
    if result.returncode == 0:
        print(f"\n✅ 执行成功 (返回码: {result.returncode})")
    else:
        print(f"\n⚠️ 执行异常 (返回码: {result.returncode})")

except subprocess.TimeoutExpired:
    elapsed = time.time() - start_time
    print(f"\n❌ 超时！执行时间超过120秒")
    print(f"   已运行: {elapsed:.1f}秒")
    print("   这说明可能仍有性能问题")

except Exception as e:
    print(f"\n❌ 执行出错: {e}")

print("\n" + "=" * 80)
print("✅ 验证完成")
print("=" * 80)
