#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修改 init.py 添加导入后自动合并
"""

import re

path = 'adapters/openclaw/scripts/init.py'
with open(path, 'r') as f:
    content = f.read()

if 'merge_streaming_segments_in_db' in content:
    print('✅ 已有合并调用，跳过')
else:
    # 方法1: 在 "全量导入完成" 打印后添加合并调用
    pattern = r"(print\(f'✅ 全量导入完成.*?)\n"
    replacement = r"""\1
    # 流式分段合并（层面A修复：导入时归一化）
    from importer.incremental import merge_streaming_segments_in_db
    merge_streaming_segments_in_db(db_path)
    print('✅ 流式分段合并完成')
"""
    
    new_content, count = re.subn(pattern, replacement, content, count=1)
    
    if count == 0:
        # 备选方案：在文件末尾添加
        new_content = content.rstrip() + """

# 全量导入后执行流式分段合并
if __name__ == '__main__':
    from importer.incremental import merge_streaming_segments_in_db
    merge_streaming_segments_in_db()
"""
    
    with open(path, 'w') as f:
        f.write(new_content)
    
    print('✅ init.py: 已添加导入后自动合并（备选方案）')
    exit(0)
    
    with open(path, 'w') as f:
        f.write(new_content)
    
    print('✅ init.py: 已添加导入后自动合并')
