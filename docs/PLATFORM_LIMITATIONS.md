# 平台限制与已知问题

## 1. secretary 内置 /flow 冲突（平台层）

- **现象**：飞书对 secretary 发 `/flow`，返回 LLM 自动摘要（~800字），不是 flow_handler.py 生成的完整深度报告（~4000字）
- **根因**：OpenClaw 对系统级 Agent（如 `secretary`）内置 `/flow` 快捷方式，外部 Skill 无法覆盖。这不是代码 bug，是平台路由层行为
- **解决**：使用非系统 Agent（如 `newness`）绑定 Skill，触发词用 `/deepflow` 或 `/cognitive-report`
- **验证**：本地执行 `python3 adapters/openclaw/scripts/flow_handler.py --intent-type mirror --time-keyword today | wc -c` 应 > 3500

## 2. database is locked（架构层）

- **现象**：执行 flow_handler.py 时报 `database is locked`，或飞书返回 "Agent couldn't generate a response"
- **根因**：旧版 flow_handler.py 同时执行数据同步（importer.run_once）+ Session切割（AutoCut）+ 自动分析（AutoAnalyze），与后台轮询引擎进程竞争 SQLite 写锁
- **解决**（已固化到代码）：
  - flow_handler.py 现为**只读报告生成器**，所有写操作由后台独立进程负责
  - 数据库连接使用 `timeout=30` + `PRAGMA journal_mode=WAL`
  - 标准化运维脚本：`bash scripts/stop_all.sh` 清锁，`bash scripts/start_poll.sh` 启后台轮询

## 3. 后台轮询进程管理（运维层）

- **现象**：即使退出 OpenClaw，数据库仍可能被锁定，`lsof` 显示 Python 进程占用
- **根因**：轮询引擎（incremental.py）是独立进程，不受 OpenClaw Gateway 生命周期管理
- **解决**：`bash scripts/stop_all.sh` 一键清理

## 架构铁律（防复发）

| 模块 | 职责 | 写入 DB？ | 触发方式 |
|------|------|-----------|----------|
| `importer/incremental.py` | 轮询同步 OpenClaw → SQLite（30s间隔） | ✅ | 后台常驻 |
| `batch_session_cutter.py` | Session 向量切割 | ✅ | 定时/cron |
| `batch_analyze_with_save.py` | LLM 4维分析 | ✅ | 定时/cron |
| `flow_handler.py` | 报告生成 | ❌ **只读** | 用户触发 |

**铁律**：`flow_handler.py` 只做 `SELECT` 和 `print(report)`，绝不 `INSERT/UPDATE`。
