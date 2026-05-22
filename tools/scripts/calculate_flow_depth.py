import sqlite3
import json
import math
from datetime import datetime
from collections import Counter

class FlowDepthCalculator:
    def __init__(self, db_path):
        self.db_path = db_path
    
    def get_session_messages(self, session_id):
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
                'timestamp': datetime.fromisoformat(row[3].replace('Z', '+00:00')) if row[3] else datetime.now()
            })
        return messages
    
    def get_all_sessions(self, limit=37):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT session_id
            FROM sessions
            GROUP BY session_id
            ORDER BY MIN(timestamp) DESC
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows]
    
    def split_fragments(self, messages):
        fragments = []
        current_fragment = []
        prev_time = None
        
        for msg in messages:
            if prev_time:
                gap = (msg['timestamp'] - prev_time).total_seconds()
                if gap > 900:
                    if current_fragment:
                        fragments.append(current_fragment)
                    current_fragment = []
            current_fragment.append(msg)
            prev_time = msg['timestamp']
        
        if current_fragment:
            fragments.append(current_fragment)
        
        return fragments
    
    def analyze_fragment_quality(self, fragment):
        user_messages = [m for m in fragment if m['role'] == 'user']
        if not user_messages:
            return {'total': 0, 'break_count': 0}
        
        content = '\n'.join([m['content'] for m in user_messages])
        
        logic_depth = self._calculate_logic_depth(content)
        orderliness = self._calculate_orderliness(content)
        progressiveness = self._calculate_progressiveness(content, user_messages)
        judgment_vector = self._calculate_judgment_vector(content)
        goal_契合度 = self._calculate_goal_alignment(content)
        
        total = (logic_depth + orderliness + progressiveness + judgment_vector + goal_契合度) / 15
        
        break_count = self._count_breaks(content)
        
        return {
            'logic_depth': logic_depth,
            'orderliness': orderliness,
            'progressiveness': progressiveness,
            'judgment_vector': judgment_vector,
            'goal_alignment': goal_契合度,
            'total': total,
            'break_count': break_count
        }
    
    def _calculate_logic_depth(self, content):
        indicators = ['因为', '所以', '因此', '从而', '首先', '其次', '最后', 
                      '如果', '那么', '假设', '推理', '证明', '推导']
        score = sum(1 for ind in indicators if ind in content)
        return min(score, 3)
    
    def _calculate_orderliness(self, content):
        depth = content.count('。') + content.count('？') + content.count('！')
        if depth == 0:
            return 0
        elif depth <= 2:
            return 1
        elif depth <= 4:
            return 2
        else:
            return 3
    
    def _calculate_progressiveness(self, content, messages):
        keywords = ['接下来', '然后', '继续', '深入', '展开', '进一步', '细化']
        count = sum(1 for kw in keywords if kw in content)
        
        if count >= 3:
            return 3
        elif count >= 1:
            return 2
        else:
            return 1
    
    def _calculate_judgment_vector(self, content):
        positive = ['确定', '明确', '肯定', '同意', '支持']
        negative = ['不确定', '疑问', '怀疑', '犹豫', '思考']
        
        pos_count = sum(1 for p in positive if p in content)
        neg_count = sum(1 for n in negative if n in content)
        
        if pos_count > neg_count:
            return 3
        elif pos_count == neg_count:
            return 2
        else:
            return 1
    
    def _calculate_goal_alignment(self, content):
        goal_keywords = ['目标', '完成', '实现', '达成', '解决', '任务']
        return min(sum(1 for kw in goal_keywords if kw in content), 3)
    
    def _count_breaks(self, content):
        break_indicators = ['等一下', '先这样', '回头再说', '算了', '下次']
        return sum(1 for ind in break_indicators if ind in content)
    
    def calculate_signal_gain(self, fragment):
        user_messages = [m for m in fragment if m['role'] == 'user']
        if not user_messages:
            return 1.0
        
        content = '\n'.join([m['content'] for m in user_messages])
        
        rebel_score = self._calculate_rebel_coefficient(content)
        zhuiwen_score = self._calculate_zhuiwen(content)
        correct_score = self._calculate_correct(content)
        time_depth = self._calculate_time_depth(fragment)
        meta_score = self._calculate_meta_cognition(content)
        
        total = (rebel_score + zhuiwen_score + correct_score + time_depth + meta_score) / 15
        signal_gain = 1.0 + total * 0.6
        
        if rebel_score == 3:
            signal_gain += 0.2
        
        return min(signal_gain, 1.8)
    
    def _calculate_rebel_coefficient(self, content):
        indicators = ['不对', '错误', '不是', '不同意', '应该这样', '我觉得']
        count = sum(1 for ind in indicators if ind in content)
        return min(count, 3)
    
    def _calculate_zhuiwen(self, content):
        question_count = content.count('？') + content.count('吗') + content.count('为什么')
        return min(question_count, 3)
    
    def _calculate_correct(self, content):
        indicators = ['修正', '更正', '应该是', '重新', '改一下']
        return min(sum(1 for ind in indicators if ind in content), 3)
    
    def _calculate_time_depth(self, fragment):
        if len(fragment) < 2:
            return 0
        
        first_time = fragment[0]['timestamp']
        last_time = fragment[-1]['timestamp']
        duration_min = (last_time - first_time).total_seconds() / 60
        
        if duration_min >= 30:
            return 3
        elif duration_min >= 5:
            return 2
        elif duration_min >= 1:
            return 1
        else:
            return 0
    
    def _calculate_meta_cognition(self, content):
        indicators = ['思考', '反思', '总结', '回顾', '分析', '理解']
        return min(sum(1 for ind in indicators if ind in content), 3)
    
    def calculate_time_coefficient(self, total_effective_minutes):
        if total_effective_minutes <= 0:
            return 0.0
        
        max_minutes = 180
        coefficient = math.log(1 + total_effective_minutes / 5) / math.log(1 + max_minutes / 5)
        return min(coefficient, 1.0)
    
    def calculate_flow_depth(self, session_id):
        messages = self.get_session_messages(session_id)
        if not messages:
            return {'session_id': session_id, 'flow_depth': 0.0, 'error': 'No messages'}
        
        fragments = self.split_fragments(messages)
        
        total_effective_minutes = 0
        weighted_quality_sum = 0
        
        for fragment in fragments:
            if not fragment:
                continue
            
            quality = self.analyze_fragment_quality(fragment)
            signal_gain = self.calculate_signal_gain(fragment)
            
            first_time = fragment[0]['timestamp']
            last_time = fragment[-1]['timestamp']
            duration_min = (last_time - first_time).total_seconds() / 60
            
            breaks = quality['break_count']
            adjusted_duration = max(duration_min - breaks * 3, 0)
            total_effective_minutes += adjusted_duration
            
            fragment_index = min(quality['total'] * signal_gain, 1.0)
            weighted_quality_sum += fragment_index * adjusted_duration
        
        if total_effective_minutes > 0:
            weighted_quality = weighted_quality_sum / total_effective_minutes
        else:
            weighted_quality = 0.0
        
        time_coefficient = self.calculate_time_coefficient(total_effective_minutes)
        flow_depth = weighted_quality * time_coefficient
        
        return {
            'session_id': session_id,
            'flow_depth': flow_depth,
            'fragment_count': len(fragments),
            'total_effective_minutes': total_effective_minutes,
            'weighted_quality': weighted_quality,
            'time_coefficient': time_coefficient,
            'message_count': len(messages)
        }
    
    def batch_calculate(self, limit=37):
        sessions = self.get_all_sessions(limit)
        results = []
        
        for session_id in sessions:
            result = self.calculate_flow_depth(session_id)
            results.append(result)
        
        return results

def main():
    calculator = FlowDepthCalculator('/Users/duguowei/Desktop/skill相关文档/openclaw_flow_plugin/flow_ecosystem.db')
    
    print('='*80)
    print('Flow Ecosystem 心流深度计算 - PRD完整算法')
    print('='*80)
    print()
    
    results = calculator.batch_calculate()
    
    valid_results = [r for r in results if 'error' not in r]
    flow_depths = [r['flow_depth'] for r in valid_results]
    
    print('【计算结果汇总】')
    print('-'*60)
    print(f'分析会话数: {len(valid_results)}')
    print(f'平均心流深度: {sum(flow_depths)/len(flow_depths):.2%}')
    print(f'最高心流深度: {max(flow_depths):.2%}')
    print(f'最低心流深度: {min(flow_depths):.2%}')
    print(f'总有效时长: {sum(r["total_effective_minutes"] for r in valid_results):.1f} 分钟')
    print(f'平均片段数: {sum(r["fragment_count"] for r in valid_results)/len(valid_results):.1f}')
    print()
    
    print('【心流等级分布】')
    print('-'*60)
    levels = {'high': 0, 'medium': 0, 'low': 0, 'critical': 0}
    for r in valid_results:
        depth = r['flow_depth']
        if depth >= 0.75:
            levels['high'] += 1
        elif depth >= 0.5:
            levels['medium'] += 1
        elif depth >= 0.25:
            levels['low'] += 1
        else:
            levels['critical'] += 1
    
    for level, count in levels.items():
        print(f'  {level}: {count} ({count/len(valid_results)*100:.1f}%)')
    
    print()
    print('【详细会话数据】')
    print('-'*60)
    for r in valid_results[:10]:
        print(f"会话: {r['session_id'][:20]}...")
        print(f"  心流深度: {r['flow_depth']:.2%}")
        print(f"  有效时长: {r['total_effective_minutes']:.1f} 分钟")
        print(f"  片段数: {r['fragment_count']}")
        print(f"  消息数: {r['message_count']}")
        print()

if __name__ == '__main__':
    main()