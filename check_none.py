import traceback
from plugin.report_assembler import ReportAssembler

print('=== 问题2：定位 NoneType 错误 ===')
asm = ReportAssembler()
try:
    r20 = asm.generate_flow_report(start='2026-04-20 00:00:00', end='2026-04-20 23:59:59')
    print(f'报告已生成，长度: {len(r20)}')
except Exception as e:
    print(f'错误类型: {type(e).__name__}')
    print(f'错误信息: {e}')
    traceback.print_exc()