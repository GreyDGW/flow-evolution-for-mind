#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 base_parser.py 多段 text 提取 v3 - 修复引号问题
"""

import re

path = 'importer/base_parser.py'
with open(path, 'r') as f:
    content = f.read()

# 查找 _extract_content_parts 函数
pattern = r'(def _extract_content_parts\([^)]*\):)(.*?)(?=\ndef [a-zA-Z_]|$)'
match = re.search(pattern, content, re.DOTALL)

if not match:
    print('❌ 未找到 _extract_content_parts 函数')
    exit(1)

func_start = match.start()
func_header = match.group(1)
body = match.group(2)

# 使用双引号避免单引号冲突
join_check = chr(39) + "'.join(texts)" + chr(39)

# 检查是否已经支持多段合并
if 'for item in content' in body and join_check in body:
    print('✅ 已支持多段合并，跳过')
    exit(0)

# 检查是否有旧的 content[0] 模式
if 'content[0]' not in body:
    print('⚠️ 无 content[0] 模式，输出函数体供检查:')
    print(body[:800])
    exit(1)

# 执行替换：将 content[0].get('text', ...) 改为多段合并逻辑
old_pattern = r"(\s+)text_content\s*=\s*content\[0\]\.get\('text'[^)]*\)[^)]*"
new_code = r"""\1texts = [item.get('text', '') for item in content if item.get('type') == 'text']
\1text_content = '\n'.join(texts) if texts else None"""

new_body, count = re.subn(old_pattern, new_code, body, count=1)

if count == 0:
    # 尝试更宽松的模式
    old_pattern2 = r"(\s+)text_content\s*=\s*content\[0\][^\n]*"
    new_body, count = re.subn(old_pattern2, new_code, body, count=1)

if count == 0:
    print('⚠️ 自动替换失败，请手动检查')
    print('\n当前 body 内容（前600字符）:')
    print(body[:600])
    exit(1)

# 组装新内容
new_content = content[:func_start] + func_header + new_body + content[match.end():]

with open(path, 'w') as f:
    f.write(new_content)

print('✅ base_parser.py: 已修复为多段 text 合并')
