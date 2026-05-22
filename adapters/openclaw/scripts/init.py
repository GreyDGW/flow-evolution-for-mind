#!/usr/bin/env python3
"""
安装初始化 —— 首次触发 Skill 时，若数据库为空则全量导入历史 jsonl
"""

import sys
import os

def find_core_dir():
    core_dir = os.getenv("FLOW_EVOLUTION_DIR")
    if core_dir and os.path.exists(core_dir):
        # V7.8-9-4-3 FIX: 首次安装时数据库不存在，只检查目录是否存在
        data_dir = os.path.join(core_dir, "data")
        if os.path.exists(data_dir) or os.path.exists(core_dir):
            return core_dir
    candidates = [
        os.path.expanduser("~/flow-evolution-for-mind"),
        os.path.expanduser("~/.flow-evolution-for-mind"),
        os.path.expanduser("~/Desktop/skill相关文档/openclaw_flow_plugin"),
    ]
    for c in candidates:
        # V7.8-9-4-3 FIX: 首次安装时数据库不存在，只检查目录是否存在
        if os.path.exists(c):
            return c
    return None

CORE_DIR = find_core_dir()
if not CORE_DIR:
    print("❌ 找不到核心层，跳过初始化", file=sys.stderr)
    sys.exit(1)

sys.path.insert(0, CORE_DIR)
os.chdir(CORE_DIR)

from importer.incremental import run_once
import sqlite3

def is_database_empty(db_path="data/flow_ecosystem.db"):
    if not os.path.exists(db_path):
        return True
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # V7.8-9-4-3: 检查 sessions 表是否存在且为空
    # 如果表不存在，也视为空（会在首次导入时自动创建）
    try:
        c.execute("SELECT COUNT(*) FROM sessions")
        count = c.fetchone()[0]
    except sqlite3.OperationalError:
        # 表不存在，视为空库
        count = 0
    conn.close()
    return count == 0

def create_kv_store(db_path="data/flow_ecosystem.db"):
    """创建泛用 Key-Value 表，用于调音系统的运行时状态存储"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS kv_store (
            agent_id TEXT,
            key TEXT,
            value TEXT,
            updated_at TEXT,
            PRIMARY KEY (agent_id, key)
        )
    ''')
    # V7.8-9-4-3: 不再预建 sessions 表
    # 原因：sessions 表结构由 _parse_jsonl_line() 动态决定，预建会导致字段不匹配
    # 解决方案：让 import_batch() 首次 INSERT 时自动创建
    conn.commit()
    conn.close()
    print("✅ kv_store 表创建/确认完成")

def run_full_import():
    print("🔄 首次安装，正在导入历史数据...", file=sys.stderr)
    try:
        imported = run_once()
        print(f"✅ 初始化完成，共导入 {imported} 条历史消息", file=sys.stderr)
        # 统计排除的备份文件（供排查）
        try:
            import glob
            backup_files = glob.glob(os.path.expanduser("~/.openclaw/agents/**/*.jsonl*"), recursive=True)
            excluded = [f for f in backup_files
                       if ".reset." in f or ".checkpoint." in f]
            if excluded:
                print(f"ℹ️  自动排除 {len(excluded)} 个备份文件（.reset/.checkpoint）", file=sys.stderr)
        except Exception:
            pass
    except Exception as e:
        print(f"⚠️ 初始化导入出错: {e}", file=sys.stderr)

if __name__ == "__main__":
    create_kv_store()
    if is_database_empty():
        run_full_import()
    else:
        print("ℹ️ 数据库已有数据，跳过初始化", file=sys.stderr)

# 全量导入后执行流式分段合并
if __name__ == '__main__':
    from importer.incremental import merge_streaming_segments_in_db
    merge_streaming_segments_in_db()
