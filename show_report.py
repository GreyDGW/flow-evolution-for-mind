from plugin.report_assembler import ReportAssembler

asm = ReportAssembler()
report = asm.generate_flow_report(start='2026-04-19 00:00:00', end='2026-04-19 23:59:59')

print("=" * 70)
print("📋 4月19日完整Flow报告")
print("=" * 70)
print(report)