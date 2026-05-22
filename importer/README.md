# Flow Ecosystem 数据导入层

## 用途
将 OpenClaw JSONL 日志解析并写入 `sessions` 基础数据表（39字段）。

## 使用方式
```python
from importer import import_jsonl

import_jsonl("tests/data/example.jsonl", "data/flow_ecosystem.db")
```

## JSONL 格式

每行一个 JSON 对象，type 字段决定事件类型：

| type | 说明 | 是否提取 |
|------|------|----------|
| session | 会话开始 | ✅ 提取元信息 |
| message | 对话消息 | ✅ 提取 role/content/tokens |
| model_change | 模型切换 | ❌ 记录但不提取 |
| thinking_level_change | 思考层级 | ❌ 记录但不提取 |
| custom | 自定义事件 | ❌ 记录但不提取 |

## 字段覆盖

- **35 个基础字段**：由 base_parser.py 原始逻辑覆盖（session_id, role, content_text, model, tokens, cost...）
- **6 个层级字段**：由 migrate_to_hierarchy.py 补充（turn_id, interaction_id, semantic_session_id, hierarchy_level, is_valid_for_analysis, is_system_task）

## 数据流

```
OpenClaw JSONL → base_parser.py → sessions 表 → 聚合 → semantic_sessions
```

## 注意事项

- msg_id 有 UNIQUE 约束，重复导入自动跳过
- toolResult 角色的消息 content_text 置空
- 原始脚本归档在 tools/scripts/archive/
