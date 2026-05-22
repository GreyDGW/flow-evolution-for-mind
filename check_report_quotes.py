import re
from plugin.report_assembler import ReportAssembler

asm = ReportAssembler()
r20 = asm.generate_flow_report(start='2026-04-20 00:00:00', end='2026-04-20 23:59:59')

print('=== 检查报告中的引号使用 ===')

# 检查中文引号
cn_quotes = re.findall(r'"[^"]+"', r20)
print(f'\n中文双引号: {len(cn_quotes)} 处')
for q in cn_quotes[:5]:
    print(f'  "{q}"')

# 检查英文引号
en_quotes = re.findall(r'"[^"]+"', r20)
print(f'\n英文双引号: {len(en_quotes)} 处')
for q in en_quotes[:5]:
    print(f'  "{q}"')

print(f'\n总报告长度: {len(r20)} 字')