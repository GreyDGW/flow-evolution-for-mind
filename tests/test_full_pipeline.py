import sys, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
import path_setup

from plugin.session_analyzer import SessionAnalyzer, DeepSeekLLMClient
from plugin.state_distiller import StateDistiller
from plugin.report_generator import ReportGenerator

print("=" * 60)
print("🚀 Phase 1+2 完整链路测试 (DeepSeek)")
print("=" * 60)

messages = [
    {"role": "user", "content": "我在想这个API的性能优化方案，应该用Redis缓存还是本地内存？"},
    {"role": "assistant", "content": "Redis适合分布式，本地内存适合单机。你的场景是微服务架构，建议Redis。"},
    {"role": "user", "content": "但是Redis的序列化开销会不会成为瓶颈？"},
    {"role": "assistant", "content": "可以考虑二进制序列化，比如MessagePack，比JSON快3-5倍。"},
    {"role": "user", "content": "那如果缓存穿透怎么办？布隆过滤器还是互斥锁？"},
    {"role": "assistant", "content": "布隆过滤器适合读多写少，互斥锁适合一致性要求高。"},
]

print("\n【1/4】SessionAnalyzer → 4维判定")
client = DeepSeekLLMClient()
analyzer = SessionAnalyzer(client)
analysis = analyzer.analyze(messages, memory_path="MEMORY.md")

if not analysis:
    print("❌ SessionAnalyzer 失败")
    sys.exit(1)

print(f"  🎯 目标对齐: {analysis.goal_alignment} ({analysis.goal_evidence})")
print(f"  🔄 闭环指数: {analysis.closure_index} ({analysis.closure_evidence})")
print(f"  💫 心流深度: {analysis.flow_depth} ({analysis.flow_evidence})")
print(f"  🧠 认知成长: {analysis.cognition_growth} ({analysis.cognition_evidence})")

print("\n【2/4】StateDistiller → 规则匹配 + MEMORY.md 调音")
distiller = StateDistiller(memory_path="MEMORY.md")
portrait = distiller.distill(analysis)

print(f"  🏷️ 标签: {portrait.label}")
print(f"  🎛️ 调音: {portrait.style.pace}/{portrait.style.depth}/{portrait.style.tone}")

distiller.update_memory(portrait)
print("  💾 MEMORY.md FLOW_STYLE 已更新")

print("\n【3/4】ReportGenerator → /flow_report 生成")
generator = ReportGenerator(client)
report = generator.generate(analysis, portrait, messages=messages, time_range="当天")

print(f"  📝 总结: {report.summary[:50]}...")
print(f"  💡 漏洞数: {len(report.breakthrough.vulnerabilities)}")
print(f"  🔧 工具: {report.breakthrough.max_return_tool[:40]}...")

print("\n【4/4】format_markdown → 最终报告")
md = generator.format_markdown(report)

assert "📅 Flow 系统认知镜像" in md
assert "破局指南" in md
assert "开始行动" in md
assert "它不评判你" in md

print("\n" + "=" * 60)
print("✅ 完整链路验证通过！")
print("=" * 60)

print("\n【/flow_report 输出预览】\n")
print(md[:1000])
print("\n... (截断)")