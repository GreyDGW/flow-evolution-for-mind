# Plan: 清理临时文件

## 当前状态

### 1. 临时测试文件
已无临时测试文件（之前已删除）

### 2. __pycache__ 目录
需清理的目录：
- `plugin/__pycache__/` (9个 .pyc 文件)
- `plugin/calculator/__pycache__/` (5个 .pyc 文件)
- `plugin/session/__pycache__/` (5个 .pyc 文件)
- `plugin/trackers/__pycache__/` (5个 .pyc 文件)
- `openclaw_flow_plugin/__pycache__/` (1个 .pyc 文件)

## 执行步骤

1. 清理所有 __pycache__ 目录
   ```bash
   find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
   ```

2. 验证 plugin 目录结构完整

## 预期结果
所有 .pyc 缓存文件删除，保留所有源码文件