import os

fpath = '/Users/duguowei/Desktop/skill相关文档/flow-evolution-for-mind/README.zh.md'

with open(fpath, 'r') as f:
    old = f.read()
print(f"Old length: {len(old)}")

new = old

old_section = '''### 方式一：首次安装（一键）

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

> ⚠️ **注意**：OpenClaw `secretary` Agent 内置 `/flow` 快捷方式，外部 Skill 无法覆盖。请使用 `/deepflow` 或 `/cognitive-report`。'''

new_section = '''### 方式一：首次安装（一键 V3 — 推荐）

```bash
git clone https://github.com/GreyDGW/flow-evolution-for-mind.git
cd flow-evolution-for-mind

chmod +x install.sh && ./install.sh
```

`install.sh` (V3, 2026-05-25 全链路修复版) 覆盖 **11 个已验证坑位**，自动完成：
- ✅ **环境预检** (Python 3.11+, Node.js 18+, OpenClaw, sqlite3)
- ✅ **代码签名验证** (SDK 导入路径 / 项目名 / DeepFlow 拦截器 / SKILL.md)
- ✅ **npm 依赖安装** (sqlite3)
- ✅ **清理旧残留** (P9: agent workspace 旧 Skill / 多余 hooks/)
- ✅ **部署 Skill** (P7: 正确结构 — 仅 SKILL.md + scripts/)
- ✅ **OpenClaw CLI 插件注册** (`openclaw plugins install -l`)
- ✅ **配置 openclaw.json** (allowConversationAccess + load.paths + skills.entries + 全 Agent 绑定)
- ✅ **环境变量** (P4/P5: FLOW_EVOLUTION_DIR + ~/.flow_evolution_dir 标记文件 + .zshrc)
- ✅ **数据库初始化** (P1: current_style 冷启动，全部 Agent 自动注入默认值)
- ✅ **Gateway 重启** (P8: CLI restart，兼容 macOS launchd)
- ✅ **轮询引擎启动** (P0: 后台数据自动导入，30s 间隔)
- ✅ **全链路验证** (插件列表 / 响应时间 / 日志 / DB 统计)

> ⚠️ **旧版 `install_v2.sh` 已废弃**（仅覆盖 P0-P1，缺少 P4-P10 关键修复）

安装完成后：
1. 在**任意 Agent** 对话中输入 **`/deepflow`** 或 **`这周怎么样`** → 获取认知体检报告
2. 发送任意消息 → 系统自动注入 4D 调音参数（静默层，用户无感知）
3. 查看日志: `tail -f ~/Library/Logs/openclaw/gateway.log | grep flow-style`
4. 运行诊断: `bash healthcheck.sh`'''

new = new.replace(old_section, new_section)

old_limit = '## ⚠️ Known Platform Limitations\n\n### 1. `/flow` 被系统 Agent 占用\nOpenClaw `secretary` Agent 内置 `/flow` 快捷方式，外部 Skill **无法覆盖**。\n\n**解决**：使用 `/deepflow` 或 `/cognitive-report` 触发，或将 Skill 绑定到非系统 Agent（如 `newness`）。'

new_limit = '## ⚠️ 已知限制 & 解决方案\n\n### 1. `/flow` 触发（已通过 DeepFlow 拦截器解决）\nPlugin 层 `registerDeepFlowInterceptor()` 在 `before_prompt_build` 阶段拦截 `/deepflow`、`/flow`、自然语言查询（"这周怎么样"、"认知体检"等），**直接调用 `flow_handler.py` 并注入完整报告为系统消息**，绕过 LLM tool_use 限制。\n\n> 所有 Agent 均可使用 `/deepflow` 或 `/flow`。'

new = new.replace(old_limit, new_limit)

old_ver = '## 版本历史\n\n### V7.8-9-7-1（当前版本）'
new_ver = '''## 版本历史

### V7.8-9-7-2（当前版本 — 2026-05-25 全链路修复）
- **install.sh V3** -- 一键安装覆盖 11 个已验证坑位 (P0-P10)
- **DeepFlow 拦截器** -- Plugin 层 execFileSync 直接调用 Python，绕过 LLM tool_use 限制
- **SKILL.md PLATFORM LIMIT 移除** -- 改为 "Available to ALL"，所有 Agent 均可触发
- **硬编码路径修复** -- counter.js / injector.js 统一使用 flow-evolution-for-mind
- **Gateway 重启方法修正** -- 使用 openclaw gateway restart CLI（兼容 macOS launchd）
- **Agent workspace 清理** -- 自动清除旧 Skill 残留 (flow/, flow-state/)
- **环境变量标准化** -- FLOW_EVOLUTION_DIR + ~/.flow_evolution_dir 标记文件 + .zshrc
- **代码签名验证** -- 安装时自动检查 SDK 路径/项目名/拦截器/SKILL.md
- **DevOps 工具链** -- .gitignore / healthcheck.sh / Docker / CI workflow

### V7.8-9-7-1'''
new = new.replace(old_ver, new_ver)

with open(fpath, 'w') as f:
    f.write(new)

print(f"New length: {len(new)}")
print(f"Has V3: {'一键 V3' in new}")
print(f"Has P0: {'P0' in new}")
print(f"Has DeepFlow interceptor: {'DeepFlow 拦截器' in new}")
print("DONE!")
