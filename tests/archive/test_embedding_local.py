import sys, os
sys.path.insert(0, os.getcwd())
import path_setup

from plugin.session.embedding import create_embedder, SentenceTransformerEmbedder

print("=== 测试本地模型加载 ===")
try:
    embedder = create_embedder()
    print("嵌入器类型:", type(embedder).__name__)
    print("向量维度:", embedder.dimension)
    
    vec = embedder.encode("测试句子")
    print("编码成功，向量长度:", len(vec))
    
    vec2 = embedder.encode_batch(["句子1", "句子2"])
    print("批量编码成功，形状:", len(vec2), "x", len(vec2[0]))
    
    print("\n🎉 本地模型加载成功！")
except Exception as e:
    print("❌ 加载失败:", e)
    import traceback
    traceback.print_exc()