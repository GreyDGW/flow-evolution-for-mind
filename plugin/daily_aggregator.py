#!/usr/bin/env python3
"""
DailyAggregator - 日级聚合器
整合 ClosureAnalyzer + ConceptTracker 计算日级结构质量分
PRD 7.4 跨日稳定性公式: cross_day_stability = 0.5 + hub_stability
"""

from typing import List, Dict
from core.concept_tracker import ConceptTracker


class DailyAggregator:
    """日级聚合器"""

    def __init__(self):
        self.tracker = ConceptTracker()

    def aggregate(self, date: str, session_results: List[Dict]) -> Dict:
        """
        执行日级聚合

        Args:
            date: 日期字符串 (YYYY-MM-DD)
            session_results: 该日所有 Session 的分析结果

        Returns:
            日级聚合结果包含:
            - avg_ewci: 平均EWCI
            - avg_flow: 平均心流深度
            - structure_quality: 结构质量分
            - hub_stability: Hub跨日稳定性
            - cross_day_stability: PRD 7.4跨日稳定性系数 (0.5~1.5)
        """
        if not session_results:
            return {
                "date": date,
                "avg_ewci": 0,
                "avg_flow": 0,
                "structure_quality": 0,
                "hub_stability": 1.0,
                "cross_day_stability": 1.0,
                "session_count": 0,
                "concept_count": 0
            }

        valid = [r for r in session_results if r.get('ewci', 0) > 0 or r.get('flow_depth', 0) > 0]

        if not valid:
            hub_stability = self.tracker.calculate_hub_stability(date)
            cross_day_stability = 0.5 + hub_stability
            cross_day_stability = max(0.5, min(1.5, cross_day_stability))
            return {
                "date": date,
                "avg_ewci": 0,
                "avg_flow": 0,
                "structure_quality": 0,
                "hub_stability": hub_stability,
                "cross_day_stability": round(cross_day_stability, 2),
                "session_count": len(session_results),
                "concept_count": 0
            }

        avg_ewci = sum(r.get('ewci', 0) for r in valid) / len(valid)
        avg_flow = sum(r.get('flow_depth', 0) for r in valid) / len(valid)

        structure_quality = avg_flow * (avg_ewci / 100) * 100

        today_concepts = self.tracker.extract_concepts(session_results)
        self.tracker.store_daily_concepts(date, today_concepts)

        hub_stability = self.tracker.calculate_hub_stability(date)
        yesterday_hub = self.tracker.get_yesterday_hub_stability(date)

        cross_day_stability = 1 + (hub_stability - yesterday_hub) * 0.5
        cross_day_stability = max(0.5, min(1.5, cross_day_stability))

        return {
            "date": date,
            "avg_ewci": round(avg_ewci, 1),
            "avg_flow": round(avg_flow, 1),
            "structure_quality": round(structure_quality, 1),
            "hub_stability": hub_stability,
            "cross_day_stability": round(cross_day_stability, 2),
            "session_count": len(session_results),
            "concept_count": len(today_concepts)
        }

    def get_daily_stats(self, date: str) -> Dict:
        """获取某日统计"""
        return self.tracker.get_stats(date)

    def generate_report(self, date: str) -> str:
        """生成日级报告"""
        stats = self.get_daily_stats(date)
        agg = self.aggregate(date, [])

        report_lines = [
            f"📊 日级报告 - {date}",
            "=" * 40,
            f"概念数量: {stats.get('concept_count', 0)}",
            f"Hub稳定性: {stats.get('hub_stability', 0):.2f}",
            f"跨日稳定性: {agg.get('cross_day_stability', 0):.2f}",
        ]

        concepts = stats.get('concepts', [])
        if concepts:
            report_lines.append(f"\n🔥 今日概念 ({len(concepts)}个):")
            for c in concepts[:5]:
                report_lines.append(f"  • {c}")
            if len(concepts) > 5:
                report_lines.append(f"  ... 还有{len(concepts) - 5}个")

        return "\n".join(report_lines)