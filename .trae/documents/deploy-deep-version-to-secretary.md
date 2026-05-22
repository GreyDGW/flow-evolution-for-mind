# 部署计划：将深度版 Flow Handler 同步到 Secretary Workspace

## 📋 目标

将包含 **DeepReportFinal 深度版** + **ANTI_SUMMARY_PREFIX 防篡改机制** + **SKILL.md 输出约束** 的完整文件集部署到 Secretary Agent 的 workspace，确保 `/flow` 命令输出完整的深度认知分析报告。

---

## 🎯 当前状态确认

### ✅ 项目源文件已就绪

**[adapters/openclaw/scripts/flow_handler.py](adapters/openclaw/scripts/flow_handler.py)** (345行)
- ✅ 第59行: `from plugin.deep_report_final import DeepReportFinal` （深度版导入）
- ✅ 第307行: `drf = DeepReportFinal()` （深度版实例化）
- ✅ 第332-342行: `ANTI_SUMMARY_PREFIX` （防篡改前缀）
- ✅ 第342行: `print(ANTI_SUMMARY_PREFIX + report)` （强制完整输出）

**[adapters/openclaw/scripts/SKILL.md](adapters/openclaw/scripts/SKILL.md)**
- ✅ 第6-13行: `【输出约束 - 绝对遵守】` （输出约束死命令）

**[adapters/openclaw/scripts/init.py](adapters/openclaw/scripts/init.py)**
- ✅ 存在且为最新版本

### ❌ Secretary Workspace 缺少目标目录

当前路径：`~/.openclaw/agents/secretary/workspace/skills/`

**已存在的 skills：**
- agents-skill-security-audit
- cognitive-loop
- feedback-controller-clarkchenkai
- flowguard-for-cron

**❌ 缺失：**
- `flow-evolution-for-mind/` 目录不存在（需要创建）

---

## 📝 执行步骤

### Step 1: 创建目标目录结构

```bash
mkdir -p ~/.openclaw/agents/secretary/workspace/skills/flow-evolution-for-mind/scripts
```

**预期结果：**
- 创建路径：`~/.openclaw/agents/secretary/workspace/skills/flow-evolution-for-mind/scripts/`
- 如果父目录已存在则不报错

---

### Step 2: 复制核心文件（强制覆盖）

```bash
# 2.1 复制 flow_handler.py（深度版 + ANTI_SUMMARY_PREFIX）
cp /Users/duguowei/Desktop/skill相关文档/openclaw_flow_plugin/adapters/openclaw/scripts/flow_handler.py \
   ~/.openclaw/agents/secretary/workspace/skills/flow-evolution-for-mind/scripts/flow_handler.py

# 2.2 复制 init.py（模块初始化文件）
cp /Users/duguowei/Desktop/skill相关文档/openclaw_flow_plugin/adapters/openclaw/scripts/init.py \
   ~/.openclaw/agents/secretary/workspace/skills/flow-evolution-for-mind/scripts/init.py

# 2.3 复制 SKILL.md（含输出约束死命令）
cp /Users/duguowei/Desktop/skill相关文档/openclaw_flow_plugin/adapters/openclaw/scripts/SKILL.md \
   ~/.openclaw/agents/secretary/workspace/skills/flow-evolution-for-mind/SKILL.md
```

**预期结果：**
- 3个文件成功复制到目标目录
- 文件权限保持不变（644）
- 时间戳更新为当前时间

---

### Step 3: 验证文件完整性

```bash
# 3.1 列出目标目录内容
ls -lh ~/.openclaw/agents/secretary/workspace/skills/flow-evolution-for-mind/scripts/

# 3.2 验证 flow_handler.py 包含深度版特征
echo "=== 验证 DeepReportFinal ==="
grep "from plugin.deep_report_final import DeepReportFinal" \
  ~/.openclaw/agents/secretary/workspace/skills/flow-evolution-for-mind/scripts/flow_handler.py

echo ""
echo "=== 验证 ANTI_SUMMARY_PREFIX ==="
grep "ANTI_SUMMARY_PREFIX" \
  ~/.openclaw/agents/secretary/workspace/skills/flow-evolution-for-mind/scripts/flow_handler.py | head -1

# 3.3 验证 SKILL.md 包含输出约束
echo ""
echo "=== 验证 SKILL.md 输出约束 ==="
grep "输出约束.*绝对遵守" \
  ~/.openclaw/agents/secretary/workspace/skills/flow-evolution-for-mind/SKILL.md

# 3.4 对比文件大小（确保完整复制）
echo ""
echo "=== 文件大小对比 ==="
echo "源文件:"
ls -lh /Users/duguowei/Desktop/skill相关文档/openclaw_flow_plugin/adapters/openclaw/scripts/flow_handler.py | awk '{print $5, $9}'
echo "目标文件:"
ls -lh ~/.openclaw/agents/secretary/workspace/skills/flow-evolution-for-mind/scripts/flow_handler.py | awk '{print $5, $9}'
```

**预期输出：**
```
=== 验证 DeepReportFinal ===
from plugin.deep_report_final import DeepReportFinal

=== 验证 ANTI_SUMMARY_PREFIX ===
    ANTI_SUMMARY_PREFIX = """【系统指令 - 严格遵循】

=== 验证 SKILL.md 输出约束 ===
## 【输出约束 - 绝对遵守】

=== 文件大小对比 ===
源文件:
15K .../flow_handler.py
目标文件:
15K .../flow_handler.py
```

---

### Step 4: 清除 Python 缓存（关键！）

```bash
# 删除 __pycache__ 目录（避免使用旧编译版本）
find ~/.openclaw/agents/secretary/workspace/skills/flow-evolution-for-mind \
  -name "__pycache__" -type d -exec rm -rf {} +

# 删除 .pyc 文件
find ~/.openclaw/agents/secretary/workspace/skills/flow-evolution-for-mind \
  -name "*.pyc" -delete

echo "✅ Python 缓存已清除"
```

**原因说明：**
Python 会编译 `.py` 文件为 `.pyc` 缓存以加速加载
如果不删除缓存，即使源文件已更新，系统可能仍使用旧的浅度版编译版本

---

### Step 5: 可选 - 同步到全局 Skills 目录（推荐）

```bash
# 同时复制到全局路径（供其他 Agent 使用）
cp /Users/duguowei/Desktop/skill相关文档/openclaw_flow_plugin/adapters/openclaw/scripts/flow_handler.py \
   ~/.openclaw/skills/flow-evolution-for-mind/scripts/flow_handler.py

cp /Users/duguowei/Desktop/skill相关文档/openclaw_flow_plugin/adapters/openclaw/scripts/SKILL.md \
   ~/.openclaw/skills/flow-evolution-for-mind/SKILL.md

echo "✅ 已同步到全局 skills 目录"
```

**说明：**
- 全局路径 `~/.openclaw/skills/flow-evolution-for-mind/` 是 SKILL.md 中定义的 `{baseDir}`
- 这是所有 Agent 默认查找 skill 的位置
- 如果只部署到 secretary workspace，其他 Agent 可能仍使用旧版本

---

## 🧪 测试验证（部署后执行）

### 方法1：通过飞书测试

在飞书中向 Secretary Agent 发送：
```
/flow
```

**检查清单（必须全部满足）：**

| # | 特征 | 期望值 |
|---|------|--------|
| 1 | 报告开头 | 包含 `【系统指令 - 严格遵循】` |
| 2 | 标题格式 | `# Flow Ecosystem - YYYY-MM-DD 认知分析报告` |
| 3 | 总记录数 | 显示具体数字（如 `17 条`） |
| 4 | 四、各Agent表现详情 | 完整表格存在 |
| 5 | 五、关键Session亮点 | 3个子章节（最佳/典型/有待提升） |
| 6 | 七、各维度详细解读 | 4个子维度（目标对齐度/闭环/心流/认知） |
| 7 | 认知成长数据 | 不为0（如 `5 / 8 / 4 / 2.06`） |
| 8 | 九、行动建议 | 包含破局策略+马上行动+预期收益 |
| 9 | 报告总长度 | > 3700字符 |

---

### 方法2：本地快速验证（可选）

```bash
cd ~/.openclaw/agents/secretary/workspace/skills/flow-evolution-for-mind/scripts

python3 << 'PYEOF'
import sys
sys.path.insert(0, '/Users/duguowei/Desktop/skill相关文档/openclaw_flow_plugin')

from plugin.deep_report_final import DeepReportFinal

report = DeepReportFinal().generate('2026-04-19', '2026-04-20')

print(f"✅ 报告生成成功")
print(f"📊 长度: {len(report)} 字符")
print(f"🔍 前100字符: {report[:100]}")

# 关键特征检测
checks = [
    ('ANTI_SUMMARY_PREFIX', '【系统指令' in report),
    ('深度版标题', '认知分析报告' in report),
    ('总记录数', '17 条' in report or '总分析记录' in report),
    ('Agent详情', '四、各Agent' in report),
    ('Session案例', '五、关键Session' in report),
    ('维度解读', '七、各维度详细解读' in report),
    ('认知成长有值', '| 5 | 8 | 4 |' in report),  # 不是 | 0 | 0 | 0 |
    ('行动建议', '破局策略' in report and '马上行动' in report),
]

print("\n📋 功能检测:")
all_pass = True
for name, ok in checks:
    status = "✅" if ok else "❌"
    print(f"   {status} {name}")
    if not ok:
        all_pass = False

if all_pass:
    print("\n🎉 所有功能正常！Secretary Agent 将输出完整深度报告")
else:
    print("\n⚠️ 部分功能异常，请检查文件是否正确复制")
PYEOF
```

---

## ⚠️ 注意事项与风险提示

### 1. 权限问题
- 如果遇到 "Permission denied"，需要在终端手动执行（非 Trae IDE 环境）
- macOS 可能要求授予终端访问 `~/.openclaw/` 目录的权限

### 2. 进程缓存
- 即使文件已更新，正在运行的 OpenClaw 进程可能仍在内存中使用旧版本
- **建议：完全退出并重启 OpenClaw 应用**

### 3. 多 Agent 一致性
- 当前操作仅影响 **Secretary Agent**
- 其他 Agent（newness, product-manager, hr-agent 等）可能仍使用旧版本
- 如需全局升级，需重复此流程或使用 Step 5 的全局同步方法

### 4. 回滚方案
如果部署后出现问题：
```bash
# 恢复备份（如果之前有备份的话）
cp ~/.openclaw/skills/flow-evolution-for-mind/scripts/flow_handler.py.shallow.bak \
   ~/.openclaw/agents/secretary/workspace/skills/flow-evolution-for-mind/scripts/flow_handler.py
```

---

## 📊 成功标准

部署成功的标志：
1. ✅ 目标目录存在且包含3个文件（flow_handler.py, init.py, SKILL.md）
2. ✅ flow_handler.py 包含 `DeepReportFinal` 和 `ANTI_SUMMARY_PREFIX`
3. ✅ SKILL.md 包含 `【输出约束 - 绝对遵守】`
4. ✅ Python 缓存已清除
5. ✅ 本地测试或飞书测试显示完整深度报告（>3700字符，10大章节齐全）

---

## 🔄 后续优化建议（可选）

1. **自动化部署脚本**: 创建 `deploy_to_secretary.sh` 一键部署
2. **多 Agent 批量部署**: 循环遍历所有 Agent workspace 并复制
3. **版本管理**: 在文件名或头部添加版本号（如 `v8.7-deep`）
4. **监控机制**: 添加日志记录每次部署的时间和版本
