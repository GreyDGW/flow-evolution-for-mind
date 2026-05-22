#!/usr/bin/env python3
"""测试 GoalManager 的主要功能 - 简化版本"""

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

class GoalManager:
    def __init__(self, db_path: str = 'flow_ecosystem.db'):
        self.engine = create_engine(f'sqlite:///{db_path}')
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def extract_goals_from_text(self, text: str, timestamp: datetime) -> List[Dict]:
        patterns = [
            r'(?:我想|我要|我需要|我打算|目标是|目的是|任务是|计划)(?:\s+)?(.+?)(?:[。！？；\n]|$)',
            r'(?:完成|实现|达成|解决|学习|掌握|开发|创建)(?:\s+)?(.+?)(?:[。！？；\n]|$)',
            r'(?:fix|solve|implement|create|build|develop|learn|master)(?:\s+)?(.+?)(?:[。！？；\n]|\.)',
        ]
        
        goals = []
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                goal_text = match.group(1).strip()
                if len(goal_text) > 5 and len(goal_text) < 200:
                    goals.append({
                        'declared_text': goal_text,
                        'declared_at': timestamp,
                        'status': 'active',
                        'drift_score': 0.0,
                        'complexity_score': self._estimate_complexity(goal_text)
                    })
        return goals
    
    def _estimate_complexity(self, text: str) -> float:
        complexity = 0.0
        keywords = {
            '复杂': 0.3, '困难': 0.3, '挑战': 0.2,
            '系统': 0.3, '架构': 0.3, '设计': 0.2,
            '集成': 0.2, '优化': 0.2, '重构': 0.3,
            '研究': 0.2, '分析': 0.2, '评估': 0.1,
            'multiple': 0.3, 'complex': 0.3, 'system': 0.3,
            'architecture': 0.3, 'design': 0.2, 'integration': 0.2
        }
        
        for keyword, score in keywords.items():
            if keyword.lower() in text.lower():
                complexity += score
        
        if len(text) > 100:
            complexity += 0.2
        
        return min(complexity, 1.0) * 10
    
    def add_goal(self, declared_text: str, declared_at: Optional[datetime] = None) -> Goal:
        existing = self.session.query(Goal).filter(
            Goal.declared_text.like(f'%{declared_text[:30]}%')
        ).filter_by(status='active').first()
        
        if existing:
            existing.last_mentioned = datetime.now()
            self.session.commit()
            return existing
        
        goal = Goal(
            declared_text=declared_text,
            declared_at=declared_at or datetime.now(),
            status='active',
            drift_score=0.0,
            last_mentioned=datetime.now(),
            complexity_score=self._estimate_complexity(declared_text)
        )
        
        self.session.add(goal)
        self.session.commit()
        return goal
    
    def get_active_goals(self) -> List[Goal]:
        return self.session.query(Goal).filter_by(status='active').all()
    
    def calculate_drift_score(self, goal_id: int, recent_messages: List[Tuple[datetime, str]]) -> float:
        goal = self.session.query(Goal).filter_by(id=goal_id).first()
        if not goal:
            return 0.0
        
        if not recent_messages:
            return goal.drift_score or 0.0
        
        goal_text = goal.declared_text.lower()
        relevance_score = 0.0
        
        for timestamp, message_text in recent_messages:
            if goal_text in message_text.lower():
                relevance_score += 1.0
            else:
                for word in goal_text.split()[:5]:
                    if word in message_text.lower():
                        relevance_score += 0.2
        
        total_messages = len(recent_messages)
        if total_messages == 0:
            return 0.0
        
        avg_relevance = relevance_score / total_messages
        time_diff = (datetime.now() - goal.last_mentioned).total_seconds() / 3600
        
        drift_score = max(0, min(10, (1 - avg_relevance) * 5 + min(time_diff / 24, 5)))
        
        goal.drift_score = drift_score
        self.session.commit()
        
        return drift_score
    
    def close(self):
        self.session.close()

def test_goal_manager():
    print("=" * 60)
    print("🎯 GoalManager 功能测试")
    print("=" * 60)
    
    gm = GoalManager('flow_ecosystem.db')
    
    print("\n1️⃣ 测试目标提取")
    test_texts = [
        "我想创建一个个人进化系统",
        "目标是完成 flow ecosystem 项目",
        "我需要学习 Python 编程",
        "帮我实现用户登录功能",
    ]
    
    for text in test_texts:
        goals = gm.extract_goals_from_text(text, datetime.now())
        if goals:
            print(f"\n输入: {text}")
            print(f"提取到的目标: {goals[0]['declared_text']}")
            print(f"复杂度评分: {goals[0]['complexity_score']:.2f}")
    
    print("\n\n2️⃣ 测试添加目标")
    goal = gm.add_goal("完成 flow ecosystem PRD 文档", datetime.now())
    print(f"添加目标成功！ID: {goal.id}, 目标: {goal.declared_text}")
    
    print("\n\n3️⃣ 测试获取活跃目标")
    active_goals = gm.get_active_goals()
    print(f"当前活跃目标数量: {len(active_goals)}")
    for g in active_goals[:3]:
        print(f"  - [{g.id}] {g.declared_text[:30]}... (漂移度: {g.drift_score:.2f})")
    
    if active_goals:
        print("\n\n4️⃣ 测试漂移分数计算")
        goal_id = active_goals[0].id
        recent_messages = [
            (datetime.now(), "我正在写 PRD 文档"),
            (datetime.now(), "flow ecosystem 的架构设计"),
            (datetime.now(), "吃午饭"),
        ]
        drift = gm.calculate_drift_score(goal_id, recent_messages)
        print(f"目标 [{goal_id}] 的漂移分数: {drift:.2f}")
    
    gm.close()
    print("\n✅ 测试完成！")

if __name__ == '__main__':
    test_goal_manager()