import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional

try:
    from .llm_manager import LLMManager
except ImportError:
    from llm_manager import LLMManager


class LLMDrivenSessionAnalyzer:
    def __init__(self, db_path: str = 'flow_ecosystem.db'):
        self.db_path = db_path
        self.llm = LLMManager(provider="minimax")

    def get_sessions(self, limit: int = 10) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, session_id, role, content_text, timestamp
            FROM sessions
            WHERE role = 'user'
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        conn.close()

        sessions = []
        for row in rows:
            sessions.append({
                'id': row[0],
                'session_id': row[1],
                'role': row[2],
                'content_text': row[3],
                'timestamp': row[4]
            })
        return sessions

    def get_session_messages(self, session_id: int) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, role, content_text, timestamp
            FROM sessions
            WHERE session_id = ?
            ORDER BY timestamp
        ''', (session_id,))
        rows = cursor.fetchall()
        conn.close()

        messages = []
        for row in rows:
            messages.append({
                'id': row[0],
                'role': row[1],
                'content': row[2],
                'timestamp': row[3]
            })
        return messages

    def analyze_with_llm(self, session_id: int) -> Dict:
        messages = self.get_session_messages(session_id)
        if not messages:
            return {'error': 'Session not found'}

        conversation_text = '\n'.join([
            f"[{msg['role']}] {msg['content']}" for msg in messages
        ])

        prompt = f"""
分析以下对话，输出JSON格式结果：

对话内容：
{conversation_text}

输出格式要求：
- 只输出JSON，不要输出其他任何文字
- 严格按照以下JSON结构输出

{{
    "session_id": "{session_id}",
    "overall_intent": "会话总体意图",
    "flow_ecosystem_related": {{
        "is_related": true,
        "confidence": 0.85,
        "reason": "判断理由",
        "related_aspects": ["目标", "心流"]
    }},
    "goal_extraction": {{
        "has_goals": true,
        "main_goals": ["目标1", "目标2"],
        "goal_types": ["short"],
        "goal_clarity": "清晰"
    }},
    "pdca_analysis": {{
        "has_plan": true,
        "has_do": true,
        "has_check": true,
        "has_adjust": false,
        "closure_completeness": 0.75,
        "pdca_stages": ["plan", "do", "check"]
    }},
    "flow_state": {{
        "flow_depth": 0.65,
        "flow_quality": "medium",
        "focus_indicator": "专注",
        "evidence": "依据"
    }},
    "cognitive_evolution": {{
        "has_evolution": true,
        "evolution_score": 0.6,
        "evolution_type": "reflective",
        "evidence": "依据"
    }},
    "prd_metrics": {{
        "completion_score": 0.55,
        "drift_score": 0.35,
        "goal_alignment": 0.2,
        "power_score": 0.6,
        "navigation_score": 0.5
    }}
}}
"""

        response = self.llm.generate(prompt, max_tokens=1500)

        try:
            cleaned_response = response.strip()
            
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            
            cleaned_response = cleaned_response.strip()
            
            if 'The user asks:' in cleaned_response or 'The user says:' in cleaned_response:
                import re
                json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
                if json_match:
                    cleaned_response = json_match.group(0)
            
            try:
                result = json.loads(cleaned_response)
            except:
                cleaned_response = cleaned_response.replace('\r\n', '\n').replace('\r', '\n')
                lines = cleaned_response.split('\n')
                cleaned_lines = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('//'):
                        cleaned_lines.append(line)
                cleaned_response = '\n'.join(cleaned_lines)
                
                try:
                    result = json.loads(cleaned_response)
                except:
                    result = {
                        'error': 'JSON解析失败',
                        'raw_response': response[:500],
                        'session_id': session_id
                    }
        except Exception as e:
            result = {
                'error': 'JSON解析失败',
                'raw_response': response[:500],
                'session_id': session_id
            }

        return {
            'session_id': session_id,
            'message_count': len(messages),
            'llm_analysis': result,
            'timestamp': datetime.now().isoformat()
        }

    def batch_analyze(self, limit: int = 10) -> List[Dict]:
        sessions = self.get_sessions(limit)
        results = []

        for session in sessions:
            session_id = session['session_id']
            print(f"分析会话 {session_id}...")
            analysis = self.analyze_with_llm(session_id)
            results.append(analysis)

        return results

    def calculate_prd_index(self, llm_analysis: Dict) -> Dict:
        prd = llm_analysis.get('llm_analysis', {}).get('prd_metrics', {})

        completion = prd.get('completion_score', 0.3)
        drift = prd.get('drift_score', 0.5)
        goal_alignment = prd.get('goal_alignment', -0.5)
        power = prd.get('power_score', 0.5)
        navigation = prd.get('navigation_score', 0.3)

        exploration_exemption = 0.8
        if prd.get('completion_score', 0) > 0.6:
            exploration_exemption = 0.5
        elif prd.get('completion_score', 0) < 0.3:
            exploration_exemption = 1.0

        adjusted_alignment = goal_alignment * exploration_exemption
        adjusted_alignment = max(-1.0, min(1.0, adjusted_alignment))

        comprehensive_index = power * max(adjusted_alignment, 0.05)

        return {
            'completion_score': completion,
            'drift_score': drift,
            'goal_alignment': adjusted_alignment,
            'goal_alignment_percent': (adjusted_alignment + 1) * 50,
            'power_score': power,
            'navigation_score': navigation,
            'comprehensive_index': comprehensive_index,
            'strategic_status': self._get_strategic_status(adjusted_alignment)
        }

    def _get_strategic_status(self, alignment: float) -> str:
        if alignment > 0.5:
            return "🎯 卓越"
        elif alignment > 0:
            return "✅ 达成"
        elif alignment > -0.5:
            return "⚠️ 偏离"
        else:
            return "❌ 失效"


def main():
    print("=" * 70)
    print("LLM驱动的会话分析器 - 纯语义理解版本")
    print("=" * 70)
    print()

    analyzer = LLMDrivenSessionAnalyzer()

    print("获取最近会话...")
    sessions = analyzer.get_sessions(5)
    print(f"获取到 {len(sessions)} 个会话")
    print()

    print("=" * 70)
    print("使用LLM进行深度分析")
    print("=" * 70)

    for i, session in enumerate(sessions, 1):
        print(f"\n{'='*70}")
        print(f"会话 {i}: {session['session_id'][:20]}...")
        print(f"预览: {session['content_text'][:60]}...")
        print()

        analysis = analyzer.analyze_with_llm(session['session_id'])

        if 'error' in analysis.get('llm_analysis', {}):
            print(f"错误: {analysis['llm_analysis']['error']}")
            if 'raw_response' in analysis.get('llm_analysis', {}):
                print(f"原始响应: {analysis['llm_analysis']['raw_response'][:200]}...")
            continue

        llm = analysis.get('llm_analysis', {})

        print("【LLM分析结果】")
        print(f"  总体意图: {llm.get('overall_intent', 'N/A')}")
        print()

        flow_rel = llm.get('flow_ecosystem_related', {})
        print(f"【Flow Ecosystem相关】")
        print(f"  相关: {flow_rel.get('is_related', False)}")
        print(f"  置信度: {flow_rel.get('confidence', 0):.0%}")
        print(f"  理由: {flow_rel.get('reason', 'N/A')}")
        print(f"  相关方面: {', '.join(flow_rel.get('related_aspects', []))}")
        print()

        goals = llm.get('goal_extraction', {})
        print(f"【目标提取】")
        print(f"  有目标: {goals.get('has_goals', False)}")
        print(f"  主要目标: {goals.get('main_goals', [])}")
        print(f"  目标类型: {', '.join(goals.get('goal_types', []))}")
        print(f"  清晰度: {goals.get('goal_clarity', 'N/A')}")
        print()

        pdca = llm.get('pdca_analysis', {})
        print(f"【PDCA闭环分析】")
        print(f"  Plan: {pdca.get('has_plan', False)}")
        print(f"  Do: {pdca.get('has_do', False)}")
        print(f"  Check: {pdca.get('has_check', False)}")
        print(f"  Adjust: {pdca.get('has_adjust', False)}")
        print(f"  闭环完整度: {pdca.get('closure_completeness', 0):.0%}")
        print(f"  阶段: {', '.join(pdca.get('pdca_stages', []))}")
        print()

        flow = llm.get('flow_state', {})
        print(f"【心流状态】")
        print(f"  心流深度: {flow.get('flow_depth', 0):.0%}")
        print(f"  心流质量: {flow.get('flow_quality', 'N/A')}")
        print(f"  专注指示: {flow.get('focus_indicator', 'N/A')}")
        print()

        cog = llm.get('cognitive_evolution', {})
        print(f"【认知进化】")
        print(f"  有进化: {cog.get('has_evolution', False)}")
        print(f"  进化分数: {cog.get('evolution_score', 0):.0%}")
        print(f"  进化类型: {cog.get('evolution_type', 'N/A')}")
        print()

        prd_idx = analyzer.calculate_prd_index(analysis)
        print(f"【PRD综合指数】")
        print(f"  完成度: {prd_idx['completion_score']:.0%}")
        print(f"  漂移分数: {prd_idx['drift_score']:.0%}")
        print(f"  目标对齐度: {prd_idx['goal_alignment']:.2f} ({prd_idx['goal_alignment_percent']:.1f}%)")
        print(f"  动力分数: {prd_idx['power_score']:.0%}")
        print(f"  导航分数: {prd_idx['navigation_score']:.0%}")
        print(f"  综合指数: {prd_idx['comprehensive_index']:.2f}")
        print(f"  战略状态: {prd_idx['strategic_status']}")


if __name__ == '__main__':
    main()
