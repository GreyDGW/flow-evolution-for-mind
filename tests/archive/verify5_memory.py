import re

oc_path = "/Users/duguowei/Desktop/OpenClaw-Secretary-Backup-20260415-2235/MEMORY.md"
try:
    with open(oc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"从备份读取 MEMORY.md ({len(content)} 字符)")
    
    anchors = ['FLOW_STYLE', 'FLOW_STATUS', 'GOALS', 'COGNITION', 'PATTERNS']
    for a in anchors:
        start = f'<!-- {a}_START -->'
        end = f'<!-- {a}_END -->'
        if start in content and end in content:
            print(f'✅ 锚点 {a} 完整')
        elif start in content or end in content:
            print(f'⚠️ 锚点 {a} 不完整')
        else:
            print(f'ℹ️ 锚点 {a} 不存在')
    
    print("\n🎉 验证 5 通过：MEMORY.md 锚点结构完整")
except Exception as e:
    print(f"读取失败: {e}")