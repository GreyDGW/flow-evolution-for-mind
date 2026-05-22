# Flow Ecosystem 数据库字段语义速查表

> **版本**: v1.0  
> **更新日期**: 2026-05-11  
> **适用范围**: `sessions` 表、`semantic_sessions` 表

---

## ⚠️ 核心概念：`session_id` 的双重语义

### 字段命名历史与实际含义

| 术语 | 用户直觉 | 实际含义 | 当前实现 |
|------|---------|---------|---------|
| **Session** | 一次完整的对话交互（有明确开始/结束） | 一个 JSONL 文件的所有消息（可能跨越数小时） | ❌ 不匹配 |
| **session_id** | 会话的唯一标识符 | 文件名字符串 + 切割后缀 | ⚠️ 需理解上下文 |

---

## 📊 `sessions.session_id` 字段详解

### 格式规范

```
{import_source_id} [#{segment_index}]
```

#### 组成部分

| 部分 | 示例 | 含义 | 来源 |
|------|------|------|------|
| `import_source_id` | `c8584676-9f5d-...` | JSONL 文件名（不含扩展名） | Importer 自动生成 |
| `#{segment_index}` | `#2`, `#5` | BatchSessionCutter 切割后的片段序号 | 可选（未切割时省略） |

#### 实际示例

```sql
-- 未切割状态（原始导入）
SELECT DISTINCT session_id FROM sessions WHERE date(timestamp) = '2026-04-19';
-- 结果: ['c8584676-9f5d-43b5-a0e9-3a0b58aec1a4.checkpoint...']

-- 切割后状态（BatchSessionCutter 处理后）
SELECT DISTINCT session_id FROM sessions WHERE date(timestamp) = '2026-04-19';
-- 结果: [
--   'c8584676-...checkpoint...',    -- 原始组（idx=0, 34条消息）
--   'c8584676-...checkpoint...#2', -- 第2个片段（6条消息）
--   'c8584676-...checkpoint...#3', -- 第3个片段（3条消息）
--   'c8584676-...checkpoint...#4', -- 第4个片段（155条消息）
--   'c8584676-...checkpoint...#5', -- 第5个片段（63条消息）
-- ]
```

---

## 🔍 语义层次对照表

| 层次 | 字段/概念 | 物理含义 | 逻辑含义 | 典型时间跨度 |
|------|----------|---------|---------|------------|
| **L0: 原始数据** | JSONL 文件 | 单个 `.jsonl` 文件 | 一天的所有消息（可能不连续） | 0~24小时 |
| **L1: 导入组** | `session_id` (无 #) | `import_source_id` | 同一文件的消息集合 | 0~24小时 |
| **L2: 对话片段** | `session_id` (带 #) | 近似 `conversation_id` | 时间连续的对话子集 | 1分钟~2小时 |
| **L3: 语义会话** | `semantic_sessions.id` | 独立的会话标识 | 主题连贯的交互单元 | 变化大 |

---

## 📝 SQL 查询指南

### 场景 1：按"文件"聚合统计

```sql
-- 统计每个导入文件的原始消息数（忽略切割）
SELECT 
    SUBSTR(session_id, 1, INSTR(session_id, '#') - 1) as import_source,
    COUNT(*) as total_msgs,
    MIN(timestamp) as first_msg,
    MAX(timestamp) as last_msg
FROM sessions
WHERE date(timestamp) = '2026-04-19'
GROUP BY import_source;
```

### 场景 2：按"对话"聚合分析

```sql
-- 分析每个切割后的对话片段
SELECT 
    session_id as conversation_id,
    COUNT(*) as msg_count,
    COUNT(CASE WHEN role IN ('user', 'assistant') THEN 1 END) as dialog_turns,
    MIN(timestamp) as start_time,
    MAX(timestamp) as end_time,
    ROUND((julianday(MAX(timestamp)) - julianday(MIN(timestamp))) * 24 * 60, 1) as duration_minutes
FROM sessions
WHERE date(timestamp) = '2026-04-19'
GROUP BY session_id
ORDER BY MIN(timestamp);
```

### 场景 3：对比切割前后

```sql
-- 切割前：每个文件一个超长 "session"
SELECT 
    SUBSTR(session_id, 1, 40) as source_id,
    COUNT(*) as msgs_in_file,
    ROUND((julianday(MAX(timestamp)) - julianday(MIN(timestamp))) * 24, 2) as span_hours
FROM sessions
WHERE date(timestamp) = '2026-04-19'
  AND session_id NOT LIKE '%#%'
GROUP BY 1;

-- 切割后：多个合理长度的对话
SELECT 
    session_id,
    COUNT(*) as msgs_in_segment,
    ROUND((julianday(MAX(timestamp)) - julianday(MIN(timestamp))) * 24 * 60, 1) as duration_min
FROM sessions
WHERE date(timestamp) = '2026-04-19'
  AND session_id LIKE '%#%'
ORDER BY MIN(timestamp);
```

---

## 🔧 代码中的使用建议

### ✅ 推荐做法

```python
# 1. 在注释中明确语义
def analyze_session(session_id: str):
    """
    Args:
        session_id: 实际是 import_source_id 或 conversation_group_id
                   格式: {source}[#{segment}]
    """

# 2. 使用有意义的变量名
import_source = session_id.split('#')[0] if '#' in session_id else session_id
is_segmented = '#' in session_id

# 3. 查询时添加说明
sql = """
    SELECT session_id  -- 注: 实际为 conversation_group_id
    FROM sessions ...
"""
```

### ❌ 避免的误解

```python
# ❌ 错误假设：每个 session_id 是独立的对话
for sid in session_ids:
    session = load_session(sid)  # 可能加载了全天 14h 的消息！

# ✅ 正确做法：先检查是否已切割
if '#' in sid:
    # 已切割，是合理的对话片段
else:
    # 未切割，可能是超长聚合体
    # 需要先运行 BatchSessionCutter
```

---

## 📖 与其他系统的术语映射

| 本系统 | OpenAI ChatGPT | Slack | Intercom |
|--------|---------------|-------|----------|
| `session_id` (无#) | Thread ID | Channel ID | Ticket ID |
| `session_id` (带#) | Message Group | Thread TS | Comment Thread |
| `semantic_sessions.id` | Conversation ID | Conversation ID | Conversation ID |

---

## 🎯 未来重构方向（v2.0 计划）

如果未来进行大规模 schema 重构，建议：

```sql
-- 方案：引入清晰的分层结构
ALTER TABLE sessions RENAME COLUMN session_id TO import_source_id;

CREATE TABLE conversations (
    id TEXT PRIMARY KEY,              -- 如 'conv_20260419_001'
    import_source_id TEXT NOT NULL,   -- 关联到 sessions.import_source_id
    segment_index INTEGER,            -- 切片序号（NULL 表示未切割）
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    topic_summary TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 视图兼容旧代码
CREATE VIEW v_sessions_compat AS
SELECT 
    s.*,
    CASE 
        WHEN c.id IS NOT NULL THEN s.import_source_id || '#' || c.segment_index
        ELSE s.import_source_id
    END as session_id  -- 向下兼容
FROM sessions s
LEFT JOIN conversations c ON s.import_source_id = c.import_source_id;
```

---

## 📌 快速参考卡片

```
┌─────────────────────────────────────────────────────┐
│           session_id 语义速查                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  格式: {文件名} [#{N}]                             │
│                                                     │
│  无 #: 原始导入组（import_source）                    │
│       → 可能包含全天消息（0~24小时）                  │
│       → 示例: 'c8584676-checkpoint...'             │
│                                                     │
│  有 #: 切割后的对话片段（conversation）               │
│       → 时间连续，主题连贯                           │
│       → 时长通常 1min ~ 2hours                      │
│       → 示例: 'c8584676-...#4' (155条, 59分钟)     │
│                                                     │
│  查询提示:                                           │
│  • 按"文件": GROUP BY 去掉 # 后缀                     │
│  • 按"对话": GROUP BY 保留完整 session_id            │
│  • 检查切割: WHERE session_id LIKE '%#%'             │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

**维护者注**: 此文档应随着代码重构同步更新。任何对 `sessions` 表结构的修改都应在此记录。