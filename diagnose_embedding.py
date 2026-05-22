#!/usr/bin/env python3
"""诊断 embedding 模块状态"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("🔍 Embedding 模块诊断")
print("=" * 60)

# 1. 检查 embedding.py 的 create_embedder 逻辑
print("\n【1】检查 plugin/session/embedding.py 的 create_embedder 逻辑")
try:
    with open('plugin/session/embedding.py', 'r') as f:
        content = f.read()
    
    import re
    match = re.search(r'def create_embedder.*?return\s+(\w+)', content, re.DOTALL)
    if match:
        print(f"  create_embedder() 返回: {match.group(1)}")
    
    if 'class ChromaEmbedder' in content:
        print("  ✅ ChromaEmbedder 类存在")
    else:
        print("  ❌ ChromaEmbedder 类不存在")
    
    if 'class KeywordEmbedder' in content:
        print("  ✅ KeywordEmbedder 类存在")
    else:
        print("  ❌ KeywordEmbedder 类不存在")
        
    if 'sentence_transformers' in content:
        print("  ✅ 有 sentence-transformers 引用")
    else:
        print("  ⚠️ 无 sentence-transformers 引用")
        
except Exception as e:
    print(f"  ❌ 读取失败: {e}")

# 2. 检查 sentence-transformers 是否可用
print("\n【2】sentence-transformers 可用性")
try:
    from sentence_transformers import SentenceTransformer
    print("  ✅ sentence_transformers 已安装")
    
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    print(f"  ✅ 模型加载成功: {model.get_sentence_embedding_dimension()} 维")
except ImportError:
    print("  ❌ sentence_transformers 未安装")
except Exception as e:
    print(f"  ⚠️ 模型加载失败: {e}")

# 3. 检查 ONNX 可用性
print("\n【3】ONNX 可用性")
try:
    import onnxruntime
    print(f"  ✅ onnxruntime 已安装: {onnxruntime.__version__}")
except ImportError:
    print("  ❌ onnxruntime 未安装")

# 4. 检查模型文件
print("\n【4】模型文件检查")
import os
model_paths = [
    'models/all-MiniLM-L6-v2.onnx',
    'models/onnx',
    '~/.cache/chroma/onnx_models',
]
for p in model_paths:
    expanded = os.path.expanduser(p)
    if os.path.exists(expanded):
        print(f"  ✅ 存在: {expanded}")
    else:
        print(f"  ❌ 不存在: {expanded}")

# 5. 直接测试 create_embedder
print("\n【5】create_embedder() 实际返回")
try:
    from plugin.session.embedding import create_embedder
    e = create_embedder()
    print(f"  返回类型: {type(e).__name__}")
    
    vec = e.encode("测试文本")
    print(f"  编码结果: 向量长度={len(vec) if vec else 'None'}")
    
    if hasattr(e, '_dim'):
        print(f"  内部维度: {e._dim}")
except Exception as e:
    print(f"  ❌ 测试失败: {e}")

print("\n" + "=" * 60)
print("🔚 诊断结束")
print("=" * 60)