import re
from plugin.report_assembler import ReportAssembler

asm = ReportAssembler()
r20 = asm.generate_flow_report(start='2026-04-20 00:00:00', end='2026-04-20 23:59:59')

# 找出包含引号的文本片段
print('=== 报告中的引号分析 ===\n')

# 找所有可能的引用内容
for m in re.finditer(r'[""\u201c\u201c][^""\u201d\u201d]{5,100}[""\u201d\u201d]', r20):
    text = m.group()
    first_char = text[0]
    last_char = text[-1]
    print(f'找到: {text[:60]}...')
    print(f'  首字符: {repr(first_char)} (U+{ord(first_char):04X})')
    print(f'  尾字符: {repr(last_char)} (U+{ord(last_char):04X})')
    print()