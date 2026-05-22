#!/usr/bin/env python3
"""从数据库的真实用户消息中提取目标"""

from datetime import datetime
from typing import List, Optional, Tuple, Dict
import re
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Session(Base):
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True)
    role = Column(String(32))
    content_text = Column(Text)
    timestamp = Column(DateTime)

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

def extract_goals_from_text(text: str) -> List[str]:
    """从文本中提取目标"""
    patterns = [
        r'(?:我想|我要|我需要|我打算|目标是|目的是|任务是|计划)(?:\s+)?(.+?)(?:[。！？；\n]|$)',
        r'(?:完成|实现|达成|解决|学习|掌握|开发|创建|更新)(?:\s+)?(.+?)(?:[。！？；\n]|$)',
        r'(?:fix|solve|implement|create|build|develop|learn|master)(?:\s+)?(.+?)(?:[。！？；\n]|\.)',
    ]
    
    goals = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            goal_text = match.group(1).strip()
            if len(goal_text) > 5 and len(goal_text) < 200:
                goals.append(goal_text)
    return goals

def estimate_complexity(text: str) -> float:
    """估算目标复杂度"""
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

def main():
    print("=" * 70)
    print("🎯 从数据库提取真实用户目标")
    print("=" * 70)
    
    # 连接数据库
    engine = create_engine('sqlite:///flow_ecosystem.db')
    SessionDB = sessionmaker(bind=engine)
    session = SessionDB()
    
    # 查询用户消息
    print("\n🔍 查询用户消息...")
    user_messages = session.query(Session).filter(
        Session.role == 'user',
        Session.content_text.isnot(None),
        Session.content_text != ''
    ).order_by(Session.timestamp.desc()).limit(100).all()
    
    print(f"找到 {len(user_messages)} 条用户消息")
    
    # 提取目标
    print("\n📝 提取目标...")
    all_goals = []
    for msg in user_messages:
        goals = extract_goals_from_text(msg.content_text)
        for goal_text in goals:
            all_goals.append({
                'text': goal_text,
                'timestamp': msg.timestamp,
                'complexity': estimate_complexity(goal_text),
                'source_msg_id': msg.id
            })
    
    print(f"共提取到 {len(all_goals)} 个目标")
    
    # 去重并显示
    print("\n📋 去重后的目标列表（按复杂度排序）:")
    unique_goals = {}
    for g in all_goals:
        key = g['text'][:50]
        if key not in unique_goals or g['complexity'] > unique_goals[key]['complexity']:
            unique_goals[key] = g
    
    sorted_goals = sorted(unique_goals.values(), key=lambda x: x['complexity'], reverse=True)
    
    for i, goal in enumerate(sorted_goals[:15], 1):
        print(f"\n{i}. [{goal['complexity']:.1f}] {goal['text']}")
        print(f"   来源: 消息ID {goal['source_msg_id']}")
        print(f"   时间: {goal['timestamp']}")
    
    # 保存到 goals 表
    print("\n💾 保存目标到数据库...")
    saved_count = 0
    for goal in sorted_goals:
        # 检查是否已存在
        existing = session.query(Goal).filter(
            Goal.declared_text.like(f'%{goal["text"][:30]}%')
        ).filter_by(status='active').first()
        
        if not existing:
            new_goal = Goal(
                declared_text=goal['text'],
                declared_at=goal['timestamp'],
                status='active',
                drift_score=0.0,
                last_mentioned=datetime.now(),
                complexity_score=goal['complexity']
            )
            session.add(new_goal)
            saved_count += 1
    
    session.commit()
    print(f"成功保存 {saved_count} 个新目标")
    
    # 统计
    total_goals = session.query(Goal).filter_by(status='active').count()
    print(f"\n📊 当前数据库中共有 {total_goals} 个活跃目标")
    
    session.close()
    print("\n✅ 完成！")

if __name__ == '__main__':
    main()