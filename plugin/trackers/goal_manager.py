import sqlite3
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class Goal:
    def __init__(self, id: int = None, declared_text: str = '', declared_at: str = None,
                 status: str = 'active', time_horizon: str = 'short',
                 drift_score: float = 0.3, completion_score: float = 0.3):
        self.id = id
        self.declared_text = declared_text
        self.declared_at = declared_at or datetime.now().isoformat()
        self.status = status
        self.time_horizon = time_horizon
        self.drift_score = drift_score
        self.completion_score = completion_score


class GoalManager:
    def __init__(self, db_path: str = 'flow_ecosystem.db', memory_path: str = None):
        self.db_path = db_path
        if memory_path is None:
            self.memory_path = '/Users/duguowei/.openclaw/workspace/MEMORY.md'
        else:
            self.memory_path = memory_path

    def read_goals_from_memory(self) -> List[Dict]:
        goals = []
        try:
            with open(self.memory_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            match = re.search(r'## 当前项目（优先级排序）\n([\s\S]*?)(?=\n## 多角色工作系统|\Z)', content)
            if match:
                projects_section = match.group(1)
                lines = projects_section.strip().split('\n')
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('###'):
                        title = line[3:].strip()
                        if title.startswith('项目') or '核心项目' in title:
                            status = 'active'
                            horizon = 'long'
                            drift_score = 0.3
                            
                            if '核心项目' in title:
                                drift_score = 0.1
                                horizon = 'long'
                            elif '次要' in title:
                                drift_score = 0.4
                                horizon = 'medium'
                            elif '暂停' in title:
                                status = 'stalled'
                                drift_score = 0.7
                                horizon = 'medium'
                            elif '运行中' in title:
                                status = 'active'
                                drift_score = 0.2
                            
                            goals.append({
                                'text': title,
                                'status': status,
                                'time_horizon': horizon,
                                'drift_score': drift_score
                            })
            
            match = re.search(r'目标：(.+)', content)
            if match:
                personal_goal = match.group(1).strip()
                goals.append({
                    'text': personal_goal,
                    'status': 'active',
                    'time_horizon': 'long',
                    'drift_score': 0.2
                })
                
        except Exception as e:
            print(f'读取 memory.md 失败: {e}')
        
        return goals

    def sync_goals_from_memory(self):
        memory_goals = self.read_goals_from_memory()
        if not memory_goals:
            return 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        added_count = 0
        for goal in memory_goals:
            cursor.execute('''
                SELECT id FROM goals WHERE declared_text = ?
            ''', (goal['text'],))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO goals (declared_text, declared_at, status, time_horizon, drift_score, completion_score)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    goal['text'],
                    datetime.now().isoformat(),
                    goal['status'],
                    goal['time_horizon'],
                    goal['drift_score'],
                    self._estimate_completion_from_status(goal['status'])
                ))
                added_count += 1
        
        conn.commit()
        conn.close()
        return added_count

    def _estimate_completion_from_status(self, status: str) -> float:
        status_map = {
            '完成': 1.0,
            'completed': 1.0,
            '推进中': 0.5,
            '稳步推进': 0.6,
            '停滞': 0.1,
            '停滞3天': 0.1,
            'active': 0.3,
        }
        return status_map.get(status, 0.3)

    def calculate_completion_score(self, goal_id: int) -> float:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT status, declared_at, closed_at, time_horizon, drift_score
            FROM goals WHERE id = ?
        ''', (goal_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return 0.0

        status, declared_at, closed_at, time_horizon, drift_score = row
        
        score = self._calculate_status_score(status, declared_at, closed_at)
        
        conn.close()
        return score

    def _calculate_status_score(self, status: str, declared_at: str, closed_at: str) -> float:
        if status == 'completed':
            return 1.0
        elif status == 'closed':
            return 0.5
        elif status == 'active':
            return self._estimate_progress(declared_at)
        elif status == 'stagnant':
            return 0.1
        elif status == 'abandoned':
            return 0.0
        else:
            return 0.2

    def _estimate_progress(self, declared_at: str) -> float:
        try:
            declared = datetime.fromisoformat(declared_at.replace('Z', '+00:00'))
            now = datetime.now()
            age_days = (now - declared).days
            
            if age_days < 1:
                return 0.25
            elif age_days < 3:
                return 0.4
            elif age_days < 7:
                return 0.5
            elif age_days < 14:
                return 0.3
            else:
                return 0.1
        except:
            return 0.25

    def calculate_overall_completion(self) -> Dict[str, float]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT time_horizon, completion_score
            FROM goals 
            WHERE completion_score IS NOT NULL
        ''')
        rows = cursor.fetchall()

        short_scores = []
        medium_scores = []
        long_scores = []

        for time_horizon, score in rows:
            if time_horizon == 'short':
                short_scores.append(score)
            elif time_horizon == 'medium':
                medium_scores.append(score)
            elif time_horizon == 'long':
                long_scores.append(score)

        short_avg = sum(short_scores) / len(short_scores) if short_scores else 0.5
        medium_avg = sum(medium_scores) / len(medium_scores) if medium_scores else 0.5
        long_avg = sum(long_scores) / len(long_scores) if long_scores else 0.5

        overall = short_avg * 0.3 + medium_avg * 0.3 + long_avg * 0.4

        conn.close()

        return {
            'short_term': short_avg,
            'medium_term': medium_avg,
            'long_term': long_avg,
            'overall': overall
        }

    def update_all_completion_scores(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM goals')
        goal_ids = [row[0] for row in cursor.fetchall()]

        updated_count = 0
        for goal_id in goal_ids:
            score = self.calculate_completion_score(goal_id)
            cursor.execute('''
                UPDATE goals SET completion_score = ? WHERE id = ?
            ''', (score, goal_id))
            updated_count += 1

        conn.commit()
        conn.close()

        return updated_count

    def calculate_drift_score(self, goal_id: int) -> float:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT declared_text, declared_at, time_horizon, status FROM goals WHERE id = ?', (goal_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return 0.3

        goal_text, declared_at, time_horizon, status = row
        
        if status == 'completed':
            conn.close()
            return 0.0
        if status == 'abandoned':
            conn.close()
            return 1.0

        goal_keywords = set([w for w in goal_text.split() if len(w) >= 2])
        if not goal_keywords:
            conn.close()
            return 0.5
        
        cursor.execute('''
            SELECT s.content_text 
            FROM sessions s
            WHERE s.timestamp >= ?
            AND s.role = 'user'
            ORDER BY s.timestamp
            LIMIT 50
        ''', (declared_at,))
        rows = cursor.fetchall()

        if not rows:
            conn.close()
            return 0.3

        relevant_count = 0
        total_count = len(rows)
        threshold = max(1, len(goal_keywords) // 3)

        for row in rows:
            content = row[0] or ''
            content_keywords = set([w for w in content.split() if len(w) >= 2])
            overlap = goal_keywords.intersection(content_keywords)
            if len(overlap) >= threshold:
                relevant_count += 1

        relevance_ratio = relevant_count / total_count if total_count > 0 else 0.5
        
        base_drift = 1 - relevance_ratio
        
        horizon_adjustment = {
            'short': 0.6,
            'medium': 0.8,
            'long': 1.0
        }.get(time_horizon, 0.8)

        adjusted_drift = base_drift * horizon_adjustment

        min_drift = {
            'short': 0.05,
            'medium': 0.1,
            'long': 0.15
        }.get(time_horizon, 0.1)

        exploration_exemption = self._calculate_exploration_exemption(goal_text, rows)
        
        final_drift = max(min_drift, min(0.9, adjusted_drift * exploration_exemption))

        conn.close()
        return final_drift

    def _calculate_exploration_exemption(self, goal_text, session_rows):
        exploration_keywords = [
            '学习', '研究', '了解', '探索', '调研', '分析', 
            '查看', '阅读', '文档', '资料', '知识', '理解'
        ]
        
        goal_lower = goal_text.lower()
        has_exploration = any(kw.lower() in goal_lower for kw in exploration_keywords)
        
        if has_exploration:
            content_text = ' '.join([row[0] or '' for row in session_rows])
            content_lower = content_text.lower()
            
            flow_keywords = ['心流', 'flow', '认知', '目标', '对齐', 'PDCA', '闭环']
            has_flow = any(kw.lower() in content_lower for kw in flow_keywords)
            
            if has_flow:
                return 0.5
            else:
                return 0.7
        else:
            return 1.0

    def update_all_drift_scores(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM goals')
        goal_ids = [row[0] for row in cursor.fetchall()]

        updated_count = 0
        for goal_id in goal_ids:
            drift_score = self.calculate_drift_score(goal_id)
            cursor.execute('''
                UPDATE goals SET drift_score = ? WHERE id = ?
            ''', (drift_score, goal_id))
            updated_count += 1

        conn.commit()
        conn.close()

        return updated_count

    def get_goal_alignment(self) -> float:
        completion = self.calculate_overall_completion()
        overall_completion = completion['overall']

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT AVG(drift_score) FROM goals WHERE drift_score IS NOT NULL')
        avg_drift = cursor.fetchone()[0] or 0.5

        cursor.execute('SELECT COUNT(*) FROM goals WHERE time_horizon = ?', ('long',))
        long_count = cursor.fetchone()[0]
        
        exploration_exemption = 0.8 if long_count > 0 else 1.0
        
        conn.close()

        alignment = (overall_completion * (1 - avg_drift * exploration_exemption) * 2) - 1
        return max(-1.0, min(1.0, alignment))

    def get_goal_alignment_percent(self) -> float:
        alignment = self.get_goal_alignment()
        return (alignment + 1) * 50


if __name__ == '__main__':
    manager = GoalManager()
    
    print('=== 从 memory.md 同步目标 ===')
    memory_goals = manager.read_goals_from_memory()
    print(f'从 memory.md 读取到 {len(memory_goals)} 个目标')
    for goal in memory_goals:
        print(f'  - [{goal["status"]}] {goal["text"]} ({goal["time_horizon"]}, 漂移度: {goal["drift_score"]})')
    
    added = manager.sync_goals_from_memory()
    print(f'\n从 memory.md 同步了 {added} 个新目标')
    
    print('\n=== 更新所有目标完成度分数 ===')
    updated = manager.update_all_completion_scores()
    print(f'已更新 {updated} 个目标')
    
    print('\n=== 更新所有目标漂移分数 ===')
    updated_drift = manager.update_all_drift_scores()
    print(f'已更新 {updated_drift} 个漂移分数')
    
    completion = manager.calculate_overall_completion()
    print('\n=== 目标完成度计算结果 ===')
    print(f'  短期目标达成度: {completion["short_term"]:.2%}')
    print(f'  中期目标达成度: {completion["medium_term"]:.2%}')
    print(f'  长期目标达成度: {completion["long_term"]:.2%}')
    print(f'  综合目标完成度: {completion["overall"]:.2%}')
    
    conn = sqlite3.connect('flow_ecosystem.db')
    cursor = conn.cursor()
    cursor.execute('SELECT MIN(drift_score), AVG(drift_score), MAX(drift_score) FROM goals')
    row = cursor.fetchone()
    print(f'\n=== 漂移分数统计 ===')
    print(f'  最小漂移: {row[0]:.3f}')
    print(f'  平均漂移: {row[1]:.3f}')
    print(f'  最大漂移: {row[2]:.3f}')
    
    cursor.execute('SELECT time_horizon, COUNT(*) FROM goals GROUP BY time_horizon')
    rows = cursor.fetchall()
    print(f'\n=== 目标时间跨度分布 ===')
    for horizon, count in rows:
        print(f'  {horizon}: {count} 个')
    
    conn.close()
    
    alignment = manager.get_goal_alignment()
    alignment_percent = manager.get_goal_alignment_percent()
    print(f'\n=== 目标对齐度 ===')
    print(f'  目标对齐度: {alignment:.2f} ({alignment_percent:.1f}%)')