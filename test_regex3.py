import re

response = """目标感：高，证据：⏱[Tue 2026-04-21 00:31 GMT+8]⏱用户主动发起数据对比请求，用户跳转至对PRD文档质量的验证，用户的所有决策都
闭环感：高，证据：用户通过对话产生了明确产出，包括数据分析结果和产品框架建议
沉浸感：中，证据：用户和助手围绕多个任务进行讨论，但中途出现多次系统工具调用
成长感：低，证据：用户在对话中未展现出对新概念的理解"""

dim_pattern = '|'.join(['目标感', '闭环感', '沉浸感', '成长感'])

# 尝试不同方式：逐行匹配证据
lines = response.split('\n')
print("=== 逐行解析 ===")
current_dim = None
current_level = None
current_evidence = []

for line in lines:
    # 检查是否是维度行
    dim_match = re.match(f'({dim_pattern})[:：]\\s*([高中低])', line)
    if dim_match:
        if current_dim and current_evidence:
            print(f"  {current_dim}: {current_level} | 长度: {len(''.join(current_evidence))} | 内容: {''.join(current_evidence)[:50]}...")
        current_dim = dim_match.group(1)
        current_level = dim_match.group(2)
        current_evidence = []
        # 提取证据部分（冒号后的所有内容）
        after_evidence = re.sub(f'^{current_dim}[:：]\\s*[高中低][，,]\\s*证据[:：]\\s*', '', line)
        current_evidence.append(after_evidence)
    else:
        current_evidence.append(line.strip())

if current_dim and current_evidence:
    print(f"  {current_dim}: {current_level} | 长度: {len(''.join(current_evidence))}")