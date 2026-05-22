import requests
import json
import logging
import re
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMManager:
    def __init__(self, provider="minimax"):
        self.provider = provider
        self.use_mock = False

        if provider == "minimax":
            self.api_key = os.environ.get("MINIMAX_API_KEY", "")
            self.base_url = "https://api.minimax.chat/v1"
            self.model_name = "MiniMax-M2.7"
        elif provider == "openai":
            self.api_key = os.environ.get("OPENAI_API_KEY", "")
            self.base_url = "https://api.openai.com/v1"
            self.model_name = "gpt-4"
        elif provider == "ollama":
            self.base_url = "http://localhost:11434/v1"
            self.model_name = "llama3.2:1b"
            self.use_mock = False
        elif provider == "ark":
            self.api_key = os.environ.get("ARK_API_KEY", "")
            self.base_url = os.environ.get("ARK_API_URL", "https://ark.bytedance.net/api/text/chat")
            self.model_name = os.environ.get("ARK_MODEL", "Kimi-K2.6")
        else:
            self.use_mock = True

    def generate(self, prompt, max_tokens=200):
        if self.use_mock:
            return self._mock_generate(prompt)

        if self.provider == "minimax":
            return self._call_minimax(prompt, max_tokens)
        elif self.provider == "openai":
            return self._call_openai(prompt, max_tokens)
        elif self.provider == "ark":
            return self._call_ark(prompt, max_tokens)

        return self._mock_generate(prompt)

    def _call_minimax(self, prompt, max_tokens):
        if not self.api_key:
            logger.warning("MiniMax API key未设置，使用模拟模式")
            return self._mock_generate(prompt)

        try:
            response = requests.post(
                f"{self.base_url}/text/chatcompletion_v2",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": 0.1
                },
                timeout=60
            )
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data and "choices" in data and data["choices"] and len(data["choices"]) > 0:
                        message = data["choices"][0]["message"]
                        content = message.get("content", "").strip()
                        if not content:
                            content = message.get("reasoning_content", "").strip()
                        return content
                    logger.warning(f"MiniMax API响应格式异常: {str(data)[:200]}")
                except Exception as e:
                    logger.warning(f"MiniMax JSON解析失败: {e}, 响应: {response.text[:200]}")
                return self._mock_generate(prompt)
            logger.error(f"MiniMax API调用失败: {response.status_code}, {response.text[:200]}")
            return self._mock_generate(prompt)
        except Exception as e:
            logger.error(f"MiniMax API调用异常: {e}")
            return self._mock_generate(prompt)

    def _call_openai(self, prompt, max_tokens):
        if not self.api_key:
            logger.warning("OpenAI API key未设置，使用模拟模式")
            return self._mock_generate(prompt)

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": 0.1
                },
                timeout=60
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            logger.error(f"OpenAI API调用失败: {response.status_code}")
            return self._mock_generate(prompt)
        except Exception as e:
            logger.error(f"OpenAI API调用异常: {e}")
            return self._mock_generate(prompt)

    def _call_ark(self, prompt, max_tokens):
        if not self.api_key:
            logger.warning("Ark API key未设置，使用模拟模式")
            return self._mock_generate(prompt)

        try:
            response = requests.post(
                f"{self.base_url}",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": 0.1
                },
                timeout=60
            )
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data and "choices" in data and data["choices"] and len(data["choices"]) > 0:
                        message = data["choices"][0]["message"]
                        content = message.get("content", "").strip()
                        return content
                    logger.warning(f"Ark API响应格式异常: {str(data)[:200]}")
                except Exception as e:
                    logger.warning(f"Ark JSON解析失败: {e}, 响应: {response.text[:200]}")
                return self._mock_generate(prompt)
            logger.error(f"Ark API调用失败: {response.status_code}, {response.text[:200]}")
            return self._mock_generate(prompt)
        except Exception as e:
            logger.error(f"Ark API调用异常: {e}")
            return self._mock_generate(prompt)

    def _mock_generate(self, prompt):
        flow_keywords = ['心流', 'flow', '认知', '目标', '对齐', 'PDCA', '闭环', '专注', '思维']
        session_keywords = ['会话', 'session', '对话', '分析', '对比']

        prompt_lower = prompt.lower()
        has_flow = any(kw in prompt_lower for kw in flow_keywords)
        has_session = any(kw in prompt_lower for kw in session_keywords)

        if has_flow and has_session:
            return json.dumps({
                "overall_intent": "Flow Ecosystem相关分析活动",
                "flow_ecosystem_related": {
                    "is_related": True,
                    "confidence": 0.85,
                    "reason": "对话涉及心流、认知、目标等Flow Ecosystem核心概念",
                    "related_aspects": ["目标", "心流", "认知进化"]
                },
                "goal_extraction": {
                    "has_goals": True,
                    "main_goals": ["分析会话行为", "优化工作流程"],
                    "goal_types": ["short"],
                    "goal_clarity": "清晰"
                },
                "pdca_analysis": {
                    "has_plan": True,
                    "has_do": True,
                    "has_check": True,
                    "has_adjust": False,
                    "closure_completeness": 0.75,
                    "pdca_stages": ["plan", "do", "check"]
                },
                "flow_state": {
                    "flow_depth": 0.65,
                    "flow_quality": "medium",
                    "focus_indicator": "专注",
                    "evidence": "用户正在分析会话数据，表现出较高的专注度"
                },
                "cognitive_evolution": {
                    "has_evolution": True,
                    "evolution_score": 0.6,
                    "evolution_type": "reflective",
                    "evidence": "通过对比分析，用户正在反思和优化工作方式"
                },
                "prd_metrics": {
                    "completion_score": 0.55,
                    "drift_score": 0.35,
                    "goal_alignment": 0.2,
                    "power_score": 0.6,
                    "navigation_score": 0.5
                }
            })

        if "PDCA" in prompt or "闭环" in prompt:
            return json.dumps({
                "has_closure": True,
                "plan_score": 70,
                "do_score": 65,
                "check_score": 60,
                "adjust_score": 55,
                "analysis": "分析完成"
            })

        if "true" in prompt.lower() or "false" in prompt.lower():
            return "true"

        return json.dumps({
            "overall_intent": "日常操作或系统任务",
            "flow_ecosystem_related": {
                "is_related": False,
                "confidence": 0.9,
                "reason": "对话内容与Flow Ecosystem核心概念无直接关联",
                "related_aspects": []
            },
            "goal_extraction": {
                "has_goals": False,
                "main_goals": [],
                "goal_types": [],
                "goal_clarity": "无"
            },
            "pdca_analysis": {
                "has_plan": False,
                "has_do": False,
                "has_check": False,
                "has_adjust": False,
                "closure_completeness": 0.0,
                "pdca_stages": []
            },
            "flow_state": {
                "flow_depth": 0.2,
                "flow_quality": "low",
                "focus_indicator": "分散",
                "evidence": "缺乏专注的Flow状态"
            },
            "cognitive_evolution": {
                "has_evolution": False,
                "evolution_score": 0.1,
                "evolution_type": "none",
                "evidence": "未观察到认知成长迹象"
            },
            "prd_metrics": {
                "completion_score": 0.2,
                "drift_score": 0.7,
                "goal_alignment": -0.6,
                "power_score": 0.3,
                "navigation_score": 0.2
            }
        })

    def extract_goals(self, text):
        prompt = f"""
请从以下用户消息中提取目标，以JSON格式输出：

用户消息：{text}

输出格式：
{{
    "goals": ["目标1", "目标2", ...],
    "time_horizon": ["short", "medium", "long", ...]
}}

注意：
- 只提取用户明确或隐含的目标
- short表示短期（几天内），medium表示中期（几周），long表示长期（数月以上）
- 如果无法提取目标，返回空列表
"""

        response = self.generate(prompt, max_tokens=300)
        if response:
            try:
                return json.loads(response)
            except:
                goals = [g.strip() for g in response.split('\n') if g.strip() and not g.startswith('{')]
                return {"goals": goals, "time_horizon": ["short"] * len(goals)}
        return {"goals": [], "time_horizon": []}

    def analyze_closure(self, conversation):
        prompt = f"""
请分析以下对话中的PDCA（Plan-Do-Check-Adjust）循环：

对话：{conversation}

输出格式：
{{
    "has_closure": true/false,
    "plan_score": 0-100,
    "do_score": 0-100,
    "check_score": 0-100,
    "adjust_score": 0-100,
    "analysis": "简要分析"
}}
"""

        response = self.generate(prompt, max_tokens=300)
        if response:
            try:
                return json.loads(response)
            except:
                return {"has_closure": False, "plan_score": 0, "do_score": 0, "check_score": 0, "adjust_score": 0, "analysis": response}
        return {"has_closure": False, "plan_score": 0, "do_score": 0, "check_score": 0, "adjust_score": 0, "analysis": ""}

    def analyze_sentiment(self, text):
        prompt = f"""
请分析以下文本的情感倾向：

文本：{text}

输出格式：
{{
    "sentiment": "positive"/"negative"/"neutral",
    "confidence": 0.0-1.0,
    "reason": "简要说明"
}}
"""

        response = self.generate(prompt, max_tokens=200)
        if response:
            try:
                return json.loads(response)
            except:
                return {"sentiment": "neutral", "confidence": 0.5, "reason": response}
        return {"sentiment": "neutral", "confidence": 0.5, "reason": ""}

    def is_valid_goal(self, text):
        if self.use_mock:
            return self._mock_is_valid_goal(text)

        prompt = f"""
判断以下文本是否是有效的用户目标或意图（可以是用户想要完成的事情、想了解的知识、想问的问题）：

文本：{text}

判断标准：
- 如果是用户想要完成的任务/动作，返回 true
- 如果是用户想要了解/知道的信息，返回 true
- 如果只是用户的自言自语、问候、简单确认，返回 false

只需输出 true 或 false
"""

        response = self.generate(prompt, max_tokens=10)
        if response:
            return 'true' in response.lower()
        return False

    def is_goal_aligned(self, text):
        if self.use_mock:
            return self._mock_is_goal_aligned(text)

        prompt = f"""
判断以下用户目标是否与Flow Ecosystem（认知共生进化系统）核心主题相关：

Flow Ecosystem核心主题：
- 认知进化、心流状态、目标对齐度
- PDCA闭环、目标追踪、专注度分析
- 个人进化系统、Flow生态系统

用户目标：{text}

判断标准：
- 如果目标与上述核心主题直接相关（认知、心流、目标、进化、PDCA、分析报告等），返回 true
- 如果目标只是普通的操作请求（打开文档、切换模式、搜索等）与Flow Ecosystem无关，返回 false

只需输出 true 或 false
"""

        response = self.generate(prompt, max_tokens=10)
        if response:
            return 'true' in response.lower()
        return False

    def _mock_is_goal_aligned(self, text):
        flow_keywords = [
            "心流", "flow", "认知", "进化", "目标", "对齐",
            "PDCA", "闭环", "专注", "分析报告", "思维混乱",
            "智能体", "agent", "对话", "session", "conversation"
        ]
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in flow_keywords)

    def _mock_is_valid_goal(self, text):
        if not text:
            return False

        invalid_patterns = [
            r'^.{1,4}$',
            r'^[一二三四五六七八九十0-9]$',
            r'^\{.*\}$',
            r'^```',
        ]

        for pattern in invalid_patterns:
            if re.match(pattern, text.strip()):
                return False

        valid_patterns = [
            '帮我', '我想', '我要', '完成', '创建', '学习', '修改',
            '实现', '解决', '开发', '分析', '设计', '优化', '检查',
            '验证', '测试', '研究', '了解', '理解', '搞懂'
        ]

        if any(pattern in text for pattern in valid_patterns):
            return True

        return len(text.strip()) > 10