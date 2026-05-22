#!/usr/bin/env python3
# -*- coding: utf-8 -*-

path = 'adapters/openclaw/scripts/flow_handler.py'
with open(path, 'r') as f:
    lines = f.readlines()

# === 1. 数据库连接增加 timeout + WAL 模式 ===
new_lines = []
db_fix_count = 0
for line in lines:
    stripped = line.strip()
    indent = line[:len(line) - len(line.lstrip())]
    
    # 匹配变体 1: conn = sqlite3.connect(db_path)
    if stripped in ['conn = sqlite3.connect(db_path)', 'conn=sqlite3.connect(db_path)']:
        new_lines.append(indent + 'conn = sqlite3.connect(db_path, timeout=30)\n')
        new_lines.append(indent + 'conn.execute("PRAGMA journal_mode=WAL;")\n')
        db_fix_count += 1
    # 匹配变体 2: conn=sqlite3.connect(db_path); c=conn.cursor()
    elif 'conn=sqlite3.connect(db_path);' in line or 'conn = sqlite3.connect(db_path);' in line:
        new_lines.append(indent + 'conn = sqlite3.connect(db_path, timeout=30)\n')
        new_lines.append(indent + 'conn.execute("PRAGMA journal_mode=WAL;")\n')
        new_lines.append(indent + 'c = conn.cursor()\n')
        db_fix_count += 1
    # 匹配变体 3: conn = sqlite3.connect("data/flow_ecosystem.db")
    elif stripped in ['conn = sqlite3.connect("data/flow_ecosystem.db")', 'conn=sqlite3.connect("data/flow_ecosystem.db")']:
        new_lines.append(indent + 'conn = sqlite3.connect("data/flow_ecosystem.db", timeout=30)\n')
        new_lines.append(indent + 'conn.execute("PRAGMA journal_mode=WAL;")\n')
        db_fix_count += 1
    else:
        new_lines.append(line)

lines = new_lines
print(f"✅ 已修复 {db_fix_count} 处数据库连接")

# === 2. 注释 importer 导入 ===
importer_commented = False
for i, line in enumerate(lines):
    if 'from importer import incremental' in line and not line.strip().startswith('#'):
        lines[i] = '# [ARCH] Disabled: avoid DB lock. Background watcher handles sync.\n# ' + line
        importer_commented = True
        break

if importer_commented:
    print("✅ 已注释 importer 导入")
else:
    print("ℹ️ importer 导入已注释或未找到")

# === 3. 注释 run_once 调用块（找到 imported = incremental.run_once( 及其缩进块）===
start_idx = None
for i, line in enumerate(lines):
    if 'imported = incremental.run_once(' in line and not line.strip().startswith('#'):
        start_idx = i
        break

if start_idx is not None:
    base_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())
    end_idx = start_idx + 1
    while end_idx < len(lines):
        line = lines[end_idx]
        if line.strip() == '' or line.strip().startswith('#'):
            end_idx += 1
            continue
        curr_indent = len(line) - len(line.lstrip())
        if curr_indent <= base_indent:
            break
        end_idx += 1
    
    for i in range(start_idx, end_idx):
        lines[i] = '# [ARCH] Disabled: ' + lines[i]
    print(f"✅ 已注释 run_once 块 (行 {start_idx+1} ~ {end_idx})")
else:
    print("ℹ️ 未找到 run_once 调用（可能已被注释）")

# === 4. 文件顶部增加架构注释 ===
arch_note = '''# [ARCHITECTURE NOTE] 
# This script is PURE REPORT GENERATOR. It does NOT: 
#   - Sync data (handled by background importer/watcher) 
#   - Cut sessions (handled by batch_session_cutter.py cron) 
#   - Analyze sessions (handled by batch_analyze_with_save.py cron) 
# It ONLY reads from DB and prints the report to stdout. 
# This prevents "database is locked" errors when background processes write. 
# 
# [PLATFORM NOTE] 
# OpenClaw's "secretary" Agent has a built-in /flow shortcut that CANNOT be 
# overridden by external Skills. Use /deepflow or /cognitive-report instead. 
# See SKILL.md for trigger word configuration. 
# 
''' 
if '[ARCHITECTURE NOTE]' not in ''.join(lines):
    lines.insert(0, arch_note)
    print("✅ 已添加架构注释")
else:
    print("ℹ️ 架构注释已存在")

with open(path, 'w') as f:
    f.writelines(lines)

print("\n✅ flow_handler.py 修复完成")
