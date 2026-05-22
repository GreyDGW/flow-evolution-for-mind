"""
TrendAnalyzer：本地趋势分析层
职责：时间范围过滤 + 4维异常检测 + 跨session规律 + 原文提取
不调用 LLM，纯本地算法
"""
import sqlite3
import statistics
from datetime import datetime, timedelta
from typing import List, Dict
from collections import Counter

class TrendAnalyzer:
    SCORE_MAP = {'高': 3, '中': 2, '低': 1}

    def __init__(self, db_path: str = "data/flow_ecosystem.db"):
        self.db_path = db_path

    def analyze_by_range(self, start_time=None, end_time=None, limit=None) -> Dict:
        sessions = self._fetch_sessions(start_time, end_time, limit)
        if len(sessions) < 2:
            return {"dimensions": {}, "anomalies": [], "patterns": []}

        result = {
            "session_count": len(sessions),
            "time_range": {
                "start": sessions[-1].get('created_at', ''),
                "end": sessions[0].get('created_at', '')
            },
            "dimensions": {},
            "anomalies": [],
            "patterns": []
        }

        for dim_name, dim_col in [
            ("目标对齐", "goal_alignment"),
            ("闭环指数", "closure_index"),
            ("心流深度", "flow_depth"),
            ("认知成长", "cognition_growth")
        ]:
            values = [s[dim_col] for s in sessions if s[dim_col]]
            result["dimensions"][dim_name] = self._analyze_single_dim(values)

        result["anomalies"] = self._detect_anomalies(sessions)
        result["patterns"] = self._detect_patterns(sessions)

        return result

    def _fetch_sessions(self, start_time, end_time, limit) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        if start_time and end_time:
            # 按对话发生时间过滤：通过 sessions 表的 session_id
            c.execute("""
                SELECT sa.*
                FROM session_analyses sa
                WHERE sa.session_id IN (
                    SELECT DISTINCT session_id FROM sessions 
                    WHERE timestamp BETWEEN ? AND ?
                )
                ORDER BY sa.created_at DESC
            """, (start_time, end_time))
        elif limit:
            c.execute("SELECT * FROM session_analyses ORDER BY created_at DESC LIMIT ?", (limit,))
        else:
            week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
            c.execute("SELECT * FROM session_analyses WHERE created_at >= ? ORDER BY created_at DESC", (week_ago,))

        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    def _analyze_single_dim(self, values: List[str]) -> Dict:
        scores = [self.SCORE_MAP.get(v, 2) for v in values]
        latest = values[0] if values else '中'
        latest_score = scores[0] if scores else 2

        recent = scores[:3]
        slope = recent[0] - recent[-1] if len(recent) >= 2 else 0
        short_term = "↗ 上升" if slope >= 1 else "↘ 下降" if slope <= -1 else "→ 平稳"

        if len(scores) >= 2:
            mean = statistics.mean(scores)
            std = statistics.stdev(scores)
            volatility = std / mean if mean > 0 else 0
        else:
            volatility = 0

        return {
            "history": " → ".join(values[:5]),
            "short_term": short_term,
            "stability": "高波动" if volatility > 0.5 else "中等波动" if volatility > 0.2 else "低波动"
        }

    def _detect_anomalies(self, sessions: List[Dict]) -> List[Dict]:
        SCORE_MAP = {'高': 3, '中': 2, '低': 1}
        dim_cols = ["goal_alignment", "closure_index", "flow_depth", "cognition_growth"]
        dim_labels = {"goal_alignment": "目标对齐", "closure_index": "闭环指数", "flow_depth": "心流深度", "cognition_growth": "认知成长"}
        evidence_cols = {"goal_alignment": "goal_evidence", "closure_index": "closure_evidence", "flow_depth": "flow_evidence", "cognition_growth": "cognition_evidence"}

        all_scores = []
        for s in sessions:
            for col in dim_cols:
                v = s.get(col)
                if v:
                    all_scores.append(SCORE_MAP.get(v, 2))

        if len(all_scores) < 3:
            return []

        mean = statistics.mean(all_scores)
        std = statistics.stdev(all_scores) if len(all_scores) > 1 else 0

        anomalies = []
        for s in sessions:
            for col in dim_cols:
                v = s.get(col)
                if not v:
                    continue
                score = SCORE_MAP.get(v, 2)
                z = (score - mean) / std if std > 0 else 0
                if abs(z) >= 1.5:
                    evidence_col = evidence_cols.get(col, col + "_evidence")
                    evidence = s.get(evidence_col, "") or ""
                    anomalies.append({
                        "dimension": dim_labels.get(col, col),
                        "value": v,
                        "z_score": round(z, 2),
                        "evidence": evidence[:60] if evidence else ""
                    })

        anomalies.sort(key=lambda x: abs(x["z_score"]), reverse=True)
        return anomalies[:10]

    def _detect_patterns(self, sessions: List[Dict]) -> List[str]:
        if len(sessions) < 3:
            return []

        patterns = []
        alignment_vals = [s.get("goal_alignment") for s in sessions if s.get("goal_alignment")]
        if len(set(alignment_vals)) == 1:
            patterns.append(f"goal alignment持续{alignment_vals[0]}（{len(alignment_vals)}/{len(sessions)}次）")

        return patterns