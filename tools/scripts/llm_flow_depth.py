import sqlite3
import json
import math
from datetime import datetime
from typing import Dict, List, Optional

try:
    from src.openclaw_flow_plugin.core.llm_manager import LLMManager
except ImportError:
    import sys
    sys.path.insert(0, '/Users/duguowei/Desktop/skill相关文档/openclaw_flow_plugin')
    from src.openclaw_flow_plugin.core.llm_manager import LLMManager


class LLMFlowDepthCalculator:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.llm = LLMManager(provider="minimax")

    def get_user_sessions(self) -> List[str]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT session_id
            FROM sessions
            WHERE role = 'user'
        ''')
        sessions = [row[0] for row in cursor.fetchall()]
        conn.close()

        user_sessions = []
        for session_id in sessions:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT content_text FROM sessions
                WHERE session_id = ? AND role = 'user' LIMIT 1
            ''', (session_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                content = row[0] or ''
                if not self._is_cron_session(content):
                    user_sessions.append(session_id)

        return user_sessions

    def _is_cron_session(self, content: str) -> bool:
        cron_keywords = ['cron', 'FlowGuard', '定时任务', '健康检查', 'registry.json']
        return any(kw.lower() in content.lower() for kw in cron_keywords)

    def get_session_messages(self, session_id: str) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT role, content_text, timestamp
            FROM sessions
            WHERE session_id = ?
            ORDER BY timestamp
        ''', (session_id,))
        rows = cursor.fetchall()
        conn.close()

        messages = []
        for role, content, timestamp in rows:
            try:
                ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                ts = datetime.now()
            messages.append({
                'role': role,
                'content': content or '',
                'timestamp': ts
            })
        return messages

    def analyze_quality_with_llm(self, content: str) -> Dict:
        prompt = f"""评估以下对话内容的质量，按0-3分评分（只输出数字）：

对话：
{content[:500]}

评估维度（每个维度0-3分）：
1. 逻辑深度：推理链条长度和严密程度
2. 有序度：内容层次和结构清晰度
3. 递进性：内容是否逐步深入
4. 判断向量：方向明确性（肯定/否定/摇摆）
5. 目标契合度：是否围绕明确目标

输出格式（严格JSON）：
{{"logic_depth":X,"orderliness":X,"progressiveness":X,"judgment_vector":X,"goal_alignment":X}}

只输出JSON，不要其他文字。"""

        response = self.llm.generate(prompt, max_tokens=200)

        try:
            cleaned = response.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.startswith('```'):
                cleaned = cleaned[3:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]

            result = json.loads(cleaned.strip())

            dimensions = ['logic_depth', 'orderliness', 'progressiveness', 'judgment_vector', 'goal_alignment']
            for dim in dimensions:
                if dim in result:
                    result[dim] = max(0, min(3, int(result[dim])))

            return result
        except:
            return {
                'logic_depth': 1,
                'orderliness': 1,
                'progressiveness': 1,
                'judgment_vector': 1,
                'goal_alignment': 1
            }

    def analyze_signal_gain_with_llm(self, content: str) -> Dict:
        prompt = f"""评估以下对话的信号特征，按0-3分评分：

对话：
{content[:500]}

评估维度（每个维度0-3分）：
1. 反叛系数：对AI观点的批判性（0=完全接受，3=明确否定并导向更优方案）
2. 持续追问：探索式追问程度（0=无追问，3=追问直到彻底理解）
3. 主动纠正：自我修正频率（0=从不纠正，3=纠正AI并反思为何AI错）
4. 时间深度：专注时长（0=<1分钟，3=>30分钟）
5. Meta认知：反思方法论程度（0=无反思，3=持续元认知监控）

输出格式（严格JSON）：
{{"rebel":X,"questioning":X,"correction":X,"time_depth":X,"meta_cognition":X}}

只输出JSON，不要其他文字。"""

        response = self.llm.generate(prompt, max_tokens=200)

        try:
            cleaned = response.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.startswith('```'):
                cleaned = cleaned[3:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]

            result = json.loads(cleaned.strip())

            dimensions = ['rebel', 'questioning', 'correction', 'time_depth', 'meta_cognition']
            for dim in dimensions:
                if dim in result:
                    result[dim] = max(0, min(3, int(result[dim])))

            return result
        except:
            return {
                'rebel': 1,
                'questioning': 1,
                'correction': 1,
                'time_depth': 1,
                'meta_cognition': 1
            }

    def calculate_flow_depth(self, session_id: str) -> Dict:
        messages = self.get_session_messages(session_id)
        if not messages:
            return {'session_id': session_id, 'error': 'No messages'}

        user_messages = [m for m in messages if m['role'] == 'user']
        if not user_messages:
            return {'session_id': session_id, 'error': 'No user messages'}

        if len(user_messages) > 1:
            first_time = user_messages[0]['timestamp']
            last_time = user_messages[-1]['timestamp']
            duration_min = (last_time - first_time).total_seconds() / 60
        else:
            duration_min = 5.0

        all_content = '\n'.join([m['content'] for m in user_messages])

        quality = self.analyze_quality_with_llm(all_content)
        signal = self.analyze_signal_gain_with_llm(all_content)

        base_quality = (
            quality['logic_depth'] +
            quality['orderliness'] +
            quality['progressiveness'] +
            quality['judgment_vector'] +
            quality['goal_alignment']
        ) / 15

        signal_raw = (
            signal['rebel'] +
            signal['questioning'] +
            signal['correction'] +
            signal['time_depth'] +
            signal['meta_cognition']
        ) / 15

        signal_gain = 1.0 + signal_raw * 0.6
        if signal['rebel'] == 3:
            signal_gain += 0.2
        signal_gain = min(signal_gain, 1.8)

        fragment_index = min(base_quality * signal_gain, 1.0)

        if duration_min <= 0:
            time_coefficient = 0.0
        else:
            max_minutes = 180
            time_coefficient = min(
                math.log(1 + duration_min / 5) / math.log(1 + max_minutes / 5),
                1.0
            )

        flow_depth = fragment_index * time_coefficient

        return {
            'session_id': session_id,
            'flow_depth': flow_depth,
            'quality': quality,
            'signal': signal,
            'base_quality': base_quality,
            'signal_gain': signal_gain,
            'time_coefficient': time_coefficient,
            'duration_min': duration_min,
            'message_count': len(user_messages)
        }

    def batch_calculate(self, limit: int = 10) -> List[Dict]:
        sessions = self.get_user_sessions()[:limit]
        results = []

        for i, session_id in enumerate(sessions, 1):
            print(f'分析会话 {i}/{len(sessions)}...')
            result = self.calculate_flow_depth(session_id)
            results.append(result)

        return results


def main():
    db_path = '/Users/duguowei/Desktop/skill相关文档/openclaw_flow_plugin/flow_ecosystem.db'
    calculator = LLMFlowDepthCalculator(db_path)

    print('='*70)
    print('LLM语义分析 - 心流深度计算（PRD完整算法）')
    print('='*70)
    print()

    sessions = calculator.get_user_sessions()
    print(f'用户会话数: {len(sessions)}')
    print(f'将分析前10个会话...')
    print()

    results = calculator.batch_calculate(limit=10)

    valid_results = [r for r in results if 'error' not in r]
    flow_depths = [r['flow_depth'] for r in valid_results]

    print()
    print('='*70)
    print('计算结果汇总')
    print('='*70)
    print(f'分析会话数: {len(valid_results)}')
    print(f'平均心流深度: {sum(flow_depths)/len(flow_depths)*100:.1f}%')
    print(f'最高心流深度: {max(flow_depths)*100:.1f}%')
    print(f'最低心流深度: {min(flow_depths)*100:.1f}%')
    print()

    print('心流等级分布:')
    levels = {'high': 0, 'medium': 0, 'low': 0, 'critical': 0}
    for r in valid_results:
        d = r['flow_depth']
        if d >= 0.75:
            levels['high'] += 1
        elif d >= 0.5:
            levels['medium'] += 1
        elif d >= 0.25:
            levels['low'] += 1
        else:
            levels['critical'] += 1

    for level, count in levels.items():
        print(f'  {level}: {count} ({count/len(valid_results)*100:.1f}%)')

    print()
    print('='*70)
    print('详细数据')
    print('='*70)

    for r in sorted(valid_results, key=lambda x: -x['flow_depth'])[:5]:
        print(f"会话: {r['session_id'][:30]}...")
        print(f"  心流深度: {r['flow_depth']*100:.1f}%")
        print(f"  基础质量分: {r['base_quality']*100:.1f}%")
        print(f"  信号增益: {r['signal_gain']:.2f}")
        print(f"  时间系数: {r['time_coefficient']*100:.1f}%")
        print(f"  逻辑深度: {r['quality']['logic_depth']}/3")
        print(f"  有序度: {r['quality']['orderliness']}/3")
        print(f"  递进性: {r['quality']['progressiveness']}/3")
        print(f"  判断向量: {r['quality']['judgment_vector']}/3")
        print(f"  目标契合度: {r['quality']['goal_alignment']}/3")
        print()


if __name__ == '__main__':
    main()