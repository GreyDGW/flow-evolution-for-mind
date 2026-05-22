#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务2: 全局搜索 - 检查所有模块的is_system_noise过滤情况
"""

import os
import re
from pathlib import Path

print("=" * 80)
print("【任务2】全局搜索 is_system_noise 过滤情况")
print("=" * 80)

# 搜索范围：排除 .venv 和 __pycache__
project_root = Path('.')
python_files = []
for root, dirs, files in os.walk(project_root):
    # 跳过虚拟环境和缓存目录
    dirs[:] = [d for d in dirs if d not in ['.venv', '__pycache__', '.git', 'node_modules', 'dist']]
    for file in files:
        if file.endswith('.py'):
            python_files.append(os.path.join(root, file))

print(f"\n📂 扫描范围: {len(python_files)} 个Python文件")

# 存储结果
results = {
    'has_filter': [],      # 有过滤的文件
    'missing_filter': [],  # 缺少过滤的文件（高风险）
    'no_sessions_query': [] # 不查询sessions表的文件
}

# 正则模式匹配SQL查询
session_query_pattern = re.compile(
    r'FROM\s+sessions\b[^;]*WHERE',
    re.IGNORECASE | re.DOTALL
)

noise_filter_pattern = re.compile(
    r'is_system_noise',
    re.IGNORECASE
)

for filepath in python_files:
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.split('\n')

        # 检查是否有sessions表查询
        has_sessions_query = bool(session_query_pattern.search(content))

        if not has_sessions_query:
            results['no_sessions_query'].append(filepath)
            continue

        # 检查是否有is_system_noise过滤
        has_noise_filter = bool(noise_filter_pattern.search(content))

        if has_noise_filter:
            # 找到具体的行号
            noise_lines = [(i+1, line.strip()) for i, line in enumerate(lines) if 'is_system_noise' in line.lower()]
            results['has_filter'].append({
                'file': filepath,
                'lines': noise_lines[:5]  # 只取前5个匹配
            })
        else:
            # 找到缺少过滤的SQL查询位置
            query_lines = []
            for i, line in enumerate(lines):
                if 'from sessions' in line.lower() and 'where' in line.lower():
                    context_start = max(0, i-2)
                    context_end = min(len(lines), i+3)
                    query_lines.append((i+1, '\n'.join(lines[context_start:context_end])))
                    if len(query_lines) >= 3:
                        break

            results['missing_filter'].append({
                'file': filepath,
                'queries': query_lines[:3]  # 只取前3个查询
            })

    except Exception as e:
        print(f"⚠️ 无法读取 {filepath}: {e}")

# 输出报告
print("\n" + "=" * 80)
print("【诊断报告】")
print("=" * 80)

print(f"\n✅ 已正确过滤 is_system_noise 的文件 ({len(results['has_filter'])} 个):")
print("-" * 80)
for item in results['has_filter'][:10]:  # 显示前10个
    rel_path = os.path.relpath(item['file'])
    print(f"\n📄 {rel_path}")
    for line_num, line_content in item['lines']:
        print(f"   第{line_num}行: {line_content[:80]}...")

if len(results['has_filter']) > 10:
    print(f"\n   ... 还有 {len(results['has_filter']) - 10} 个文件")

print(f"\n❌ 缺少 is_system_noise 过滤的文件 ({len(results['missing_filter'])} 个) [高风险]:")
print("-" * 80)
for item in results['missing_filter'][:15]:  # 显示前15个
    rel_path = os.path.relpath(item['file'])
    print(f"\n📄 {rel_path}")
    for line_num, query_context in item['queries']:
        print(f"   第{line_num}行附近:")
        for ctx_line in query_context.split('\n'):
            print(f"      {ctx_line.strip()[:70]}")

if len(results['missing_filter']) > 15:
    print(f"\n   ... 还有 {len(results['missing_filter']) - 15} 个文件")

print(f"\nℹ️ 不涉及sessions表查询的文件 ({len(results['no_sessions_query'])} 个)")
print("   (这些文件无需关注)")

# 统计总结
print("\n" + "=" * 80)
print("【统计总结】")
print("=" * 80)
total_with_sessions = len(results['has_filter']) + len(results['missing_filter'])
print(f"\n总扫描Python文件数: {len(python_files)}")
print(f"涉及sessions表查询的文件: {total_with_sessions}")
print(f"  ✅ 已正确过滤: {len(results['has_filter'])} ({round(len(results['has_filter'])/max(total_with_sessions,1)*100, 1)}%)")
print(f"  ❌ 缺少过滤: {len(results['missing_filter'])} ({round(len(results['missing_filter'])/max(total_with_sessions,1)*100, 1)}%)")
print(f"不涉及sessions表的文件: {len(results['no_sessions_query'])}")

if results['missing_filter']:
    print("\n⚠️ 建议优先修复以下关键模块:")
    priority_files = ['batch_analyze_with_save.py', 'importer/incremental.py',
                     'plugin/session_analyzer.py', 'plugin/deep_report_final.py']
    for pf in priority_files:
        matching = [item for item in results['missing_filter'] if pf in item['file']]
        if matching:
            print(f"  🔴 {pf}")

print("\n" + "=" * 80)
print("✅ 任务2完成：全局搜索结束")
print("=" * 80)
