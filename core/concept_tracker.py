#!/usr/bin/env python3
"""
ConceptTracker - Hub 概念追踪器
PRD 7.4 核心组件：追踪跨日概念稳定性（全球兼容，向量语义匹配）
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Set


class ConceptTracker:
    """Hub 概念追踪器"""

    DEFAULT_PATH = Path.home() / ".openclaw" / "concepts.json"

    def __init__(self, storage_path: Path = None, model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2'):
        self.storage_path = storage_path or self.DEFAULT_PATH
        self._ensure_storage()
        self.model = None
        self._model_name = model_name

    def _ensure_storage(self):
        if not self.storage_path.exists():
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.storage_path.write_text('{}', encoding='utf-8')

    def _load(self) -> Dict:
        try:
            return json.loads(self.storage_path.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save(self, data: Dict):
        self.storage_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    def _init_model(self):
        """懒加载 sentence-transformers（全球兼容）"""
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(self._model_name)
            except ImportError:
                pass

    def _fingerprint(self, text: str) -> str:
        """保留语义文本供向量编码（全球兼容）"""
        cleaned = text.strip().replace('\n', ' ')
        return cleaned[:80]

    def extract_concepts(self, session_results: List[Dict]) -> Set[str]:
        """从 Session 结果提取概念指纹"""
        concepts = set()
        for result in session_results:
            goal = result.get('goal', {})
            if goal.get('evidence'):
                concepts.add(self._fingerprint(goal['evidence']))
            pdca = result.get('pdca', {})
            for stage in ['plan', 'do', 'check', 'adjust']:
                evidence = pdca.get(stage, {}).get('evidence', '')
                if evidence:
                    concepts.add(self._fingerprint(evidence))
            flow = result.get('flow', {})
            bq = flow.get('base_quality', {})
            for key in ['logic_depth', 'orderliness', 'progression', 'judgment_vector', 'goal_alignment']:
                evidence = bq.get(key, {}).get('evidence', '')
                if evidence:
                    concepts.add(self._fingerprint(evidence))
            sg = flow.get('signal_gain', {})
            for key in ['rebellion', 'persistent_questioning', 'self_correction', 'time_depth', 'meta_cognition']:
                evidence = sg.get(key, {}).get('evidence', '')
                if evidence:
                    concepts.add(self._fingerprint(evidence))
            cog = result.get('cognition', {})
            for key in ['concept_density', 'causal_depth', 'self_correction_freq', 'cross_domain_links']:
                evidence = cog.get(key, {}).get('evidence', '')
                if evidence:
                    concepts.add(self._fingerprint(evidence))
        return {c for c in concepts if len(c) >= 3}

    def store_daily_concepts(self, date: str, concepts: Set[str]):
        """存储某日概念集合"""
        data = self._load()
        data[date] = list(concepts)
        self._save(data)

    def get_concepts(self, date: str) -> Set[str]:
        """读取某日概念集合"""
        data = self._load()
        return set(data.get(date, []))

    def calculate_hub_stability(self, today: str, yesterday: str = None) -> float:
        """Hub 跨日稳定性：向量语义匹配（跨语言，全球兼容）"""
        today_set = self.get_concepts(today)
        if yesterday is None:
            dates = sorted(self._load().keys())
            if today in dates and dates.index(today) > 0:
                yesterday = dates[dates.index(today) - 1]
            else:
                return 1.0
        yesterday_set = self.get_concepts(yesterday)
        if not yesterday_set or not today_set:
            return 1.0
        # 向量语义匹配
        self._init_model()
        if self.model is not None:
            today_emb = self.model.encode(list(today_set))
            yesterday_emb = self.model.encode(list(yesterday_set))
            a_norm = today_emb / np.linalg.norm(today_emb, axis=1, keepdims=True)
            b_norm = yesterday_emb / np.linalg.norm(yesterday_emb, axis=1, keepdims=True)
            sim_matrix = np.dot(a_norm, b_norm.T)
            max_sims = sim_matrix.max(axis=1)
            stability = float(np.mean(max_sims))
            return round(stability, 2)
        # Fallback: Jaccard
        intersection = len(today_set & yesterday_set)
        union = len(today_set | yesterday_set)
        if union == 0:
            return 1.0
        return round(intersection / union, 2)

    def get_stats(self, date: str) -> Dict:
        """获取某日概念统计"""
        concepts = self.get_concepts(date)
        all_dates = sorted(self._load().keys())
        prev_date = None
        if date in all_dates and all_dates.index(date) > 0:
            prev_date = all_dates[all_dates.index(date) - 1]
        stability = self.calculate_hub_stability(date, prev_date) if prev_date else 1.0
        return {
            "date": date,
            "concept_count": len(concepts),
            "concepts": list(concepts),
            "prev_date": prev_date,
            "hub_stability": stability
        }
