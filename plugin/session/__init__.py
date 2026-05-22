"""Flow Ecosystem - Session Management Module

三层渐进式会话切割：
- hard_rules: 硬规则层（0ms，80%触发）
- vector_layer: 向量判定层（<50ms，17%触发）
- llm_arbiter: LLM精判层（<2s，<3%触发）
- interaction: 离线聚类Interaction
"""

from .preprocessor import TurnPreprocessor
from .closure_analyzer import ClosureAnalyzer
from .session_cutter import SessionCutter, CutDecision, SessionCutResult, SemanticSessionCutter
from .embedding import (
    KeywordEmbedder,
    ChromaEmbedder,
    SentenceTransformerEmbedder,
    create_embedder,
    create_embedding_function,
)
from core.vector_layer import VectorLayer, VectorDecision
from .llm_arbiter import LLMArbiter

__all__ = [
    "TurnPreprocessor",
    "ClosureAnalyzer",
    "SessionCutter",
    "SemanticSessionCutter",
    "CutDecision",
    "SessionCutResult",
    "KeywordEmbedder",
    "ChromaEmbedder",
    "SentenceTransformerEmbedder",
    "create_embedder",
    "create_embedding_function",
    "VectorLayer",
    "VectorDecision",
    "LLMArbiter",
]
