import json
import re
import os
from datetime import datetime

class LLMManager:
    def __init__(self, model_name="Kimi-K2.6", base_url="https://api.moonshot.cn/v1"):
        self.model_name = model_name
        self.base_url = base_url
        self.api_key = os.environ.get('KIMI_API_KEY', 'sk-kimi-4p2CofkAUGOicZbS1a2HjivePFXLjAY3tU7xwPoYokrembzNEkSoeqfy56GyJSnp')
        self.use_mock = False if self.api_key and not self.api_key.startswith('your_') else True
    
    def generate(self, prompt, max_tokens=200):
        if self.use_mock:
            return self._mock_generate(prompt)
        
        try:
            import requests
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json={
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "stream": False
                }
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            print(f"LLM API调用失败: {response.status_code} - {response.text}")
            return self._mock_generate(prompt)
        except Exception as e:
            print(f"LLM调用失败，使用模拟模式: {e}")
            return self._mock_generate(prompt)
    
    def _mock_generate(self, prompt):
        if "提取目标" in prompt:
            return self._mock_extract_goals(prompt)
        elif "PDCA" in prompt or "闭环" in prompt:
            return self._mock_analyze_closure(prompt)
        elif "语义关联" in prompt or "相似" in prompt or "相关" in prompt:
            return "1"
        else:
            return "这是模拟响应。当Kimi API可用时，将使用真实模型。"
    
    def _mock_extract_goals(self, prompt):
        goals = []
        time_horizon = []
        
        user_message_match = re.search(r'用户消息：(.+)', prompt, re.DOTALL)
        if not user_message_match:
            return json.dumps({"goals": [], "time_horizon": []})
        
        user_message = user_message_match.group(1)
        user_message = user_message.replace('\n', ' ')
        
        patterns = [
            r'(帮我)(\s+[^\n。！？；]{6,100})',
            r'(我想|我要|我需要)(\s+[^\n。！？；]{6,100})',
            r'(完成|实现|学习|开发|创建|设计)(\s+[^\n。！？；]{6,100})',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, user_message)
            for match in matches:
                if len(match.groups()) >= 2:
                    goal = match.group(2).strip()
                    goal = re.sub(r'[。！？；,，]$', '', goal)
                    if goal and goal not in goals:
                        goals.append(match.group(1) + goal)
                        if any(kw in goal for kw in ['今天', '现在', '立即', '马上']):
                            time_horizon.append('short')
                        elif any(kw in goal for kw in ['本周', '这周', '下周', '项目']):
                            time_horizon.append('medium')
                        else:
                            time_horizon.append('short')
        
        return json.dumps({"goals": goals, "time_horizon": time_horizon})
    
    def _mock_analyze_closure(self, prompt):
        plan_score = 0
        do_score = 0
        check_score = 0
        adjust_score = 0
        
        if "计划" in prompt or "plan" in prompt.lower():
            plan_score = 70
        if "做" in prompt or "执行" in prompt or "do" in prompt.lower():
            do_score = 60
        if "检查" in prompt or "check" in prompt.lower():
            check_score = 50
        if "调整" in prompt or "修正" in prompt or "adjust" in prompt.lower():
            adjust_score = 40
        
        has_closure = sum([plan_score, do_score, check_score, adjust_score]) > 100
        
        result = {
            "has_closure": has_closure,
            "plan_score": plan_score,
            "do_score": do_score,
            "check_score": check_score,
            "adjust_score": adjust_score,
            "analysis": "模拟分析：检测到PDCA循环" if has_closure else "模拟分析：未检测到完整的PDCA循环"
        }
        
        return json.dumps(result)
    
    def extract_goals(self, text):
        if self.use_mock:
            return self._mock_extract_goals_direct(text)
        
        prompt = f"""
        请从以下用户消息中提取目标，以JSON格式输出：
        
        用户消息：{text}
        
        输出格式：
        {{
            "goals": ["目标1", "目标2", ...],
            "time_horizon": ["short", "medium", "long", ...]
        }}
        """
        
        response = self.generate(prompt, max_tokens=300)
        if response:
            try:
                return json.loads(response)
            except:
                goals = [g.strip() for g in response.split('\n') if g.strip()]
                return {"goals": goals, "time_horizon": ["short"] * len(goals)}
        return {"goals": [], "time_horizon": []}
    
    def _mock_extract_goals_direct(self, text):
        goals = []
        time_horizon = []
        
        bangwo_match = re.search(r'帮我(.+)', text)
        if bangwo_match:
            goal = bangwo_match.group(1).strip()
            goal = re.sub(r'[。！？；,，]$', '', goal)
            if len(goal) >= 4:
                goals.append("帮我" + goal)
                time_horizon.append('short')
        
        woxiang_match = re.search(r'我想(.+)', text)
        if woxiang_match:
            goal = woxiang_match.group(1).strip()
            goal = re.sub(r'[。！？；,，]$', '', goal)
            if len(goal) >= 4 and goal not in str(goals):
                goals.append("我想" + goal)
                time_horizon.append('short')
        
        woyao_match = re.search(r'我要(.+)', text)
        if woyao_match:
            goal = woyao_match.group(1).strip()
            goal = re.sub(r'[。！？；,，]$', '', goal)
            if len(goal) >= 4 and goal not in str(goals):
                goals.append("我要" + goal)
                time_horizon.append('short')
        
        woxuyao_match = re.search(r'我需要(.+)', text)
        if woxuyao_match:
            goal = woxuyao_match.group(1).strip()
            goal = re.sub(r'[。！？；,，]$', '', goal)
            if len(goal) >= 4 and goal not in str(goals):
                goals.append("我需要" + goal)
                time_horizon.append('short')
        
        return {"goals": goals, "time_horizon": time_horizon}
    
    def analyze_closure(self, conversation):
        prompt = f"""
        请分析以下对话中的PDCA循环：
        
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
    
    def is_semantically_related(self, text1, text2, threshold=0.7):
        prompt = f"""
        判断以下两段文本是否语义相关。只回答1或0。
        
        文本1：{text1}
        
        文本2：{text2}
        
        输出：1（相关）或0（不相关）
        """
        
        response = self.generate(prompt, max_tokens=10)
        if response:
            try:
                return int(response.strip()) == 1
            except:
                return False
        return False