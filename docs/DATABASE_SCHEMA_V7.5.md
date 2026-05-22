# Flow Ecosystem 数据库 Schema（V7.5）

> 基于 Flow Ecosystem Skill PRD V7.5
> 更新时间：2026-04-30

---

## 概述

**核心资产层（SQLite）**：9 张核心表，完整原文永久存档，schema 稳定，向后兼容

**语义雷达层（ChromaDB）**：4 个向量集合

---

## 一、SQLite 核心表（9张）

### 1. messages（对话原文）

原 `sessions` 表更名，存储单条消息记录。**永久保存**。

| 字段名 | 类型 | 用途 | 说明 |
|--------|------|------|------|
| id | INTEGER PRIMARY KEY | 自增主键 | - |
| message_id | TEXT | 消息唯一标识 | UUID格式 |
| session_id | TEXT | 所属Session ID | 外键 → semantic_sessions.session_id |
| timestamp | DATETIME | 消息时间戳 | - |
| role | TEXT | 角色 | 'user' / 'assistant' |
| content | TEXT | 消息内容 | 原文存储 |
| msg_length | INTEGER | 消息长度 | 字符数 |
| has_code | BOOLEAN | 是否包含代码 | - |
| is_question | BOOLEAN | 是否为提问 | - |
| concept_density | REAL | 概念密度 | 0.0-1.0 |
| topic_vector_id | TEXT | 主题向量ID | 关联ChromaDB |

**外键关系**：`messages.session_id` → `semantic_sessions.session_id`

---

### 2. semantic_sessions（语义会话）

三层切割产物，代表一个完整的语义会话。**永久保存**。

| 字段名 | 类型 | 用途 | 说明 |
|--------|------|------|------|
| id | INTEGER PRIMARY KEY | 自增主键 | - |
| session_id | TEXT UNIQUE | Session唯一标识 | UUID格式 |
| start_time | DATETIME | 会话开始时间 | - |
| end_time | DATETIME | 会话结束时间 | - |
| turn_count | INTEGER | Turn数量 | - |
| topic_tag | TEXT | 会话主题标签 | 如：'database_design' |
| status | TEXT | 会话状态 | 'active' / 'closed' / 'merged' / 'archived' |
| cut_reason | TEXT | 切割原因 | 触发哪条硬规则/向量层 |
| cut_layer | TEXT | 切割层级 | 'hard_rules' / 'vector_layer' / 'llm_arbiter' |
| avg_similarity | REAL | 平均语义相似度 | 向量层计算结果 |
| slump_triggered | BOOLEAN | 是否触发摆烂模式 | - |
| fatigue_triggered | BOOLEAN | 是否触发疲劳预警 | - |

---

### 3. interactions（子话题聚类）

同一 Session 内的子话题聚类，离线生成。**永久保存**。

| 字段名 | 类型 | 用途 | 说明 |
|--------|------|------|------|
| id | INTEGER PRIMARY KEY | 自增主键 | - |
| session_id | TEXT | 所属Session ID | 外键 → semantic_sessions.session_id |
| start_turn | INTEGER | 起始Turn编号 | - |
| end_turn | INTEGER | 结束Turn编号 | - |
| topic_tag | TEXT | 子话题标签 | - |
| summary | TEXT | 话题摘要 | LLM生成 |
| entities | TEXT | 关键实体 | JSON数组格式 |
| emotional_tone | TEXT | 情感基调 | 'neutral' / 'positive' / 'negative' |
| key_decisions | TEXT | 关键决策 | JSON数组格式 |
| open_questions | TEXT | 未解决问题 | JSON数组格式 |
| closure_candidate | BOOLEAN | 是否可标记为闭环 | - |
| generated_at | DATETIME | 生成时间 | - |

---

### 4. session_cuts（会话切割日志）

可审计的切割记录。**永久保存**。

| 字段名 | 类型 | 用途 | 说明 |
|--------|------|------|------|
| id | INTEGER PRIMARY KEY | 自增主键 | - |
| session_id | TEXT | 所属Session ID | 外键 → semantic_sessions.session_id |
| turn_index | INTEGER | Turn索引 | - |
| layer | TEXT | 触发层级 | 'hard_rules' / 'vector_layer' / 'llm_arbiter' |
| rule | TEXT | 触发的具体规则 | 如：'timeout_30min' |
| similarity | REAL | 向量相似度 | 仅向量层使用 |
| latency_ms | INTEGER | 判定延迟 | 毫秒 |
| created_at | DATETIME | 创建时间 | - |

---

### 5. goals（目标档案）

永久存储的用户目标

| 字段名 | 类型 | 用途 | 说明 |
|--------|------|------|------|
| id | INTEGER PRIMARY KEY | 自增主键 | - |
| declared_text | TEXT | 目标文本 | 用户声明的原始目标 |
| declared_at | DATETIME | 声明时间 | - |
| status | TEXT | 目标状态 | 'active' / 'achieved' / 'abandoned' / 'drifted' |
| drift_score | REAL | 漂移分数 | 0.0-1.0 |
| last_mentioned | DATETIME | 最后提及时间 | - |
| closed_at | DATETIME | 关闭时间 | 目标完成/放弃时间 |
| closure_evidence | TEXT | 闭环证据 | - |
| complexity_score | REAL | 复杂度评分 | 1-10 |

---

### 6. closures（闭环记录）

永久存储的闭环记录

| 字段名 | 类型 | 用途 | 说明 |
|--------|------|------|------|
| id | INTEGER PRIMARY KEY | 自增主键 | - |
| goal_id | INTEGER | 关联目标ID | 外键 → goals.id |
| session_id | TEXT | 关联Session ID | 外键 → semantic_sessions.session_id |
| task_name | TEXT | 任务名称 | - |
| plan_evidence | TEXT | Plan阶段证据 | - |
| do_evidence | TEXT | Do阶段证据 | - |
| check_evidence | TEXT | Check阶段证据 | - |
| adjust_evidence | TEXT | Adjust阶段证据 | - |
| topology | TEXT | PDCA拓扑结构 | 'linear' / 'spiral' / 'double_loop' |
| complexity_score | REAL | 复杂度评分 | 1-10 |
| value_score | REAL | 价值评分 | 1-10 |
| time_invested_ratio | REAL | 时间投入比 | 实际/预期 |
| started_at | DATETIME | 开始时间 | - |
| closed_at | DATETIME | 关闭时间 | - |

**外键关系**：
- `closures.goal_id` → `goals.id`
- `closures.session_id` → `semantic_sessions.session_id`

---

### 7. flow_fragments（心流片段）

心流分析片段。**永久保存**。

| 字段名 | 类型 | 用途 | 说明 |
|--------|------|------|------|
| id | INTEGER PRIMARY KEY | 自增主键 | - |
| session_id | TEXT | 所属Session ID | 外键 → semantic_sessions.session_id |
| start_time | DATETIME | 片段开始时间 | - |
| end_time | DATETIME | 片段结束时间 | - |
| duration_min | INTEGER | 持续时长（分钟） | - |
| rounds_count | INTEGER | 交互轮数 | - |
| interruptions | INTEGER | 中断次数 | - |
| recovery_rounds | INTEGER | 恢复轮数 | 中断后恢复的次数 |
| intensity | REAL | 心流强度 | 0.0-1.0 |
| semantic_coherence | REAL | 语义连贯性 | 0.0-1.0 |
| merged_sessions | TEXT | 合并的Session列表 | JSON数组，如：[Session_A.id, Session_B.id] |

---

### 8. concepts（概念节点）

永久存储的概念知识图谱节点

| 字段名 | 类型 | 用途 | 说明 |
|--------|------|------|------|
| id | INTEGER PRIMARY KEY | 自增主键 | - |
| name | TEXT UNIQUE | 概念名称 | - |
| first_seen | DATETIME | 首次出现时间 | - |
| last_seen | DATETIME | 最后出现时间 | - |
| mention_count | INTEGER | 提及次数 | - |
| mastery_stage | TEXT | 掌握阶段 | 'new' / 'learning' / 'familiar' / 'mastered' |
| source_session | TEXT | 来源Session | 首次出现的Session ID |

---

### 9. concept_relations（概念关联）

永久存储的概念关系

| 字段名 | 类型 | 用途 | 说明 |
|--------|------|------|------|
| from_concept | INTEGER | 起始概念ID | 外键 → concepts.id |
| to_concept | INTEGER | 目标概念ID | 外键 → concepts.id |
| relation_type | TEXT | 关系类型 | 'uses' / 'depends_on' / 'similar_to' / 'refines' |
| first_seen | DATETIME | 首次关联时间 | - |
| weight | REAL | 关系权重 | 0.0-1.0 |

**复合主键**：`PRIMARY KEY (from_concept, to_concept, relation_type)`

---

## 二、ChromaDB 向量集合（4个）

| 集合名 | 用途 | 关联表 |
|--------|------|--------|
| goal_vectors | 目标语义向量，用于漂移计算 | goals.topic_vector_id |
| message_vectors | 对话消息向量，用于语义检索 | messages.topic_vector_id |
| concept_vectors | 概念语义向量，用于认知图谱 | concepts.id |
| session_vectors | Session主题向量，用于跨Session相似度计算 | semantic_sessions.session_id |

---

## 三、表关系图

```
semantic_sessions (1) ──────< messages (N)
    │
    ├──────< interactions (N)
    │
    ├──────< session_cuts (N)
    │
    ├──────< closures (N) ──────> goals (1)
    │
    └──────< flow_fragments (N)

goals (1) ──────< closures (N)

concepts (1) ──────< concept_relations (N)
                           │
                           └──────> concepts (1)
```

---

## 四、兼容性设计

- **旧版工具兼容**：`CREATE VIEW sessions AS SELECT * FROM messages`
- **预留扩展字段**：semantic_sessions.status 支持 future 扩展
- **标准SQL**：所有表使用标准SQL，无自定义类型，兼容任意SQLite工具
- **向量分离**：向量数据与结构化数据分离，未来可迁移至其他向量数据库

---

## 五、数据保留周期

> **重要更新（2026-04-30）**：所有9张表均改为**永久保存**，不设滚动删除

| 表名 | 保留周期 |
|------|---------|
| messages | **永久** |
| semantic_sessions | **永久** |
| interactions | **永久** |
| session_cuts | **永久** |
| goals | 永久 |
| closures | 永久 |
| flow_fragments | **永久** |
| concepts | 永久 |
| concept_relations | 永久 |

---

**版本历史**：
- V7.5: 从6张表扩展为9张表，新增 semantic_sessions、interactions、session_cuts
- V7.3: 初始6张表设计

---

## 六、核心模块实现（2026-07-13）

### 6.1 LLM Client 模块

**文件**: `core/llm_client.py`

| 类 | 说明 | 状态 |
|----|------|------|
| `OpenClawLLMClient` | 单阶段JSON输出，使用response_format | ✅ 已固化 |
| `MockLLMClient` | 测试用模拟客户端 | ✅ 已固化 |

**配置**:
```python
# 从 .env 读取
LLM_API_KEY=sk-xxx
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_MODEL=deepseek-ai/DeepSeek-V3
LLM_TIMEOUT=60
```

**Prompt模板**（极简版）:
```python
PROMPT_TEMPLATE = """基于对话和活跃目标，输出严格JSON。
评估（每项0-3分，带evidence原文引用）：
1. goal: drift_score(0-1), is_drifting(bool), goal_progress(0-100), evidence
2. pdca: plan/do/check/adjust各{detected(bool), completeness(full/partial/missing), evidence}, double_loop(bool)
3. flow.base_quality: logic_depth/orderliness/progression/judgment_vector/goal_alignment各{score, evidence}
4. flow.signal_gain: rebellion/persistent_questioning/self_correction/time_depth/meta_cognition各{score, evidence}
5. cognition: concept_density/causal_depth/self_correction_freq/cross_domain_links各{score, evidence}
6. meta: complexity_score(1-10), value_score(1-10), time_ratio(0.5-2.0)
只输出JSON，不要任何解释。"""
```

---

### 6.2 Preprocessor 模块

**文件**: `plugin/session/preprocessor.py`

| 类 | 说明 | 状态 |
|----|------|------|
| `TurnPreprocessor` | 代码块/引用/列表提取，content标准化 | ✅ 已固化 |

**功能**:
- `preprocess(content)` - 处理list/dict/str多种格式
- `_extract_code_blocks()` - Markdown代码块提取
- `_extract_quote_blocks()` - 引用块提取（>200字阈值）
- `_extract_long_lists()` - 长列表提取（5行+阈值）
- 概念指纹：MD5前8位哈希

---

### 6.3 SemanticSessionCutter 模块

**文件**: `plugin/session/session_cutter.py`

| 类 | 说明 | 状态 |
|----|------|------|
| `SemanticSessionCutter` | sentence-transformers向量化切分 | ✅ 已固化 |

**切分规则**:
- 阈值0.15：相邻消息相似度 < 0.15 → 新Session
- 豁免合并：≤2轮闲聊 → 合并到相邻大Session
- 独立切分：≥3轮闲聊 → 独立成Session

**向量化**:
```python
# 使用 paraphrase-multilingual-MiniLM-L12-v2
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
embeddings = model.encode(contents)
# 余弦相似度计算
```

---

### 6.4 ClosureAnalyzer 模块

**文件**: `plugin/session/closure_analyzer.py`

| 类 | 说明 | 状态 |
|----|------|------|
| `ClosureAnalyzer` | EWCI/心流/PDCA计算 | ✅ 已固化 |

**输出指标**:
- `ewci`: 效率 × 质量 × 复杂度
- `flow_depth`: 心流深度（base_quality × signal_gain）
- `goal_alignment`: drift_score, goal_progress
- `pdca`: plan/do/check/adjust 各阶段 detected + completeness

---

### 6.5 GoalLoader 模块

**文件**: `core/goal_loader.py`

| 类 | 说明 | 状态 |
|----|------|------|
| `GoalLoader` | 从memory.md读取活跃目标 | ✅ 已固化 |

**数据路径**: `~/.openclaw/memory.md`

**活跃状态过滤**:
```python
active_statuses = {"推进中", "稳步推进", "进行中", "活跃", "active", "in_progress"}
```

---

### 6.6 ConceptTracker 模块

**文件**: `core/concept_tracker.py`

| 类 | 说明 | 状态 |
|----|------|------|
| `ConceptTracker` | Hub概念追踪，跨日稳定性计算 | ✅ 已固化 |

**数据路径**: `~/.openclaw/concepts.json`

**核心方法**:
- `extract_concepts()` - 从LLM evidence提取概念指纹（前15字）
- `store_daily_concepts()` - 存储日概念集合
- `calculate_hub_stability()` - Jaccard相似度（今日∩昨日)/(今日∪昨日)

---

### 6.7 DailyAggregator 模块

**文件**: `core/daily_aggregator.py`

| 类 | 说明 | 状态 |
|----|------|------|
| `DailyAggregator` | 日级聚合，PRD 7.4跨日稳定性 | ✅ 已固化 |

**PRD 7.4 跨日稳定性公式**:
```python
cross_day_stability = 1 + (hub_stability - yesterday_hub) * 0.5
# 范围限制: 0.5 ~ 1.5
```

---

### 6.8 向量嵌入层

**文件**: `plugin/session/embedding.py`

| 嵌入器 | 模型 | 维度 | 状态 |
|--------|------|------|------|
| `SentenceTransformerEmbedder` | paraphrase-multilingual-MiniLM-L12-v2 | 384 | ✅ 主要 |
| `ChromaEmbedder` | all-MiniLM-L6-v2 (ONNX) | 384 | ⏳ 有中文Bug |
| `KeywordEmbedder` | 无外部依赖 | 10 | ⏳ Fallback |

---

## 七、API配置

**文件**: `.env`

```bash
LLM_API_KEY=sk-xxx                    # 硅基流动API Key
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_MODEL=deepseek-ai/DeepSeek-V3
LLM_TIMEOUT=60
```

**LLM Providers**:
- 硅基流动（默认）
- DeepSeek官方

---

## 八、验收状态（2026-07-13）

| Task | 说明 | 状态 |
|------|------|------|
| Task 16 | 三层渐进式会话切割 | ✅ |
| Task 16.1 | 引用块预处理器 | ✅ |
| Task 16.2 | LLM Client | ✅ |
| Task 16.3 | SemanticSessionCutter | ✅ |
| Task 16.4 | GoalLoader | ✅ |
| Task 16.5 | 完整流水线测试 | ✅ (9/10) |

**测试结果**:
- 5组JSON结构: 100%通过
- 10组端到端: 90%通过
- 6组综合测试: 完成
- Hub跨日稳定性: ✅ 已验证