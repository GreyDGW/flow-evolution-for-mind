import json
from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class LLMClient(ABC):
    @abstractmethod
    def analyze_session(self, messages: List[Dict], active_goals: Optional[List[Dict]] = None) -> Dict:
        pass


class OpenClawLLMClient(LLMClient):
    PROMPT_TEMPLATE = """基于对话和活跃目标，输出严格JSON。

活跃目标：
{active_goals}

对话：
{conversation}

评估（每项0-3分，带evidence原文引用）：
1. goal: drift_score(0-1), is_drifting(bool), goal_progress(0-100), evidence
2. pdca: plan/do/check/adjust各{{detected(bool), completeness(full/partial/missing), evidence}}, double_loop(bool)
3. flow.base_quality: logic_depth/orderliness/progression/judgment_vector/goal_alignment各{{score, evidence}}
4. flow.signal_gain: rebellion/persistent_questioning/self_correction/time_depth/meta_cognition各{{score, evidence}}
5. cognition: concept_density/causal_depth/self_correction_freq/cross_domain_links各{{score, evidence}}
6. meta: complexity_score(1-10), value_score(1-10), time_ratio(0.5-2.0)

JSON结构：
{{
  "goal": {{"drift_score": 0.0, "is_drifting": false, "goal_progress": 0, "evidence": ""}},
  "pdca": {{
    "plan": {{"detected": false, "completeness": "missing", "evidence": ""}},
    "do": {{"detected": false, "completeness": "missing", "evidence": ""}},
    "check": {{"detected": false, "completeness": "missing", "evidence": ""}},
    "adjust": {{"detected": false, "completeness": "missing", "evidence": ""}},
    "double_loop": false
  }},
  "flow": {{
    "base_quality": {{
      "logic_depth": {{"score": 0, "evidence": ""}},
      "orderliness": {{"score": 0, "evidence": ""}},
      "progression": {{"score": 0, "evidence": ""}},
      "judgment_vector": {{"score": 0, "evidence": ""}},
      "goal_alignment": {{"score": 0, "evidence": ""}}
    }},
    "signal_gain": {{
      "rebellion": {{"score": 0, "evidence": ""}},
      "persistent_questioning": {{"score": 0, "evidence": ""}},
      "self_correction": {{"score": 0, "evidence": ""}},
      "time_depth": {{"score": 0, "evidence": ""}},
      "meta_cognition": {{"score": 0, "evidence": ""}}
    }}
  }},
  "cognition": {{
    "concept_density": {{"score": 0, "evidence": ""}},
    "causal_depth": {{"score": 0, "evidence": ""}},
    "self_correction_freq": {{"score": 0, "evidence": ""}},
    "cross_domain_links": {{"score": 0, "evidence": ""}}
  }},
  "complexity_score": 5,
  "value_score": 5,
  "time_ratio": 1.0
}}

只输出JSON，不要任何解释。"""

    def __init__(self, api_key: str, base_url: str, model: str, timeout: int = 60):
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        except ImportError:
            raise ImportError("pip install openai")
        self.model = model
        self.max_tokens = 2000

    def analyze_session(self, messages: List[Dict], active_goals: Optional[List[Dict]] = None) -> Dict:
        conversation = self._format_messages(messages)

        goals_str = "无活跃目标"
        if active_goals:
            goals_str = "\n".join([
                "- [" + str(g.get('type', '未知')) + "] " + str(g.get('text', '')) + " (状态: " + str(g.get('status', '未知')) + ")"
                for g in active_goals
            ])

        prompt = self.PROMPT_TEMPLATE.format(
            active_goals=goals_str,
            conversation=conversation
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=self.max_tokens,
                temperature=0.2
            )
            raw_json = response.choices[0].message.content
            result = json.loads(raw_json)
            return self._validate_result(result)
        except json.JSONDecodeError as e:
            return self._empty_result(error=f"JSON解析失败: {e}")
        except Exception as e:
            return self._empty_result(error=f"API调用失败: {e}")

    def _format_messages(self, messages):
        if len(messages) <= 8:
            return self._concat_messages(messages)
        head = messages[:3]
        tail = messages[-4:]
        middle = [m for m in messages[3:-4] if m.get("role") == "user"]
        summary = "[中间" + str(len(middle)) + "轮摘要：" + "|".join([m.get('content', '')[:20] for m in middle])
        return self._concat_messages(head) + "\n" + summary + "\n" + self._concat_messages(tail)

    def _concat_messages(self, messages):
        parts = []
        for msg in messages:
            role = "用户" if msg.get("role") == "user" else "AI"
            content = msg.get("content", "")[:500]
            parts.append(role + ": " + content + "\n")
        return "".join(parts)

    def _validate_result(self, result):
        goal = result.get("goal", {})
        goal.setdefault("drift_score", 0.0)
        goal.setdefault("is_drifting", False)
        goal.setdefault("goal_progress", 0)
        goal.setdefault("evidence", "")

        default_stage = {"detected": False, "completeness": "missing", "evidence": ""}
        pdca = result.get("pdca", {})
        for key in ["plan", "do", "check", "adjust"]:
            if key not in pdca or not isinstance(pdca.get(key), dict):
                pdca[key] = default_stage.copy()

        default_signal = {"score": 0, "evidence": ""}
        flow = result.get("flow", {})
        if not isinstance(flow.get("base_quality"), dict):
            flow["base_quality"] = {}
        for key in ["logic_depth", "orderliness", "progression", "judgment_vector", "goal_alignment"]:
            if not isinstance(flow["base_quality"].get(key), dict):
                flow["base_quality"][key] = default_signal.copy()

        if not isinstance(flow.get("signal_gain"), dict):
            flow["signal_gain"] = {}
        for key in ["rebellion", "persistent_questioning", "self_correction", "time_depth", "meta_cognition"]:
            if not isinstance(flow["signal_gain"].get(key), dict):
                flow["signal_gain"][key] = default_signal.copy()

        cognition = result.get("cognition", {})
        for key in ["concept_density", "causal_depth", "self_correction_freq", "cross_domain_links"]:
            if not isinstance(cognition.get(key), dict):
                cognition[key] = default_signal.copy()

        result.setdefault("complexity_score", 5)
        result.setdefault("value_score", 5)
        result.setdefault("time_ratio", 1.0)
        result.setdefault("double_loop", False)

        return result

    def _empty_result(self, error: str = ""):
        default_signal = {"score": 0, "evidence": ""}
        return {
            "goal": {"drift_score": 0.0, "is_drifting": False, "goal_progress": 0, "evidence": ""},
            "pdca": {
                "plan": {"detected": False, "completeness": "missing", "evidence": ""},
                "do": {"detected": False, "completeness": "missing", "evidence": ""},
                "check": {"detected": False, "completeness": "missing", "evidence": ""},
                "adjust": {"detected": False, "completeness": "missing", "evidence": ""},
                "double_loop": False
            },
            "flow": {
                "base_quality": {
                    "logic_depth": default_signal.copy(),
                    "orderliness": default_signal.copy(),
                    "progression": default_signal.copy(),
                    "judgment_vector": default_signal.copy(),
                    "goal_alignment": default_signal.copy()
                },
                "signal_gain": {
                    "rebellion": default_signal.copy(),
                    "persistent_questioning": default_signal.copy(),
                    "self_correction": default_signal.copy(),
                    "time_depth": default_signal.copy(),
                    "meta_cognition": default_signal.copy()
                }
            },
            "cognition": {
                "concept_density": default_signal.copy(),
                "causal_depth": default_signal.copy(),
                "self_correction_freq": default_signal.copy(),
                "cross_domain_links": default_signal.copy()
            },
            "complexity_score": 5,
            "value_score": 5,
            "time_ratio": 1.0,
            "_error": error
        }


class MockLLMClient(LLMClient):
    def analyze_session(self, messages: List[Dict], active_goals: Optional[List[Dict]] = None) -> Dict:
        text = " ".join([m.get("content", "") for m in messages]).lower()

        has_plan = any(k in text for k in ["计划", "目标", "方案", "想", "准备", "优化", "研究"])
        has_do = any(k in text for k in ["完成", "做了", "加了", "写了", "改了", "部署", "实现"])
        has_check = any(k in text for k in ["测试", "验证", "检查", "复盘", "监控", "测了"])
        has_adjust = any(k in text for k in ["调整", "优化", "改进", "修改", "归档", "文档"])

        default_signal = {"score": 1, "evidence": "规则匹配"}

        return {
            "goal": {"drift_score": 0.2, "is_drifting": False, "goal_progress": 50, "evidence": "规则匹配"},
            "pdca": {
                "plan": {"detected": has_plan, "completeness": "full" if has_plan else "missing", "evidence": "规则匹配"},
                "do": {"detected": has_do, "completeness": "full" if has_do else "missing", "evidence": "规则匹配"},
                "check": {"detected": has_check, "completeness": "full" if has_check else "missing", "evidence": "规则匹配"},
                "adjust": {"detected": has_adjust, "completeness": "full" if has_adjust else "missing", "evidence": "规则匹配"},
                "double_loop": False
            },
            "flow": {
                "base_quality": {
                    "logic_depth": default_signal.copy(),
                    "orderliness": default_signal.copy(),
                    "progression": default_signal.copy(),
                    "judgment_vector": default_signal.copy(),
                    "goal_alignment": default_signal.copy()
                },
                "signal_gain": {
                    "rebellion": default_signal.copy(),
                    "persistent_questioning": default_signal.copy(),
                    "self_correction": default_signal.copy(),
                    "time_depth": default_signal.copy(),
                    "meta_cognition": default_signal.copy()
                }
            },
            "cognition": {
                "concept_density": default_signal.copy(),
                "causal_depth": default_signal.copy(),
                "self_correction_freq": default_signal.copy(),
                "cross_domain_links": default_signal.copy()
            },
            "complexity_score": 5,
            "value_score": 5,
            "time_ratio": 1.0
        }