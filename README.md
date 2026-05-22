# Flow Ecosystem - 认知流分析系统

## ⚠️ Known Platform Limitations

### 1. OpenClaw Agent Routing
System Agents (e.g., `secretary`) may reserve `/flow` for internal use. External Skills **cannot override** these bindings.

**Solution**: Use `/deepflow` or `/cognitive-report` as trigger, or bind the Skill to a non-system Agent (e.g., `newness`).

### 2. Database Locking
If you see `database is locked`:
```bash
bash scripts/stop_all.sh  # Kill background watcher + clean locks
```
Root cause: Older flow_handler.py tried to sync + cut + analyze inside the report handler, competing with background watcher.py. Current version is read-only.

### 3. Background Process Management
```bash
# Start sync (run once per session)
bash scripts/start_poll.sh

# Stop all background processes
bash scripts/stop_all.sh
```

## 项目简介

Flow Ecosystem 是一个基于 OpenClaw 的认知流分析插件，提供：
- 🪞 **镜像反思 (Mirror)** - 分析对话中的学习模式和认知偏差
- 🔧 **工具推荐 (Tool Recommend)** - 基于上下文推荐最佳工具
- 🚀 **解锁建议 (Unblock)** - 识别瓶颈并提供突破方案
- 🎨 **Style Scanner** - 自动分析并调整 5D 风格参数

## 核心特性

### 1. Soul 协议集成
- 14 种认知状态定义（portraits.json）
- 基于 Portrait 的动态风格调整
- 5D Style 系统：pace/depth/tone/friction

### 2. 智能数据管理
- 增量 JSONL 导入（自动发现路径）
- 备份文件过滤（.reset.* / .checkpoint.*）
- 动态 Schema 演进（ALTER TABLE）
- Agent 隔离与数据分段

### 3. AutoCut / AutoAnalyze
- 自动切割长会话为语义片段
- LLM 驱动的认知分析
- 报告持久化到 session_analyses 表

## 快速安装（一键）

```bash
git clone <repo-url>
cd flow-evolution-for-mind

./install.sh
```

安装脚本自动完成：
- ✅ 备份现有 OpenClaw 配置
- ✅ 同步 Plugin 到 ~/.openclaw/extensions/
- ✅ 安装 sqlite3 依赖
- ✅ 同步 Skill 脚本到 ~/.openclaw/skills/
- ✅ 自动给所有 Agent 绑定 flow-evolution-for-mind Skill
- ✅ 重启 Gateway

安装完成后，在飞书对任意 Agent 输入 `/flow` 即可测试。

## 使用方式

### 基础命令
```
/flow mirror today              # 今日镜像反思
/flow tool_recommend week       # 本周工具推荐
/flow unblock yesterday         # 昨日解锁分析
/flow --update-style            # Style Scanner：更新调音
```

### 高级用法
```
/flow mirror date --date-value 2026-05-17   # 指定日期
/flow mirror last_N --limit 10              # 最近 N 次 Session
/flow mirror week --agent techboss          # 指定 Agent
```

## 项目结构

```
openclaw_flow_plugin/
├── adapters/
│   └── openclaw/
│       ├── plugin/
│       │   ├── dist/                    # Plugin 分发文件
│       │   │   ├── hooks/injector.js    # 注入器（Soul 协议加载）
│       │   │   └── soul-protocols/      # 认知状态定义
│       │   └── openclaw.plugin.json     # Plugin 元数据
│       └── scripts/
│           ├── flow_handler.py          # Skill 主入口
│           ├── init.py                  # 初始化脚本
│           └── SKILL.md                 # Skill 描述（LLM 触发用）
├── core/
│   └── openclaw_path_resolver.py        # 跨平台路径发现
├── importer/
│   ├── base_parser.py                   # JSONL 解析器
│   └── incremental.py                   # 增量导入引擎
├── batch_session_cutter.py              # 会话切割器
├── batch_analyze_with_save.py           # 批量分析器
├── install.sh                           # 一键安装脚本
└── data/
    └── flow_ecosystem.db                # SQLite 数据库
```

## 技术栈

- **Runtime**: Python 3.9+ / Node.js 18+
- **Database**: SQLite3 (via better-sqlite3)
- **AI**: LLM API (GPT-4 / Claude)
- **Platform**: OpenClaw Gateway + 飞书 Bot

## 开发指南

### 环境配置
```bash
# 可选：设置核心层路径（默认自动发现）
export FLOW_EVOLUTION_DIR=/path/to/project

# 可选：设置 OpenClaw 数据目录（默认 ~/.openclaw）
export OPENCLAW_DATA_DIR=/path/to/openclaw/data
```

### 本地测试
```bash
# 测试 Skill 入口
python3 adapters/openclaw/scripts/flow_handler.py \
  --intent-type mirror \
  --time-keyword today

# 测试增量导入
python3 -c "from importer.incremental import run_once; print(run_once())"

# 测试路径发现
python3 -c "from core.openclaw_path_resolver import find_openclaw_data_dir; print(find_openclaw_data_dir())"
```

### 调试日志
```bash
# 查看 Gateway 日志
tail -f /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log | grep -i flow

# 查看增量导入日志
python3 -c "from importer.incremental import run_once; run_once()" 2>&1 | grep "\[增量导入\]"
```

## 版本历史

### V7.8-9-3 (当前版本)
- ✅ 全自动安装脚本（6 步流程）
- ✅ 自动绑定 Skill 到所有 Agent
- ✅ sys.argv 参数污染隔离
- ✅ 动态 Schema 演进
- ✅ 备份文件过滤优化
- ✅ 跨平台路径发现模块

### V7.8-9-2
- Soul 协议集成（14 种认知状态）
- injector.js 重写
- agent_id 三层查询修复

### V7.8-9-1
- 初始版本发布
- 基础 Mirror/Tool/Unblock 功能

## 故障排查

### 问题：`/flow` 无响应
**原因**: LLM 未识别为 Skill 调用
**解决**:
1. 检查 SKILL.md 是否存在：`ls adapters/openclaw/scripts/SKILL.md`
2. 确认 Skill 已绑定：`grep flow-evolution-for-mind ~/.openclaw/openclaw.json`
3. 查看日志：`tail -f /tmp/openclaw/*.log | grep flow`

### 问题：数据库表不存在
**原因**: 首次运行未初始化
**解决**:
```bash
python3 adapters/openclaw/scripts/init.py
```

### 问题：agent_id 为 NULL
**原因**: JSONL 文件缺少 cwd 字段
**解决**:
```bash
# 清理 NULL 记录并重新导入
sqlite3 data/flow_ecosystem.db "DELETE FROM sessions WHERE agent_id IS NULL;"
python3 -c "from importer.incremental import run_once; run_once()"
```

## 许可证

MIT License

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

---

## 新用户安装流程（理想状态）

```bash
git clone <你的-repo-url>
cd flow-evolution-for-mind

# 一键安装（6步全自动，无需手动改配置）
./install.sh

# 完成。直接去飞书发 /flow。
```

全程不需要：
- ❌ 手动复制文件到 ~/.openclaw/
- ❌ 手动 npm install sqlite3
- ❌ 手动编辑 openclaw.json 绑定 Agent
- ❌ 手动重启 Gateway