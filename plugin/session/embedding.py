"""
会话切割向量层 - 文本嵌入器

支持三种嵌入模式（按优先级）：
1. SentenceTransformerEmbedder: 使用 paraphrase-multilingual-MiniLM-L12-v2（384维，推荐）
2. ChromaEmbedder: 使用 ChromaDB 内置 ONNX 模型（384维）
3. KeywordEmbedder: 基于关键词权重（无需外部依赖）
"""

from typing import List, Dict, Tuple, Optional, Union
import re
import os

# 强制使用本地 HuggingFace 缓存，禁止联网
os.environ["HF_HOME"] = os.path.expanduser("~/.cache/huggingface")
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

ST_AVAILABLE = False
try:
    from sentence_transformers import SentenceTransformer
    ST_AVAILABLE = True
except ImportError:
    pass

CHROMA_AVAILABLE = False
try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    pass


class SentenceTransformerEmbedder:
    MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2'

    def __init__(self, model_name: Optional[str] = None):
        if not ST_AVAILABLE:
            raise ImportError("sentence-transformers 未安装")

        self._model_name = model_name or self.MODEL_NAME
        self._model = SentenceTransformer(
            self._model_name,
            local_files_only=True,
            cache_folder=os.path.expanduser("~/.cache/huggingface/hub")
        )

    def encode(self, text: str) -> List[float]:
        result = self._model.encode([text])
        return result[0].tolist()

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        result = self._model.encode(texts)
        return result.tolist()

    @property
    def dimension(self) -> int:
        return 384


class ChromaEmbedder:
    def __init__(self):
        if not CHROMA_AVAILABLE:
            raise ImportError("ChromaDB 未安装")

        from chromadb.utils import embedding_functions
        self._func = embedding_functions.DefaultEmbeddingFunction()

    def encode(self, text: str) -> List[float]:
        result = self._func([text])
        return result[0]

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        return self._func(texts)

    @property
    def dimension(self) -> int:
        return 384


class KeywordEmbedder:
    def __init__(self, custom_keywords: Optional[Dict[str, List[str]]] = None):
        self._keyword_categories = custom_keywords or self._default_keywords()
        self._category_names = list(self._keyword_categories.keys())

    def _default_keywords(self) -> Dict[str, List[str]]:
        return {
            'database': ['数据库', 'sql', '表结构', '索引', '查询', 'mongodb', 'mysql',
                         'postgresql', 'redis', '存储', '事务', 'schema', 'orm',
                         'crud', 'join', '聚合', 'nosql', '关系型', '主键', '外键'],
            'api': ['接口', 'api', 'http', '请求', '响应', 'rest', 'graphql',
                    'endpoint', '路由', 'get', 'post', 'put', 'delete', 'webhook',
                    'axios', 'fetch', 'json', 'xml', 'header', 'body'],
            'code': ['代码', '函数', 'class', 'def', 'import', '变量', '方法',
                     '实现', 'bug', '调试', '逻辑', '算法', '数据结构', '循环',
                     '条件', '异常', 'try', 'except', 'return', '参数', '返回值'],
            'design': ['设计', '架构', '模式', '结构', '方案', '思路', '规划',
                       'uml', '流程图', '类图', '时序图', '组件', '模块', '层次',
                       '松耦合', '高内聚', '可扩展', '可维护'],
            'devops': ['部署', 'docker', 'kubernetes', 'k8s', 'ci', 'cd', 'jenkins',
                       '服务器', 'nginx', '容器', '镜像', 'pod', 'service', 'ingress',
                       'yaml', '配置文件', '环境变量', '负载均衡'],
            'ai_ml': ['模型', 'llm', 'ai', '训练', 'prompt', 'token', 'embedding',
                      '机器学习', '深度学习', '神经网络', '自然语言', 'nlp', 'cv',
                      'transformer', 'bert', 'gpt', '微调', '推理', '向量'],
            'testing': ['测试', '单元测试', '集成测试', 'e2e', '自动化', 'jest',
                        'pytest', 'coverage', '断言', 'mock', 'stub', 'spy', '基准'],
            'performance': ['性能', '优化', '缓存', '索引', '并行', '异步', '并发',
                           '延迟', '吞吐量', 'qps', 'tps', '响应时间', '加载', '瓶颈'],
            'business': ['需求', '业务', '产品', '用户', '市场', '运营', '增长',
                         'kpi', '指标', '数据', '分析', '报表', '仪表盘', '统计'],
            'general': ['问题', '解决', '方案', '帮助', '如何', '怎么', '为什么',
                        '什么', '哪里', '哪个', '请', '能不能', '是否可以', '需要']
        }

    def encode(self, text: str) -> List[float]:
        text_lower = text.lower()
        text_clean = re.sub(r'[^\w\s]', ' ', text_lower)

        vector = []
        for category in self._category_names:
            keywords = self._keyword_categories[category]
            count = sum(1 for kw in keywords if kw in text_clean)
            vector.append(count)

        return vector

    def cosine_sim(self, vec1: List[float], vec2: List[float]) -> float:
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    @property
    def dimension(self) -> int:
        return len(self._category_names)


def create_embedder(force_fallback: str = None) -> Union[SentenceTransformerEmbedder, ChromaEmbedder, KeywordEmbedder]:
    if force_fallback == 'sentence':
        print("使用 SentenceTransformerEmbedder")
        return SentenceTransformerEmbedder()

    if force_fallback == 'chroma':
        print("使用 ChromaEmbedder")
        if not CHROMA_AVAILABLE:
            print("ChromaDB 未安装，回退到 KeywordEmbedder")
            return KeywordEmbedder()
        return ChromaEmbedder()

    if force_fallback == 'keyword':
        print("使用 KeywordEmbedder")
        return KeywordEmbedder()

    if ST_AVAILABLE:
        try:
            print("使用 SentenceTransformerEmbedder")
            return SentenceTransformerEmbedder()
        except Exception as e:
            print(f"SentenceTransformerEmbedder 失败: {e}")

    if CHROMA_AVAILABLE:
        try:
            print("使用 ChromaEmbedder")
            return ChromaEmbedder()
        except Exception as e:
            print(f"ChromaEmbedder 失败: {e}")

    print("使用 KeywordEmbedder")
    return KeywordEmbedder()


def create_embedding_function(force_fallback: str = None):
    embedder = create_embedder(force_fallback=force_fallback)

    def embedding_func(text: str) -> List[float]:
        return embedder.encode(text)

    return embedding_func


if __name__ == "__main__":
    print("=" * 60)
    print("嵌入器测试")
    print("=" * 60)

    embedder = create_embedder()
    print(f"嵌入器类型: {type(embedder).__name__}")
    print(f"向量维度: {embedder.dimension}")

    test_text = "我想聊聊微服务架构设计和数据库优化"
    vector = embedder.encode(test_text)
    print(f"\n测试文本: {test_text}")
    print(f"向量长度: {len(vector)}")