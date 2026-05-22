import re

test_str = '"你在这段复盘里主动推动了两轮分析请求"'

# 测试各种正则
patterns = [
    (r'"([^"]{10,60})"', '英文引号'),
    (r'["""]([^"""]{10,60})["""]', '中英文引号'),
    (r'[\u201c\u201d"]([^"\u201c\u201d]{10,60})[\u201c\u201d"]', 'Unicode引号'),
]

for p, desc in patterns:
    matches = re.findall(p, test_str)
    print(f'{desc}: {len(matches)} 处 - {matches}')

# 直接检查字符
print(f'\n字符串: {test_str}')
print(f'第一个字符: {repr(test_str[0])} (U+{ord(test_str[0]):04X})')
print(f'最后一个字符: {repr(test_str[-1])} (U+{ord(test_str[-1]):04X})')