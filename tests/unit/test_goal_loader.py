import path_setup
#!/usr/bin/env python3
from src.core import GoalLoader, OpenClawLLMClient, get_llm_config
from src.session import ClosureAnalyzer
import time

# 1. 读取活跃目标（自动从 ~/.openclaw/memory.md）
loader = GoalLoader()
goals = loader.load_active_goals()
print(f'活跃目标数: {len(goals)}')
for g in goals:
    print(f'  [{g["type"]}] {g["text"]} (状态: {g["status"]}, 优先级: {g["priority"]})')

# 2. 用标准初始化创建 LLMClient（不再绕过）
client = OpenClawLLMClient(**get_llm_config())
analyzer = ClosureAnalyzer(client)

# 3. 测试对话
msgs = [
    {'role': 'user', 'content': '我打算重构订单模块，用策略模式替换if-else'},
    {'role': 'assistant', 'content': '策略模式适合多种计价规则'},
    {'role': 'user', 'content': '我实现了3个子类，单元测试覆盖率85%，压测QPS从1200提升到1800'},
]

print('\n开始分析...')
t0 = time.time()
result = analyzer.analyze_session(msgs, goals)
t1 = time.time()

print(f'耗时: {t1-t0:.1f}s')
print(f'EWCI: {result.get("ewci")}')
print(f'心流: {result.get("flow_depth")}')
print(f'推进: {result.get("goal_alignment", {}).get("goal_progress")}')
print(f'漂移: {result.get("goal_alignment", {}).get("drift_score")}')

# 4. 显示所有目标（包括非活跃）
all_goals = loader.get_all_goals()
print(f'\n所有目标: {len(all_goals)}个')
for g in all_goals:
    status_icon = '✅' if loader._is_active(g) else '⏸️'
    print(f'  {status_icon} [{g["type"]}] {g["text"]} ({g["status"]})')