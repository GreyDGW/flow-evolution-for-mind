from typing import List, Dict, Optional
from core.llm_client import LLMClient, MockLLMClient


class ClosureAnalyzer:
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or MockLLMClient()

    def analyze_session(self, messages: List[Dict], active_goals: Optional[List[Dict]] = None) -> Dict:
        llm_result = self.llm_client.analyze_session(messages, active_goals)

        pdca = llm_result.get("pdca", {})
        completeness = self._calculate_completeness(pdca)
        quality = self._calculate_quality(pdca)
        complexity = self._calculate_complexity_coeff(llm_result)
        flow_depth = self._calculate_flow_depth(llm_result.get("flow", {}))

        ewci = self._calculate_ewci(0.8, 1, quality, complexity)
        is_candidate = self._is_closure_candidate(pdca)

        return {
            "goal_alignment": llm_result.get("goal", {}),
            "pdca": pdca,
            "completeness": completeness,
            "ewci": ewci,
            "quality": quality,
            "complexity": complexity,
            "flow_depth": flow_depth,
            "is_closure_candidate": is_candidate,
            "double_loop": pdca.get("double_loop", False),
            "cognition": llm_result.get("cognition", {}),
            "complexity_score": llm_result.get("complexity_score", 5),
            "value_score": llm_result.get("value_score", 5),
            "time_ratio": llm_result.get("time_ratio", 1.0),
            "_error": llm_result.get("_error", "")
        }

    def _calculate_completeness(self, pdca: Dict) -> float:
        scores = {"full": 100, "partial": 60, "missing": 20}
        plan = scores.get(pdca.get("plan", {}).get("completeness", "missing"), 20)
        do = scores.get(pdca.get("do", {}).get("completeness", "missing"), 20)
        check = scores.get(pdca.get("check", {}).get("completeness", "missing"), 20)
        adjust = scores.get(pdca.get("adjust", {}).get("completeness", "missing"), 20)
        return plan * 0.2 + do * 0.3 + check * 0.2 + adjust * 0.3

    def _calculate_quality(self, pdca: Dict) -> float:
        stages = ["plan", "do", "check", "adjust"]
        full_count = sum(1 for s in stages if pdca.get(s, {}).get("completeness") == "full")
        return {4: 1.0, 3: 0.9, 2: 0.7, 1: 0.4, 0: 0.0}.get(full_count, 0.0)

    def _calculate_complexity_coeff(self, llm_result: Dict) -> float:
        complexity = llm_result.get("complexity_score", 5)
        value = llm_result.get("value_score", 5)
        time_ratio = llm_result.get("time_ratio", 1.0)
        base = (complexity / 10 * 0.4 + value / 10 * 0.4 + min(time_ratio, 2) / 2 * 0.2)
        if complexity >= 7 and value >= 7:
            return base * 1.2
        elif complexity <= 3 and value <= 3:
            return base * 0.6
        return base * 1.0

    def _calculate_flow_depth(self, flow: Dict) -> float:
        bq = flow.get("base_quality", {})
        sg = flow.get("signal_gain", {})

        base_dims = ["logic_depth", "orderliness", "progression", "judgment_vector", "goal_alignment"]
        base_scores = [bq.get(d, {}).get("score", 0) for d in base_dims]
        base_quality = sum(base_scores) / 15

        signals = ["rebellion", "persistent_questioning", "self_correction", "time_depth", "meta_cognition"]
        signal_scores = [sg.get(s, {}).get("score", 0) for s in signals]
        signal_raw = sum(signal_scores) / 15

        gain_coeff = 1.0 + signal_raw * 0.6

        rebellion = sg.get("rebellion", {}).get("score", 0)
        if rebellion == 3:
            gain_coeff += 0.2

        return min(base_quality * gain_coeff, 1.0) * 100

    def _calculate_ewci(self, efficiency: float, count: int, quality: float, complexity: float) -> float:
        import math
        count_factor = 1 + math.log(1 + min(count, 10)) / 3
        return efficiency * count_factor * quality * complexity * 100

    def _is_closure_candidate(self, pdca: Dict) -> bool:
        stages = ["plan", "do", "check", "adjust"]
        detected = all(pdca.get(s, {}).get("detected", False) for s in stages)
        full_count = sum(1 for s in stages if pdca.get(s, {}).get("completeness") == "full")
        return detected and full_count >= 2