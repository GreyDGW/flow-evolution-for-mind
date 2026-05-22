# Flow Ecosystem 技术规格说明书

> 版本：V7.7 | 更新：2026-05-08

---

## 一、核心模块规格

### 1.1 SessionAnalyzer（4维判定系统）

#### 输入输出

| 字段 | 类型 | 说明 |
|------|------|------|
| 输入：messages | List[Dict] | 对话历史 |
| 输入：memory_path | str | MEMORY.md 路径 |
| 输出：SessionAnalysis | dataclass | 4维判定结果 |

#### 4维定义

| 维度 | 定义 | 判定标准 |
|------|------|----------|
| 目标对齐 | 对话是否围绕用户活跃目标 | 高=紧密围绕，中=部分相关，低=偏离或无关 |
| 闭环指数 | 对话是否产生可交付产出 | 高=有明确产出，中=有方案但未交付，低=纯讨论 |
| 心流深度 | 用户注意力投入程度 | 高=深度沉浸，中=有波动，低=频繁分心 |
| 认知成长 | 对话中是否产生新概念 | 高=突破舒适区，中=稳步积累，低=重复已知 |

#### 证据规范

| 层级 | 长度 | 用途 |
|------|------|------|
| SessionAnalyzer 输出 | 30字内 | 信号密度，内部判定 |
| /flow_report 展示 | 50字内 | 叙事密度，用户阅读 |

---

### 1.2 StateDistiller（12条规则体系）

#### 规则优先级

| 优先级 | 规则 | pace | depth | tone |
|:------:|------|------|------|------|
| 1 | 卡壳 burnout | hold | surface | soft |
| 2 | 能量耗尽 | hold | surface | soft |
| 3 | 产出饱和 | hold | surface | soft |
| 4 | 迷失探索 | explore | surface | soft |
| 5 | 目标漂移 | anchor | surface | soft |
| 6 | 执行卡壳 | converge | deep | neutral |
| 7 | 心流不稳 | explore | surface | neutral |
| 8 | 舒适区运转 | converge | deep | neutral |
| 9 | 四维协同 | converge | deep | neutral |
| 10 | 高产出模式 | converge | deep | neutral |
| 11 | 认知突破 | explore | deep | neutral |
| 12 | 平稳推进 | explore | deep | neutral |

#### pace 映射

| pace | 映射 |
|------|------|
| converge | 收敛推进 |
| explore | 顺势探索 |
| hold | 静默陪伴 |
| anchor | 锚定回目标 |

---

### 1.3 ReportGenerator（报告组装）

#### LLM 调用次数

| 调用 | 目的 | Token 估算 |
|------|------|----------|
| 第1次 | portrait 润色 | ~500 |
| 第2次 | 破局指南 | ~800 |
| **合计** | - | **~1300/次** |

#### 输出格式

```markdown
📅 Flow 系统认知镜像 (YYYY-MM-DD)

时间范围：[当天/当周/当月/当年/自定义]

**四维评估**：
🎯 目标对齐：[高/中/低]（50字内证据）
🔄 闭环指数：[高/中/低]（50字内证据）
💫 心流深度：[高/中/低]（50字内证据）
🧠 认知成长：[高/中/低]（50字内证据）

💡 **破局指南**

| 优先级 | 问题类型 | 推荐工具 | 推荐理由 | 节省时间 | 学习成本 |
|--------|----------|----------|----------|----------|----------|
| 🔴 1 | ... | ... | ... | ... | ... |

最大回报工具：...
即插即用工具：...
```

---

## 二、API 规格

### 2.1 SiliconFlowLLMClient

```python
class SiliconFlowLLMClient:
    def generate(self, prompt: str) -> str: ...
    # Base URL: https://api.siliconflow.cn/v1/chat/completions
    # Model: Qwen/Qwen2.5-7B-Instruct
```

### 2.2 BraveSearch

```python
class BraveSearch:
    def search(self, query: str, count: int = 3) -> List[Dict]: ...
    # Base URL: https://api.search.brave.com/res/v1/web/search
    # Header: X-Subscription-Token: {BRAVE_API_KEY}
```

---

## 三、数据模型

### 3.1 SQLite Schema

```sql
CREATE TABLE semantic_sessions (
    session_id TEXT PRIMARY KEY,
    created_at TIMESTAMP,
    message_count INTEGER,
    topic_tag TEXT,
    vector_ids TEXT
);

CREATE TABLE session_analyses (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    goal_alignment TEXT,
    closure_index TEXT,
    flow_depth TEXT,
    cognition_growth TEXT,
    goal_evidence TEXT,
    closure_evidence TEXT,
    flow_evidence TEXT,
    cognition_evidence TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES semantic_sessions(session_id)
);

CREATE TABLE daily_summaries (
    date TEXT PRIMARY KEY,
    session_count INTEGER,
    avg_goal_alignment REAL,
    avg_closure_index REAL,
    avg_flow_depth REAL,
    avg_cognition_growth REAL
);
```

---

## 四、关键约束

1. **不输出固定标签** —— 放弃 12型/81型分类
2. **不输出数值分数** —— 只保留 高/中/低 三档
3. **不主动展示** —— 仅用户召唤 /flow_report 时输出
4. **工具自由推荐** —— LLM 根据损失动态推荐真实工具
5. **pace 变化时写入** —— 仅 pace 变化时更新 MEMORY.md
