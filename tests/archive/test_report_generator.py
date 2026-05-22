import sys, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
import path_setup

from plugin.session_analyzer import SessionAnalysis
from plugin.state_distiller import StateDistiller, StatePortrait, StyleParams
from plugin.report_generator import ReportGenerator
from plugin.session_analyzer import SiliconFlowLLMClient

analysis = SessionAnalysis(
    goal_alignment="低", goal_evidence="围绕API优化，偏离思维连续性保护器",
    closure_index="高", closure_evidence="4条落地方案",
    flow_depth="高", flow_evidence="沉浸3小时",
    cognition_growth="中", cognition_evidence="未突破"
)

portrait = StateDistiller().distill(analysis)

messages = [
    {"role": "user", "content": "我在想API性能优化，Redis还是本地内存？"},
    {"role": "assistant", "content": "Redis适合分布式。"},
    {"role": "user", "content": "序列化开销会不会瓶颈？"},
]

client = SiliconFlowLLMClient()
gen = ReportGenerator(client)
report = gen.generate(analysis, portrait, messages=messages, time_range="当天")

print("=" * 50)
print("标签:", report.summary[:40])
print("洞察:", report.rule_insight[:50])
print("漏洞数:", len(report.breakthrough.vulnerabilities))
print("回报:", report.breakthrough.max_return_tool[:40])

md = gen.format_markdown(report)
assert "📅 Flow 系统认知镜像" in md
assert "破局指南" in md
assert "开始行动" in md
print("\n✅ ReportGenerator 通过")