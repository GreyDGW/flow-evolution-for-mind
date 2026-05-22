#!/usr/bin/env python3
"""测试完整的目标管理系统（含中长期目标）"""

from datetime import datetime
from typing import List, Optional, Tuple, Dict
import re
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Goal(Base):
    __tablename__ = 'goals'
    
    id = Column(Integer, primary_key=True)
    declared_text = Column(Text)
    declared_at = Column(DateTime)
    status = Column(String(32))
    drift_score = Column(Float)
    last_mentioned = Column(DateTime)
    closed_at = Column(DateTime)
    closure_evidence = Column(Text)
    complexity_score = Column(Float)
    time_horizon = Column(String(16))
    completion_score = Column(Float)

class GoalManager:
    def __init__(self, db_path: str = 'flow_ecosystem.db'):
        self.engine = create_engine(f'sqlite:///{db_path}')
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def _classify_time_horizon(self, text: str) -> str:
        text_lower = text.lower()
        short_keywords = ['今天', '今日', '今天完成', '立即', '马上', '现在', '本周内', '短期']
        medium_keywords = ['本周', '这周', '这星期', '下周', '本月', '中期', '项目']
        long_keywords = ['长期', '目标', '愿景', '梦想', '成为', '学会', '掌握', '年度', '人生']
        
        for kw in short_keywords:
            if kw in text_lower:
                return 'short'
        for kw in medium_keywords:
            if kw in text_lower:
                return 'medium'
        for kw in long_keywords:
            if kw in text_lower:
                return 'long'
        return 'short'
    
    def _estimate_complexity(self, text: str) -> float:
        complexity = 0.0
        keywords = {
            '复杂': 0.3, '困难': 0.3, '挑战': 0.2,
            '系统': 0.3, '架构': 0.3, '设计': 0.2,
            '集成': 0.2, '优化': 0.2, '重构': 0.3,
            '研究': 0.2, '分析': 0.2, '评估': 0.1,
        }
        for keyword, score in keywords.items():
            if keyword.lower() in text.lower():
                complexity += score
        if len(text) > 100:
            complexity += 0.2
        return round(min(complexity, 1.0) * 10, 1)
    
    def add_goal(self, declared_text: str, declared_at: Optional[datetime] = None, 
                 time_horizon: Optional[str] = None) -> Goal:
        existing = self.session.query(Goal).filter(
            Goal.declared_text.like(f'%{declared_text[:30]}%')
        ).filter_by(status='active').first()
        
        if existing:
            existing.last_mentioned = datetime.now()
            self.session.commit()
            return existing
        
        if time_horizon is None:
            time_horizon = self._classify_time_horizon(declared_text)
        
        goal = Goal(
            declared_text=declared_text,
            declared_at=declared_at or datetime.now(),
            status='active',
            drift_score=0.0,
            last_mentioned=datetime.now(),
            complexity_score=self._estimate_complexity(declared_text),
            time_horizon=time_horizon,
            completion_score=0.0
        )
        self.session.add(goal)
        self.session.commit()
        return goal
    
    def calculate_goal_completion(self) -> float:
        short_goals = self.session.query(Goal).filter_by(status='active', time_horizon='short').all()
        medium_goals = self.session.query(Goal).filter_by(status='active', time_horizon='medium').all()
        long_goals = self.session.query(Goal).filter_by(status='active', time_horizon='long').all()
        
        def get_avg_completion(goals):
            if not goals:
                return 0.5
            return sum(g.completion_score or 0.0 for g in goals) / len(goals)
        
        short_score = get_avg_completion(short_goals)
        medium_score = get_avg_completion(medium_goals)
        long_score = get_avg_completion(long_goals)
        
        completion = short_score * 0.3 + medium_score * 0.3 + long_score * 0.4
        return round(completion, 2)
    
    def update_completion_score(self, goal_id: int, completion: float):
        goal = self.session.query(Goal).filter_by(id=goal_id).first()
        if goal:
            goal.completion_score = min(1.0, max(0.0, completion))
            self.session.commit()
    
    def get_active_goals(self, time_horizon: Optional[str] = None) -> List[Goal]:
        query = self.session.query(Goal).filter_by(status='active')
        if time_horizon:
            query = query.filter_by(time_horizon=time_horizon)
        return query.all()
    
    def get_goals_by_horizon(self) -> Dict[str, List[Goal]]:
        return {
            'short': self.get_active_goals('short'),
            'medium': self.get_active_goals('medium'),
            'long': self.get_active_goals('long')
        }
    
    def load_goals_from_memory(self, memory_path: str) -> List[Dict]:
        goals = []
        try:
            with open(memory_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            flow_goals_pattern = r'## Flow-Goals\n(.*?)(?=\n## |\Z)'
            match = re.search(flow_goals_pattern, content, re.DOTALL)
            
            if match:
                goals_text = match.group(1)
                lines = goals_text.strip().split('\n')
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('- '):
                        line = line[2:].strip()
                        status_match = re.match(r'\[(.*?)\]\s*(.+?)(?:\s*\((.*?)\))?$', line)
                        if status_match:
                            status = status_match.group(1)
                            goal_text = status_match.group(2).strip()
                            meta = status_match.group(3)
                            
                            time_horizon = 'short'
                            drift_score = 0.0
                            
                            if meta:
                                if '短期' in meta:
                                    time_horizon = 'short'
                                elif '中期' in meta:
                                    time_horizon = 'medium'
                                elif '长期' in meta:
                                    time_horizon = 'long'
                                
                                drift_match = re.search(r'漂移度(\d+\.?\d*)', meta)
                                if drift_match:
                                    drift_score = float(drift_match.group(1))
                            
                            goals.append({
                                'declared_text': goal_text,
                                'declared_at': datetime.now(),
                                'status': 'active' if status in ['推进中', '稳步推进'] else 'blocked',
                                'drift_score': drift_score,
                                'complexity_score': self._estimate_complexity(goal_text),
                                'time_horizon': time_horizon,
                                'completion_score': 0.0
                            })
        except Exception as e:
            print(f"读取memory.md失败: {e}")
        
        return goals
    
    def close(self):
        self.session.close()

def test_full_goal_system():
    print("=" * 70)
    print("🎯 完整目标管理系统测试")
    print("=" * 70)
    
    gm = GoalManager('flow_ecosystem.db')
    
    print("\n1️⃣ 测试时间跨度分类")
    test_texts = [
        "今天完成API文档",
        "本周完成项目设计",
        "长期目标是成为架构师",
        "我要学习Python编程",
    ]
    
    for text in test_texts:
        horizon = gm._classify_time_horizon(text)
        horizon_label = {'short': '短期', 'medium': '中期', 'long': '长期'}[horizon]
        print(f"  '{text}' → {horizon_label}")
    
    print("\n\n2️⃣ 测试添加不同时间跨度的目标")
    goals = [
        ("完成今日任务", 'short'),
        ("本周完成系统设计", 'medium'),
        ("长期目标：成为技术专家", 'long'),
    ]
    
    for text, horizon in goals:
        goal = gm.add_goal(text, datetime.now(), horizon)
        horizon_label = {'short': '短期', 'medium': '中期', 'long': '长期'}[goal.time_horizon]
        print(f"  添加成功：[{horizon_label}] {goal.declared_text} (ID:{goal.id})")
    
    print("\n\n3️⃣ 测试按时间跨度分组获取目标")
    goals_by_horizon = gm.get_goals_by_horizon()
    
    for horizon, goals_list in goals_by_horizon.items():
        horizon_label = {'short': '短期', 'medium': '中期', 'long': '长期'}[horizon]
        print(f"  {horizon_label}目标: {len(goals_list)}个")
        for g in goals_list[:3]:
            print(f"    - [{g.id}] {g.declared_text[:30]}...")
    
    print("\n\n4️⃣ 测试目标完成度计算")
    if goals_by_horizon['short']:
        gm.update_completion_score(goals_by_horizon['short'][0].id, 0.8)
    if goals_by_horizon['medium']:
        gm.update_completion_score(goals_by_horizon['medium'][0].id, 0.5)
    if goals_by_horizon['long']:
        gm.update_completion_score(goals_by_horizon['long'][0].id, 0.3)
    
    completion = gm.calculate_goal_completion()
    print(f"  综合目标完成度: {completion:.2f}")
    print(f"  计算公式: 短期×0.3 + 中期×0.3 + 长期×0.4")
    
    print("\n\n5️⃣ 测试从memory.md读取目标（模拟）")
    import os
    memory_content = """## Flow-Goals
- [推进中] 完成API文档（短期，漂移度0.2）
- [停滞3天] 微服务拆分方案（中期，漂移度0.6）
- [稳步推进] 成为架构师（长期）

## Flow-Status
一些状态信息..."""
    
    memory_path = '/tmp/test_memory.md'
    with open(memory_path, 'w', encoding='utf-8') as f:
        f.write(memory_content)
    
    loaded_goals = gm.load_goals_from_memory(memory_path)
    print(f"  从memory.md读取到 {len(loaded_goals)} 个目标")
    for g in loaded_goals:
        horizon_label = {'short': '短期', 'medium': '中期', 'long': '长期'}[g['time_horizon']]
        print(f"    - [{horizon_label}] {g['declared_text']} (漂移度:{g['drift_score']})")
    
    os.remove(memory_path)
    
    gm.close()
    print("\n✅ 测试完成！")

if __name__ == '__main__':
    test_full_goal_system()