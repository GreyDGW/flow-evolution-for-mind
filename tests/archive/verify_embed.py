import sys, os
sys.path.insert(0, os.getcwd())
import path_setup

print("=== 嵌入器测试 ===")

ST_AVAILABLE = False
try:
    from sentence_transformers import SentenceTransformer
    ST_AVAILABLE = True
    print("sentence_transformers 导入成功")
except ImportError as e:
    print("sentence_transformers 导入失败: " + str(e))

from plugin.session.embedding import create_embedder

embedder = create_embedder()
print("嵌入器类型: " + type(embedder).__name__)
print("向量维度: " + str(embedder.dimension))

vec1 = embedder.encode("帮我优化API性能")
vec2 = embedder.encode("Redis缓存配置方法")
print("vec1 长度: " + str(len(vec1)))
print("vec2 长度: " + str(len(vec2)))

print("\n嵌入器创建成功！")