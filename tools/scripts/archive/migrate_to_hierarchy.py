#!/usr/bin/env python3
"""
Flow Ecosystem V7.3 数据库迁移脚本
实现会话层级：message → turn → interaction → semantic_session

层级定义：
- message: 原始消息（当前 sessions 表）
- turn: 单次问答对（user → assistant）
- interaction: 多个语义相关的 turn
- semantic_session: 围绕一个主题的完整会话（可能跨多天）
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple

DB_PATH = '/Users/duguowei/Desktop/skill相关文档/openclaw_flow_plugin/flow_ecosystem.db'

def create_backup(conn: sqlite3.Connection):
    """创建数据库备份"""
    cursor = conn.cursor()

    tables_to_backup = ['sessions', 'goals', 'closures', 'flow_fragments',
                        'concepts', 'concept_relations', 'session_analyses']

    for table in tables_to_backup:
        try:
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {table}_v7_backup AS SELECT * FROM {table}")
            print(f"  ✅ 已备份表: {table}")
        except sqlite3.OperationalError as e:
            if "already exists" not in str(e):
                print(f"  ⚠️ 备份 {table} 失败: {e}")

    conn.commit()

def add_hierarchy_fields_to_sessions(conn: sqlite3.Connection):
    """为 sessions 表添加层级字段"""
    cursor = conn.cursor()

    new_columns = [
        ('turn_id', 'TEXT'),           # 所属 turn 的 ID
        ('interaction_id', 'TEXT'),    # 所属 interaction 的 ID
        ('semantic_session_id', 'TEXT'),  # 所属 semantic_session 的 ID
        ('hierarchy_level', 'TEXT'),   # 层级: 'message'
        ('is_valid_for_analysis', 'INTEGER DEFAULT 1'),  # 是否有效用于分析
        ('is_system_task', 'INTEGER DEFAULT 0'),  # 是否为系统任务
    ]

    for col_name, col_type in new_columns:
        try:
            cursor.execute(f"ALTER TABLE sessions ADD COLUMN {col_name} {col_type}")
            print(f"  ✅ 已添加字段: {col_name} ({col_type})")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"  ⏭️ 字段已存在: {col_name}")
            else:
                print(f"  ⚠️ 添加字段失败 {col_name}: {e}")

    conn.commit()

def create_interactions_table(conn: sqlite3.Connection):
    """创建 interactions 表"""
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interactions (
            id TEXT PRIMARY KEY,
            start_time DATETIME NOT NULL,
            end_time DATETIME,
            duration_minutes REAL,
            turn_count INTEGER DEFAULT 0,
            topic_summary TEXT,
            semantic_coherence REAL,
            llm_analysis_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  ✅ 已创建表: interactions")

    cursor.execute("CREATE INDEX IF NOT EXISTS ix_interactions_start_time ON interactions(start_time)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_interactions_semantic_session ON interactions(id)")

    conn.commit()

def create_semantic_sessions_table(conn: sqlite3.Connection):
    """创建 semantic_sessions 表"""
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS semantic_sessions (
            id TEXT PRIMARY KEY,
            title TEXT,
            topic_summary TEXT,
            overall_goal TEXT,
            start_time DATETIME NOT NULL,
            end_time DATETIME,
            duration_minutes REAL,
            interaction_count INTEGER DEFAULT 0,
            total_message_count INTEGER DEFAULT 0,
            goal_alignment_score REAL,
            drift_score REAL,
            llm_analysis_json TEXT,
            status TEXT DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  ✅ 已创建表: semantic_sessions")

    cursor.execute("CREATE INDEX IF NOT EXISTS ix_semantic_sessions_start_time ON semantic_sessions(start_time)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_semantic_sessions_status ON semantic_sessions(status)")

    conn.commit()

def create_turns_table(conn: sqlite3.Connection):
    """创建 turns 表"""
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS turns (
            id TEXT PRIMARY KEY,
            interaction_id TEXT,
            start_time DATETIME NOT NULL,
            end_time DATETIME,
            user_message TEXT,
            assistant_response TEXT,
            message_count INTEGER DEFAULT 2,
            has_goal INTEGER DEFAULT 0,
            goal_text TEXT,
            pdca_stages TEXT,
            flow_depth REAL,
            cognitive_evolution_score REAL,
            llm_analysis_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (interaction_id) REFERENCES interactions(id)
        )
    """)
    print("  ✅ 已创建表: turns")

    cursor.execute("CREATE INDEX IF NOT EXISTS ix_turns_interaction ON turns(interaction_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_turns_start_time ON turns(start_time)")

    conn.commit()

def create_turn_relationships_table(conn: sqlite3.Connection):
    """创建 turn_relationships 表用于追踪 turn 之间的关系"""
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS turn_relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_turn_id TEXT,
            to_turn_id TEXT,
            relationship_type TEXT,
            semantic_similarity REAL,
            goal_continuity INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (from_turn_id) REFERENCES turns(id),
            FOREIGN KEY (to_turn_id) REFERENCES turns(id)
        )
    """)
    print("  ✅ 已创建表: turn_relationships")

    cursor.execute("CREATE INDEX IF NOT EXISTS ix_turn_rel_from ON turn_relationships(from_turn_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_turn_rel_to ON turn_relationships(to_turn_id)")

    conn.commit()

def mark_invalid_messages(conn: sqlite3.Connection):
    """标记无效消息（系统任务如 cron 等）"""
    import re
    cursor = conn.cursor()

    invalid_patterns = [
        r'^\{.*\}$', r'^```', r'^\[.*\]$', r'^#{1,6}\s', r'^\|\s',
        r'^•\s', r'^-{3,}$', r'^={3,}$', r'^[0-9\s\[\]]+$', r'^[0-9]+$',
        r'^GMT.*\d+$', r'^A new session was started', r'^bootstrap is still pending',
        r'^\[cron:', r'^You are FlowGuard', r'^检查 memory/flowguard',
        r'^只报告问题', r'^\d+\s+GMT.*\]$', r'^\d+\s+GMT.*\]\s*\d+$',
        r'^[0-9\]\s]+$', r'^FlowGuard', r'^Heartbeat', r'^cron',
    ]

    cursor.execute("SELECT id, content_text FROM sessions WHERE is_valid_for_analysis = 1 AND content_text IS NOT NULL")
    all_messages = cursor.fetchall()

    update_count = 0
    for msg_id, content in all_messages:
        is_invalid = False
        for pattern in invalid_patterns:
            if re.match(pattern, content.strip()):
                is_invalid = True
                break
        if is_invalid:
            cursor.execute("UPDATE sessions SET is_system_task = 1, is_valid_for_analysis = 0 WHERE id = ?", (msg_id,))
            update_count += 1

    conn.commit()
    print(f"  ✅ 已标记 {update_count} 条无效消息")

def identify_turns(conn: sqlite3.Connection):
    """识别 turns（单次问答对）"""
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, role, content_text, timestamp
        FROM sessions
        WHERE role = 'user'
        AND is_valid_for_analysis = 1
        ORDER BY timestamp
    """)

    user_messages = cursor.fetchall()

    turn_id = str(uuid.uuid4())
    turn_interaction_id = None
    turn_count = 0

    interaction_id = str(uuid.uuid4())
    interaction_start = None

    for msg_id, role, content, timestamp in user_messages:
        if turn_count == 0:
            interaction_start = timestamp

        turn_id = str(uuid.uuid4())

        cursor.execute("""
            UPDATE sessions
            SET turn_id = ?,
                hierarchy_level = 'message'
            WHERE id = ?
        """, (turn_id, msg_id))

        turn_count += 1

        if turn_count >= 5:
            turn_count = 0

    conn.commit()
    print(f"  ✅ 已识别 {len(user_messages)} 个 turns")

def migrate_database():
    """执行数据库迁移"""
    print("\n" + "="*70)
    print("Flow Ecosystem V7.3 数据库迁移")
    print("="*70)

    conn = sqlite3.connect(DB_PATH)

    try:
        print("\n📦 步骤 1: 创建备份...")
        create_backup(conn)

        print("\n📊 步骤 2: 添加层级字段到 sessions 表...")
        add_hierarchy_fields_to_sessions(conn)

        print("\n🎯 步骤 3: 创建 interactions 表...")
        create_interactions_table(conn)

        print("\n🎯 步骤 4: 创建 semantic_sessions 表...")
        create_semantic_sessions_table(conn)

        print("\n🔄 步骤 5: 创建 turns 表...")
        create_turns_table(conn)

        print("\n🔗 步骤 6: 创建 turn_relationships 表...")
        create_turn_relationships_table(conn)

        print("\n🏷️ 步骤 7: 标记无效消息...")
        mark_invalid_messages(conn)

        print("\n🔍 步骤 8: 识别 turns...")
        identify_turns(conn)

        print("\n✅ 迁移完成！")

        print("\n" + "="*70)
        print("新数据结构说明:")
        print("="*70)
        print("""
会话层级（从低到高）：
├── message（原始消息）  → sessions 表（新增字段）
│   ├── turn_id: 所属 turn
│   ├── interaction_id: 所属 interaction
│   ├── semantic_session_id: 所属 semantic_session
│   ├── hierarchy_level: 'message'
│   ├── is_valid_for_analysis: 是否有效
│   └── is_system_task: 是否为系统任务
│
├── turn（单次问答对）  → turns 表（新建）
│   ├── interaction_id: 所属 interaction
│   ├── user_message / assistant_response
│   ├── goal_text: 提取的目标
│   └── pdca_stages: 闭环阶段
│
├── interaction（多个相关 turn）  → interactions 表（新建）
│   ├── topic_summary: 主题摘要
│   ├── semantic_coherence: 语义连贯性
│   └── turn_count: 包含的 turn 数
│
└── semantic_session（主题会话）  → semantic_sessions 表（新建）
    ├── title: 会话标题
    ├── overall_goal: 整体目标
    ├── goal_alignment_score: 目标对齐度
    └── status: active/completed
        """)

    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def verify_migration():
    """验证迁移结果"""
    print("\n" + "="*70)
    print("验证迁移结果")
    print("="*70)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    tables = ['sessions', 'interactions', 'semantic_sessions', 'turns', 'turn_relationships']

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  📊 {table}: {count} 条记录")

    print("\n📋 sessions 表新增字段:")
    cursor.execute("PRAGMA table_info(sessions)")
    columns = cursor.fetchall()
    new_fields = ['turn_id', 'interaction_id', 'semantic_session_id', 'hierarchy_level',
                  'is_valid_for_analysis', 'is_system_task']
    for col in columns:
        if col[1] in new_fields:
            print(f"  ✅ {col[1]}: {col[2]}")

    print("\n📊 无效消息统计:")
    cursor.execute("SELECT COUNT(*) FROM sessions WHERE is_system_task = 1")
    invalid_count = cursor.fetchone()[0]
    print(f"  ⚠️ 系统任务: {invalid_count} 条")

    cursor.execute("SELECT COUNT(*) FROM sessions WHERE is_valid_for_analysis = 0")
    invalid_analysis = cursor.fetchone()[0]
    print(f"  ⚠️ 无效分析: {invalid_analysis} 条")

    conn.close()

if __name__ == '__main__':
    migrate_database()
    verify_migration()