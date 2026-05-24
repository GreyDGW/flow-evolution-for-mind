# Flow&Evolution for Mind — 个人认知进化系统


> **前言**：agent 太强大了，强大到很多时候我们都已经习惯性地去放弃自我、遵从 AI。而你一旦决定遵从它、放弃自我，你会发现这是它把你导向混乱的开端——因为你已经丧失了对 AI 时代而言最重要的品味和判断力。


## 产品哲学

**成就 = 正确方向上的高效闭环 ⬅️➡️ 内部心流 + 认知进化。**

我们需要构建出一个属于我们的"熵减循环"。进化不是单纯的累加，而是你处理世界时，系统混乱度（熵）的下降。

### 一、产品核心定位与进化哲学

**Slogan：首个反降智 / 认知共生引擎**

这是一个通过**认知共生协议（Cognitive Symbiosis Protocol）**与用户共同进化的个人动力系统。它充分了解你、理解你，在后台疯狂分析你和 AI 的每一次对话，计算你的认知状态：

> 默默地为你构建起一个"防降智、促进化"的力场。

像一位真正懂你的伙伴。系统用 14 种 Portrait 画像把你的认知状态翻译成 AI 的行为边界：该直接给方案时绝不绕弯子，该以问代答时绝不直接塞答案，该沉默陪伴时绝不强行推进。你几乎感觉不到它的存在，但你会发现 AI 越来越「对味」，而不是什么问题都搞苏格拉底式拷问或者事事顺从你。

> 当你主动召唤时，它会给你一份「认知体检报告」：

- 🎯 你最近的方向有没有跑偏？
- 🔄 做事是不是总在开坑不填？
- 🌊 心流状态好不好？
- 🧠 认知有没有真正成长？

基于完整的语义化原文证据，并为你推荐最适合你的工具或者方法。

**宿主平台**：OpenClaw


### 双层设计理念

| 层次 | 内容 | 作用 |
|------|------|------|
| **外部层**（目标对齐度 + 闭环指数） | 工作做对的事，并且做完；考虑高不高、多长时间做完 | 外部观察和评价标准，判断工作做得好不好、效率高不高 |
| **内部层**（心流深度 + 认知成长） | 心流状态保持 + 认知框架稳步提升 | 内部心理进步和良好体验，反哺外部工作流效率 |

---


## 4 维评估体系（系统核心算法）

每个 Session 结束后，LLM 会给四个维度打分：

| 维度 | 评估什么 |
|------|----------|
| 🎯 **目标对齐度** | 做的事是否在为主目标添砖加瓦？ |
| 🔄 **闭环指数** | 提出的坑填上了吗？PDCA 循环如何？ |
| 🌊 **心流深度** | 思考密度、逻辑连贯性 |
| 🧠 **认知成长** | 有没有 "Aha!" 时刻、新连接 |

「目标对齐度」：读取你 Agent 的 `MEMORY.md` 文件里的长期目标作为「外部目标参照系」，防止 LLM 瞎判断。其他三维纯粹基于对话原文评估，互不污染。




## 核心架构：三层时间尺度

| 层级 | 触发时机 | 核心动作 | 延迟 |
|------|----------|----------|------|
| **Turn 级（实时）** | 你和 AI 每聊一句 | AI 知道你内部层和外部层的状态对应到你的portrait画像，自动「4D 调音参数」，调节语气/深度/阻力 | 0ms |
| **Session 级（分析）** | 一段对话结束 | LLM 做 4 维判定 + 80-300 字证据 → 提炼 Portrait 画像 → 写入数据库 | <3s |
| **日/周级（展示）** | 用户召唤 `/deepflow` | 读取数据库，加权平均，双 LLM 润色，输出 Markdown 报告 | 异步 |

**关键设计**：实时路径不碰分析路径，分析路径不碰展示路径。各跑各的，互不阻塞。

---

---

## 调音系统：让 AI 真正「懂你」

每轮对话都在微调 AI 的行为模式。

### 4D 调音参数

| 参数 | 取值 | 比喻 |
|------|------|------|
| **pace** | converge / explore / hold / anchor | 方向盘——给不给方案 |
| **depth** | deep / surface | 油门深浅——分析多深 |
| **tone** | neutral / soft | 空调温度——说话语气 |
| **friction** | direct / socratic / dynamic | 离合器——给答案还是给问题 |

### 14 种 Portrait 画像

系统用 14 条规则把 4 维分数映射成「状态画像」，例如：
- **执行卡壳** —— 方向极准，但落地薄弱
- **迷失探索** —— 好奇心大于目标感，浅尝辄止
- **四维协同** —— 峰值状态，记录触发条件
- ...共 14 种

每种画像对应「行为方向强控」（DO / NOT TO-DO），直接告诉 AI 该做什么、禁止做什么。

### 注入文本五段式

每轮对话前，系统会把一段约 240-260 字的「认知协议」注入给 LLM：

```markdown
【Flow认知协议 - 角色启动】
你现在是用户的「执行卡壳」状态...

【Flow认知协议】
当前状态：执行卡壳 · converge · surface · neutral · direct
核心意图：你察觉到用户在用讨论的安全感对抗交付的焦虑...
行为基调：沉默交付。让产出本身成为唯一的语言。
行为方向强控：DO：越过安慰，直接交付... NOT TO-DO：禁止委婉商量...
```


---
### 认知体检报告

当你主动召唤 `/deepflow` 时，系统会读取 `session_analyses` 表中的全部分析记录，按时间段加权聚合，经双 LLM 润色后，输出一份完整的 Markdown 认知体检报告。

**报告结构（深度版）**：

```markdown
📅 Flow 认知镜像 · {时间段}

一、总体统计概览
   └─ 分析日期 | 总记录数 | Agent 数量

二、四维评估分布
   └─ 🎯 目标对齐 | 🔄 闭环指数 | 🌊 心流深度 | 🧠 认知成长
   └─ 高/中/低分布 + 均分 + 综合评分

三、画像标签分布
   └─ 表格：标签 | 数量 | 占比 | 进度条可视化

四、各 Agent 表现详情
   └─ 表格：Agent ID | Session 数 | 平均目标分 | 目标分布

五、关键 Session 亮点
   └─ 🌟 最佳表现（最高分 session）
   └─ 📊 典型案例（接近均分 session）
   └─ 💡 有待提升（最低分 session）

六、关键洞察与分析
   └─ ✅ 优势领域（自动识别 ≥2.5 分的维度）
   └─ ⚠️ 改进空间（自动识别 <2.0 分的维度）

七、各维度详细解读
   └─ 🎯 目标对齐度分析
   └─ 🔄 闭环指数分析
   └─ 🌊 心流深度分析
   └─ 🧠 认知成长分析

八、数据质量 & 趋势对比
   └─ 记录完整性 | Agent 填充率 | 证据质量
   └─ 前一天 vs 当前 环比趋势

九、行动建议（LLM 破局指南）
   └─ 主导画像诊断 + 核心卡壳点
   └─ 🔴 高优先级（15 分钟最大回报行动）
   └─ 🟡 中优先级（5 分钟最高性价比行动）
   └─ ⏱ 预期收益（时间 + 价值维度）

十、报告元信息
   └─ 版本 | 生成时间 | 数据来源 | 统计范围
```

**设计原则**：
- **证据驱动**：所有具体表现和典型场景必须引用 `session_analyses` 表中的原始 evidence（80-300 字语义化原文），禁止编造。每条 evidence 包含：事实锚点 + 原文片段（带引号）+ 认知解读
- **加权聚合**：评价 = 时间段加权平均（权重 = session 持续时间秒数，高=3/中=2/低=1）；趋势基于时间序列变化
- **双 LLM 润色**：LLM-A 负责「引语 + 整体建议」（温暖、洞察、不爹味），LLM-B 负责「破局指南」（犀利、actionable、指出具体卡点）
- **静默触发**：用户不召唤不输出，召唤时一次性给全量，不逐条推送
- **封顶原则**：引语 ~120 字，整体建议 ≤200 字，具体表现 30-50 字/条，宁断勿水







## 数据流与过滤体系

```
OpenClaw JSONL 日志 (100%)
    ↓
导入层（4层噪音检测 + 双层标记 + 内容合并）
    ↓
sessions 表（语义完整、无碎片、噪音标记分离）
    ↓
SessionCutter（三层切割：硬规则→向量层→LLM仲裁）
    ↓
SessionAnalyzer（LLM 4维分析 v8.7）
    ↓
StateDistiller（14条规则 → Portrait + 4D基线）
    ↓
session_analyses 表
    ↓
ReportAssembler（用户召唤 /deepflow 时组装报告）
```

**双层标记字段**：
- `is_system_noise` —— 心跳/cron/空内容，完全排除分析
- `is_auto_push` —— Agent 中转/纯确认响应，保留数据但排除分析

**工作流合并**：AI 的「一问多答」（工具调用链、流式分段）合并为一条完整回复，数据质量从 A- 提升到 S 级（97/100）。

---

## 快速开始

### 方式一：首次安装（一键）

```bash
git clone <repo-url>
cd flow-evolution-for-mind

./install.sh
```

`install.sh` 自动完成：
- ✅ 备份现有 OpenClaw 配置
- ✅ 同步 Plugin 到 `~/.openclaw/extensions/`
- ✅ 安装 sqlite3 依赖
- ✅ 同步 Skill 脚本到 `~/.openclaw/skills/`
- ✅ 自动给所有 Agent 绑定 Skill
- ✅ 重启 Gateway

安装完成后，在飞书对任意 Agent 输入 **`/deepflow`** 即可获取认知体检报告。

> ⚠️ **注意**：OpenClaw `secretary` Agent 内置 `/flow` 快捷方式，外部 Skill 无法覆盖。请使用 `/deepflow` 或 `/cognitive-report`。

### 方式二：全链路重建（清库 → 导入 → 切割 → 分析 → 验证）

如果你需要从头重建全部历史数据（比如修复导入层 bug 后验证数据质量）：

```bash
python3 scripts/run_full_pipeline.py
```

一键自动完成：
1. 备份现有数据库
2. 清空所有表 + 删除 `.collect_state.json`（关键！不清除会导致导入 0 条）
3. 全量导入（修复后的 base_parser.py + HEARTBEAT 前缀匹配）
4. 全量切割（全历史扫描，不再只扫 60 分钟）
5. 全量分析（遍历所有日期，逐个 Session 调用 LLM v8.7 Prompt）
6. 质量验证（成功率 / 4 维分布 / Portrait 画像 / 证据长度）

**耗时**：约 15-40 分钟（取决于历史数据量和 API 响应速度）。

---

## 使用方式

### 主动召唤（展示层）

```
/deepflow                    # 生成完整认知体检报告
/deepflow today              # 今日报告
/deepflow week               # 本周报告
/cognitive-report            # 同 /deepflow
```

### 实时调音（静默层，用户无感知）

无需任何操作。每轮对话前，系统自动读取 `kv_store.current_style`，注入 4D 调音参数，AI 的语气/深度/阻力会自然适配你当前的状态。

---

## 项目结构

```
openclaw_flow_plugin/
├── adapters/openclaw/
│   ├── plugin/dist/              # Plugin 分发（Soul 协议 + Injector）
│   │   ├── hooks/injector.js     # 4D 调音注入器
│   │   └── soul-protocols/       # 14 种 Portrait 定义
│   └── scripts/
│       ├── flow_handler.py       # /deepflow 报告生成（只读，WAL 模式）
│       ├── init.py               # 全量导入 + 流式合并
│       └── SKILL.md              # Skill 描述（LLM 触发用）
├── core/
│   └── openclaw_path_resolver.py # 跨平台路径发现（Mac/Linux/Windows）
├── importer/
│   ├── base_parser.py            # JSONL 解析（content 数组多段 text 合并）
│   └── incremental.py            # 增量导入 + 4层噪音检测 + AutoCut/AutoAnalyze（24h窗口）
├── plugin/
│   ├── llm_client.py             # LLM API 客户端（硅基流动 / DeepSeek）
│   ├── session_analyzer.py       # v8.7 Prompt，4 维判定 + GoalExtractor
│   ├── state_distiller.py        # 14 条规则 → Portrait + 4D 基线
│   └── goal_extractor.py         # 从 MEMORY.md 提取长期目标（24h 缓存）
├── batch_session_cutter.py       # 三层渐进式切割（全量扫描）
├── batch_analyze_with_save.py    # 批量分析 + 工作流合并（30秒阈值）
├── scripts/
│   ├── install.sh                # 一键安装
│   ├── run_full_pipeline.py      # 一键全链路重建（新增）
│   ├── stop_all.sh               # 一键杀进程 + 清 SQLite 锁
│   └── start_poll.sh             # 一键启动后台轮询引擎
├── docs/
│   └── PLATFORM_LIMITATIONS.md   # 开发者防坑指南
├── data/
│   └── flow_ecosystem.db         # SQLite 数据库
├── README.md                     # 本文档
├── requirements.txt              # Python 依赖
└── .env.example                  # 环境变量模板
```

---

## 技术栈

- **Runtime**: Python 3.9+ / Node.js 18+
- **Database**: SQLite3（WAL 模式，支持并发读写）
- **AI**: DeepSeek-V3 / MiniMax（通过硅基流动或官方 API）
- **向量**: sentence-transformers（all-MiniLM-L6-v2，本地运行）
- **Platform**: OpenClaw Gateway + 飞书 Bot

---

## ⚠️ Known Platform Limitations

### 1. `/flow` 被系统 Agent 占用
OpenClaw `secretary` Agent 内置 `/flow` 快捷方式，外部 Skill **无法覆盖**。

**解决**：使用 `/deepflow` 或 `/cognitive-report` 触发，或将 Skill 绑定到非系统 Agent（如 `newness`）。

### 2. `database is locked`
如果看到此错误：
```bash
bash scripts/stop_all.sh  # 杀后台进程 + 清 SQLite 锁文件
```
根因：旧版 `flow_handler.py` 同时做写入 + 分析，与后台轮询引擎抢锁。当前版已改为**只读 + WAL 模式**。

### 3. 后台进程管理
```bash
bash scripts/start_poll.sh   # 启动轮询引擎（30秒间隔同步）
bash scripts/stop_all.sh     # 停止所有后台进程
```

---

## 开发者坑点指南（10 条铁律）

| # | 坑点 | 预防措施 |
|---|------|----------|
| 1 | 导入后 U:A 比值失真 (0.49) | `base_parser.py` 合并 content 数组所有 text 段，不只取 `[0]` |
| 2 | HEARTBEAT 混入有效数据 | 用 `startswith('Read HEARTBEAT.md')` 前缀匹配，**不限制 role** |
| 3 | 清库后导入 0 条 | **必须** `rm -f .collect_state.json` 重置导入状态 |
| 4 | 切割后 session 极少 (3 个) | `find_uncut_sessions` 默认 `since_minutes=None`（全量扫描） |
| 5 | API 批量分析超时 | 国内优先**硅基流动** `api.siliconflow.cn`，timeout ≥ 60s |
| 6 | 单条指令超过 6000 字 | 超限必须分步骤拆解 |
| 7 | DB Browser 看到 HEARTBEAT 以为是 bug | 查询必须加 `WHERE is_system_noise=0 OR is_system_noise IS NULL` |
| 8 | 切割后 avg 16.3 条以为是 bug | 真实工作场景对话较长，1-10 条占比 50%+ 即为正常 |
| 9 | `flow_handler.py` 写入导致锁 | 当前版已改为**只读**，绝不 INSERT/UPDATE |
| 10 | 跨平台路径问题 | `core/openclaw_path_resolver.py` 四级兜底（环境变量→配置→探测→交互） |

---

## 故障排查

### `/deepflow` 无响应
1. 检查 Skill 绑定：`grep flow-evolution-for-mind ~/.openclaw/openclaw.json`
2. 查看日志：`tail -f /tmp/openclaw/*.log | grep -i flow`
3. 确认触发词：用 `/deepflow` 而非 `/flow`

### 数据库表不存在
```bash
python3 adapters/openclaw/scripts/init.py
```

### agent_id 为 NULL
```bash
# 清理 NULL 记录并重新导入
sqlite3 data/flow_ecosystem.db "DELETE FROM sessions WHERE agent_id IS NULL;"
python3 -c "from importer.incremental import run_once; run_once()"
```

---

## 版本历史

### V7.8-9-7-1（当前版本）
- ✅ **全链路重建脚本** `scripts/run_full_pipeline.py`（一键清库→导入→切割→分析→验证）
- ✅ **base_parser.py** 修复 content 数组多段 text 合并（层面 B 碎片）
- ✅ **HEARTBEAT 前缀匹配** 修复（`startswith('Read HEARTBEAT.md')`，不限制 role）
- ✅ **batch_session_cutter.py** 默认全量扫描（`since_minutes=None`）
- ✅ **数据质量 S 级**（U:A 0.65 / HEARTBEAT 100% 标记 / 噪音清除 96.3%）
- ✅ **Phase 1 核心链路 100% 跑通**

### V7.8-9-7
- ✅ `flow_handler.py` 只读 + WAL 模式 + `timeout=30`
- ✅ `/deepflow` 触发词（避开 secretary 内置 `/flow`）
- ✅ `scripts/stop_all.sh` + `start_poll.sh` 运维标准化
- ✅ `docs/PLATFORM_LIMITATIONS.md` 开发者防坑指南

### V7.8-9-6
- ✅ Prompt v8.7 + GoalExtractor（外部目标参照系）
- ✅ 4 维解耦（只有目标对齐度读取 MEMORY.md）
- ✅ 隐藏思考链（a/b/c 强制对比，不泄露到输出）

### V7.8-9-5
- ✅ 双层标记体系（`is_system_noise` + `is_auto_push`）
- ✅ 4 层噪音检测规则
- ✅ 工作流合并机制（30 秒阈值，38 条碎片合并）
- ✅ 白名单策略（`role IN ('user', 'assistant')`）

### V7.8-9-3
- ✅ 全自动安装脚本（`install.sh`）
- ✅ 自动绑定 Skill 到所有 Agent
- ✅ sys.argv 参数污染隔离
- ✅ 动态 Schema 演进

---

## 路线图

| 阶段 | 功能 | 状态 |
|------|------|------|
| **Phase 1** | 实时调音 + Session 分析 + 报告展示 | ✅ 100% 跑通 |
| **Phase 2** | 仪表盘 + 跨 Session 模式识别 + 基于 4 维的 42 维精细分析扩展 | ⏳ 待实现 |
| **Phase 3** | 时序 + GraphRAG 的自然涌现 | 🔮 远期 |

---

## 许可证

MIT License

---

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request


