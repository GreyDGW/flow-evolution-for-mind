import os
from typing import List, Dict
from dotenv import load_dotenv
from plugin.llm_client import DeepSeekLLMClient

load_dotenv()

class BreakthroughWriter:
    def __init__(self):
        try:
            key = os.getenv('LLM_API_KEY') or os.getenv('DEEPSEEK_API_KEY')
            if key:
                self.client = DeepSeekLLMClient(api_key=key)
            else:
                self.client = None
        except:
            self.client = None

    def write(self, tools: List[Dict], portrait: Dict, stuck_points: List[str]) -> Dict:
        if not self.client:
            return self._fallback(portrait, stuck_points)
        try:
            prompt = self._build_prompt(tools, portrait, stuck_points)
            response = self.client.chat(prompt)
            result = self._parse_response(response)
            if not result.get('qualitative'):
                return self._fallback(portrait, stuck_points)
            return result
        except Exception as e:
            print(f"[Writer] {e}")
            return self._fallback(portrait, stuck_points)

    def _build_prompt(self, tools: List[Dict], portrait: Dict, stuck_points: List[str]) -> str:
        lines = []
        label = portrait.get('label') or '未知'
        
        if label == '四维协同':
            lines.append("你是 Flow 系统的进阶教练。用户处于巅峰状态，帮助固化与萃取经验。禁止使用抽象词汇如保持节奏、模式复用，必须包含具体数字和可验证场景。")
            lines.append("标签：" + label)
            desc = portrait.get('description') or ''
            lines.append("描述：" + desc)
            if stuck_points:
                lines.append("卡壳点：" + "、".join(stuck_points[:3]))
        else:
            lines.append("你是 Flow 系统的破局顾问。帮助用户找到突破口。禁止使用抽象词汇如节省时间、提升效率，必须包含具体数字和可验证场景。")
            lines.append("标签：" + label)
            desc = portrait.get('description') or ''
            lines.append("描述：" + desc)
            if stuck_points:
                lines.append("卡壳点：" + "、".join(stuck_points[:3]))
        
        if tools:
            for i, t in enumerate(tools[:2], 1):
                lines.append("工具" + str(i) + "：" + t.get('title', '未知'))
                lines.append("描述：" + t.get('description', '')[:100])
                if t.get('url'):
                    lines.append("来源：" + t['url'].split('/')[2])
        else:
            lines.append("无外部工具推荐，基于画像生成通用建议")
        
        lines.append("输出格式：定性：[一句话] | 收益时间：[具体分钟数] | 收益价值：[具体场景] | 行动1：[15分钟具体动作] | 行动2：[5分钟具体动作]")
        return "\n".join(lines)

    def _parse_response(self, response: str) -> Dict:
        result = {"qualitative": "", "benefit_time": "", "benefit_value": "", "action_max": "", "action_quick": ""}
        
        # 处理 | 分隔的格式
        if '|' in response:
            for part in response.split('|'):
                part = part.strip().replace('*', '').replace('**', '')
                if '定性' in part and '：' in part:
                    result["qualitative"] = part.split('：', 1)[1].strip()
                elif '收益时间' in part and '：' in part:
                    result["benefit_time"] = part.split('：', 1)[1].strip()
                elif '收益价值' in part and '：' in part:
                    result["benefit_value"] = part.split('：', 1)[1].strip()
                elif '行动1' in part and '：' in part:
                    result["action_max"] = part.split('：', 1)[1].strip()
                elif '行动2' in part and '：' in part:
                    result["action_quick"] = part.split('：', 1)[1].strip()
        else:
            # 按行解析
            for line in response.split("\n"):
                line = line.strip().replace("*", "").replace("**", "")
                if "定性" in line and "：" in line:
                    result["qualitative"] = line.split("：", 1)[1].strip()
                elif "收益时间" in line and "：" in line:
                    result["benefit_time"] = line.split("：", 1)[1].strip()
                elif "收益价值" in line and "：" in line:
                    result["benefit_value"] = line.split("：", 1)[1].strip()
                elif "行动1" in line and "：" in line:
                    result["action_max"] = line.split("：", 1)[1].strip()
                elif "行动2" in line and "：" in line:
                    result["action_quick"] = line.split("：", 1)[1].strip()
        
        return result

    def _fallback(self, portrait: Dict, stuck_points: List[str] = None) -> Dict:
        label = portrait.get('label', '未知')
        desc = portrait.get('description', '')

        # 修复：如果有 stuck_points，基于具体卡壳点生成建议
        if stuck_points and len(stuck_points) > 0 and stuck_points[0] != '当前整体状态平稳，无明显卡壳点':
            stuck = stuck_points[0]
            return {
                "qualitative": f"当前状态为{label}——{desc}。具体卡壳点：{stuck}。",
                "benefit_time": f"解决'{stuck}'后，预计每次节省15-20分钟",
                "benefit_value": f"把'{stuck}'变成可复用的检查清单，避免重复踩坑",
                "action_max": f"15分钟：针对'{stuck}'写一个最小可验证动作（如一个TODO或一段伪代码）",
                "action_quick": f"5分钟：在日历中设置一个15分钟的提醒，专门处理'{stuck}'"
            }

        if label == '四维协同':
            return {
                "qualitative": "当前状态极佳，继续保持。建议固化经验。",
                "benefit_time": "固化后每次启动快15分钟",
                "benefit_value": "形成清单，后续不再从头摸索",
                "action_max": "5分钟：记录本次关键决策点",
                "action_quick": "2分钟：设定明天启动节点"
            }

        return {
            "qualitative": f"当前状态为{label}——{desc}。",
            "benefit_time": "锁定下一步节省30分钟摸索",
            "benefit_value": "找到突破口避免空转",
            "action_max": "15分钟：选择一个核心任务并写出第一步",
            "action_quick": "5分钟：列出明天3个优先项"
        }