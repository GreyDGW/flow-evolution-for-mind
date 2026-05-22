import re

response = """目标感：高，证据：⏱[Tue 2026-04-21 00:31 GMT+8]⏱用户主动发起数据对比请求，用户跳转至对PRD文档质量的验证，用户的所有决策都
闭环感：高，证据：用户通过对话产生了明确产出，包括数据分析结果和产品框架建议
沉浸感：中，证据：用户和助手围绕多个任务进行讨论，但中途出现多次系统工具调用
成长感：低，证据：用户在对话中未展现出对新概念的理解"""

# 完整维度名
dim_pattern = '|'.join(['目标感', '闭环感', '沉浸感', '成长感'])
print(f"维度模式: {dim_pattern}")

patterns = [
    (f'({dim_pattern})[:：]\\s*([高中低])[，,]\\s*证据[:：]\\s*(.+?)(?=\\n({dim_pattern})|$)', 're.DOTALL'),
    (f'({dim_pattern})[:：]\\s*([高中低])[，,]\\s*证据[:：]\\s*(.+)', 're.DOTALL'),
]

for i, (p, flags) in enumerate(patterns):
    print(f"\n=== 模式 {i+1} (re.{flags}) ===")
    print(f"正则: {p[:80]}...")
    matches = re.findall(p, response, re.DOTALL)
    print(f"匹配数: {len(matches)}")
    for m in matches:
        print(f"  {m[0]}: {m[1]} | 长度: {len(m[2])}")