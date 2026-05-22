"""Flow Ecosystem - Plugin Core Module

核心组件：
- session_analyzer: LLM 4维判定（目标感、闭环感、心流深度、认知成长）
- state_distiller: 调音参数计算
- daily_aggregator: 日级统计聚合
- memory_manager: MEMORY.md 更新管理
- brave_search: 联网工具推荐
"""

from .session_analyzer import SessionAnalyzer, SessionAnalysis
from .state_distiller import StateDistiller, StyleParams, StatePortrait
from .daily_aggregator import DailyAggregator
from .memory_manager import MemoryManager
from .brave_search import BraveSearch
from .report_generator import ReportGenerator, FlowReport, BreakthroughGuide

__all__ = [
    "SessionAnalyzer",
    "SessionAnalysis",
    "StateDistiller",
    "StyleParams",
    "StatePortrait",
    "DailyAggregator",
    "MemoryManager",
    "BraveSearch",
    "ReportGenerator",
    "FlowReport",
    "BreakthroughGuide",
]